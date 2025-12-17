from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.db import get_db
from app.config.redis import cache
from app.exception.cache_exceptions import RedisOperationError
from app.utils.logger import api_logger, log_access_message


class BoothRepository:
    def __init__(self):
        pass

    def get_brand_category_id(self, brand_id: str) -> Optional[str]:
        db: Session = next(get_db())
        try:
            query = text(
                """
                SELECT categories_id
                FROM brand
                WHERE brand_id = :brand_id
                LIMIT 1
                """
            )
            result = db.execute(query, {"brand_id": brand_id}).fetchone()
            if result:
                return result.categories_id
            return None
        except Exception as e:
            log_access_message(
                logger=api_logger,
                log_level="error",
                event_type="db_error",
                entity_type="brand",
                entity_id=brand_id,
                message=str(e),
                exc_info=True,
            )
            return None
        finally:
            db.close()

    def get_available_booths_with_category_and_price(
        self,
        mall_ids: List[str],
        min_size: Optional[float] = None,
        max_size: Optional[float] = None,
        preferred_floors: Optional[List[int]] = None,
        size_tolerance: float = 0.2,
    ) -> List[Dict[str, Any]]:
        db: Session = next(get_db())
        try:
            placeholders = ",".join([f":mall_id_{i}" for i in range(len(mall_ids))])
            query_parts = [
                f"""
                SELECT
                    b.booth_id,
                    b.name as booth_name,
                    b.mall_id,
                    b.size_m2,
                    b.zone_id,
                    b.floor_id,
                    current_price.rent_price,
                    COALESCE(current_price.is_current, false) as price_is_current,
                    m.name as mall_name,
                    m.logo as mall_logo,
                    m.address as mall_address,
                    f.level as floor_level,
                    z.categories_id as zone_categories_id,
                    bi.frontage_width_m as frontage_width_m,
                    asset.file_url as booth_image
                FROM booth b
                LEFT JOIN LATERAL (
                    SELECT brp.rent_price, brp.is_current
                    FROM booth_rental_price brp
                    WHERE brp.booth_id = b.booth_id
                    ORDER BY brp.is_current DESC NULLS LAST, brp.effective_from DESC NULLS LAST
                    LIMIT 1
                ) current_price ON TRUE
                LEFT JOIN zone z ON b.zone_id = z.zone_id
                LEFT JOIN floor f ON b.floor_id = f.floor_id
                LEFT JOIN booth_information bi ON b.booth_id = bi.booth_id
                LEFT JOIN mall m ON b.mall_id = m.mall_id
                LEFT JOIN LATERAL (
                    SELECT bva.file_url
                    FROM booth_visual_assets bva
                    WHERE bva.booth_id = b.booth_id
                    ORDER BY bva.display_order ASC NULLS LAST
                    LIMIT 1
                ) asset ON TRUE
                WHERE b.is_available = true
                    AND b.mall_id IN ({placeholders})
                    AND m.status = 'ACTIVE'
            """
            ]

            params: Dict[str, Any] = {f"mall_id_{i}": mall_id for i, mall_id in enumerate(mall_ids)}

            if min_size is not None:
                min_size_decimal = Decimal(str(min_size))
                tolerance_decimal = Decimal(str(size_tolerance))
                min_size_with_tolerance = min_size_decimal * (Decimal("1") - tolerance_decimal)
                query_parts.append("AND b.size_m2 >= :min_size")
                params["min_size"] = float(min_size_with_tolerance)

            if max_size is not None:
                max_size_decimal = Decimal(str(max_size))
                tolerance_decimal = Decimal(str(size_tolerance))
                max_size_with_tolerance = max_size_decimal * (Decimal("1") + tolerance_decimal)
                query_parts.append("AND b.size_m2 <= :max_size")
                params["max_size"] = float(max_size_with_tolerance)

            if preferred_floors is not None and len(preferred_floors) > 0:
                floor_placeholders = ",".join([f":floor_{i}" for i in range(len(preferred_floors))])
                query_parts.append(f"AND f.level IN ({floor_placeholders})")
                for i, floor in enumerate(preferred_floors):
                    params[f"floor_{i}"] = floor

            query = text(" ".join(query_parts))

            log_access_message(
                logger=api_logger,
                log_level="info",
                event_type="db_query",
                entity_type="booth",
                message=f"Querying booths with category and price for {len(mall_ids)} malls",
            )

            results = db.execute(query, params).fetchall()

            booths = []
            for row in results:
                booth = {
                    "booth_id": row.booth_id,
                    "booth_name": row.booth_name,
                    "mall_id": row.mall_id,
                    "size_m2": float(row.size_m2) if row.size_m2 else None,
                    "zone_id": row.zone_id,
                    "floor_id": row.floor_id,
                    "rent_price": float(row.rent_price) if row.rent_price else None,
                    "price_is_current": row.price_is_current if row.price_is_current else False,
                    "mall_name": row.mall_name,
                    "mall_logo": row.mall_logo,
                    "mall_address": row.mall_address,
                    "floor_level": row.floor_level,
                    "zone_categories_id": row.zone_categories_id,
                    "frontage_width_m": float(row.frontage_width_m) if row.frontage_width_m else None,
                    "booth_image": row.booth_image,
                }
                booths.append(booth)

            log_access_message(
                logger=api_logger,
                log_level="info",
                event_type="db_found",
                entity_type="booth",
                message=f"Found {len(booths)} booths with category and price data",
            )

            return booths

        except Exception as e:
            log_access_message(
                logger=api_logger,
                log_level="error",
                event_type="db_error",
                entity_type="booth",
                message=str(e),
                exc_info=True,
            )
            return []
        finally:
            db.close()

    def get_available_booths_by_mall_ids(
        self,
        mall_ids: List[str],
        min_size: Optional[float] = None,
        max_size: Optional[float] = None,
        max_price: Optional[float] = None,
        category_id: Optional[str] = None,
        preferred_floors: Optional[List[int]] = None,
        size_tolerance: float = 0.2,
    ) -> List[Dict[str, Any]]:
        db: Session = next(get_db())
        try:
            placeholders = ",".join([f":mall_id_{i}" for i in range(len(mall_ids))])
            query_parts = [
                f"""
                SELECT
                    b.booth_id,
                    b.name as booth_name,
                    b.mall_id,
                    b.size_m2,
                    brp.rent_price,
                    m.name as mall_name,
                    m.logo as mall_logo,
                    m.address as mall_address,
                    f.level as floor_level,
                    bi.frontage_width_m as frontage_width_m,
                    asset.file_url as booth_image
                FROM booth b
                LEFT JOIN booth_rental_price brp
                    ON b.booth_id = brp.booth_id AND brp.is_current = true
                LEFT JOIN zone z ON b.zone_id = z.zone_id
                LEFT JOIN floor f ON b.floor_id = f.floor_id
                LEFT JOIN booth_information bi ON b.booth_id = bi.booth_id
                LEFT JOIN mall m ON b.mall_id = m.mall_id
                LEFT JOIN LATERAL (
                    SELECT bva.file_url
                    FROM booth_visual_assets bva
                    WHERE bva.booth_id = b.booth_id
                    ORDER BY bva.display_order ASC NULLS LAST
                    LIMIT 1
                ) asset ON TRUE
                WHERE b.is_available = true
                    AND b.mall_id IN ({placeholders})
                    AND m.status = 'ACTIVE'
            """
            ]

            params: Dict[str, Any] = {f"mall_id_{i}": mall_id for i, mall_id in enumerate(mall_ids)}

            if min_size is not None:
                min_size_decimal = Decimal(str(min_size))
                min_size_with_tolerance = min_size_decimal * (1 - size_tolerance)
                query_parts.append("AND b.size_m2 >= :min_size")
                params["min_size"] = float(min_size_with_tolerance)

            if max_size is not None:
                max_size_decimal = Decimal(str(max_size))
                max_size_with_tolerance = max_size_decimal * (1 + size_tolerance)
                query_parts.append("AND b.size_m2 <= :max_size")
                params["max_size"] = float(max_size_with_tolerance)

            if max_price is not None:
                query_parts.append("AND (brp.rent_price IS NULL OR brp.rent_price <= :max_price)")
                params["max_price"] = float(max_price)

            if category_id is not None:
                query_parts.append("AND z.categories_id = :category_id")
                params["category_id"] = category_id

            if preferred_floors is not None and len(preferred_floors) > 0:
                floor_placeholders = ",".join([f":floor_{i}" for i in range(len(preferred_floors))])
                query_parts.append(f"AND f.level IN ({floor_placeholders})")
                for i, floor in enumerate(preferred_floors):
                    params[f"floor_{i}"] = floor

            query = text(" ".join(query_parts))

            log_access_message(
                logger=api_logger,
                log_level="info",
                event_type="db_query",
                entity_type="booth",
                message=f"Querying booths for {len(mall_ids)} malls",
            )

            results = db.execute(query, params).fetchall()

            booths = []
            for row in results:
                booth = {
                    "booth_id": row.booth_id,
                    "booth_name": row.booth_name,
                    "mall_id": row.mall_id,
                    "size_m2": float(row.size_m2) if row.size_m2 else None,
                    "rent_price": float(row.rent_price) if row.rent_price else None,
                    "mall_name": row.mall_name,
                    "mall_logo": row.mall_logo,
                    "mall_address": row.mall_address,
                    "floor_level": row.floor_level,
                    "frontage_width_m": float(row.frontage_width_m) if row.frontage_width_m else None,
                    "booth_image": row.booth_image,
                }
                booths.append(booth)

            log_access_message(
                logger=api_logger,
                log_level="info",
                event_type="db_found",
                entity_type="booth",
                message=f"Found {len(booths)} booths",
            )

            return booths

        except Exception as e:
            log_access_message(
                logger=api_logger,
                log_level="error",
                event_type="db_error",
                entity_type="booth",
                message=str(e),
                exc_info=True,
            )
            return []
        finally:
            db.close()

    def get_available_booths_by_mall_id(
        self,
        mall_id: str,
        min_size: Optional[float] = None,
        max_size: Optional[float] = None,
        max_price: Optional[float] = None,
        category_id: Optional[str] = None,
        preferred_floors: Optional[List[int]] = None,
        size_tolerance: float = 0.2,
    ) -> List[Dict[str, Any]]:
        return self.get_available_booths_by_mall_ids(
            mall_ids=[mall_id],
            min_size=min_size,
            max_size=max_size,
            max_price=max_price,
            category_id=category_id,
            preferred_floors=preferred_floors,
            size_tolerance=size_tolerance,
        )

    def get_booth_with_details(self, booth_id: str) -> Optional[Dict[str, Any]]:
        cache_key = f"booth:details:{booth_id}"
        try:
            cached_data = cache.get(cache_key)
            if cached_data:
                log_access_message(
                    logger=api_logger,
                    log_level="debug",
                    event_type="cache_hit",
                    entity_type="booth",
                    entity_id=booth_id,
                )
                return cached_data
        except RedisOperationError:
            pass

        db: Session = next(get_db())
        try:
            query = text(
                """
                SELECT
                    b.booth_id,
                    b.name,
                    b.floor_position_reference,
                    b.mall_id,
                    b.zone_id,
                    b.size_m2,
                    b.floor_id,
                    b.is_available,
                    b.verify_status,
                    b.requirement,
                    b.status,
                    brp.rent_price,
                    brp.is_current as price_is_current,
                    brp.effective_from,
                    brp.effective_to,
                    bi.zone_description,
                    bi.shape,
                    bi.ceiling_height_m,
                    bi.frontage_width_m,
                    bi.has_windows,
                    bi.has_column_obstacles,
                    bi.has_electricity,
                    bi.electricity_capacity_kw,
                    bi.has_water_supply,
                    bi.has_gas_line,
                    bi.has_drainage,
                    bi.has_ventilation,
                    bi.has_grease_trap,
                    bi.has_internet,
                    bi.has_storage_area,
                    bi.storage_area_m2,
                    bi.description,
                    z.categories_id,
                    f.level as floor_level,
                    m.name as mall_name
                FROM booth b
                LEFT JOIN booth_rental_price brp
                    ON b.booth_id = brp.booth_id AND brp.is_current = true
                LEFT JOIN booth_information bi
                    ON b.booth_id = bi.booth_id
                LEFT JOIN zone z ON b.zone_id = z.zone_id
                LEFT JOIN floor f ON b.floor_id = f.floor_id
                LEFT JOIN mall m ON b.mall_id = m.mall_id
                WHERE b.booth_id = :booth_id
                LIMIT 1
            """
            )

            log_access_message(
                logger=api_logger,
                log_level="info",
                event_type="db_query",
                entity_type="booth",
                entity_id=booth_id,
            )

            result = db.execute(query, {"booth_id": booth_id}).fetchone()

            if result:
                booth = {
                    "booth_id": result.booth_id,
                    "name": result.name,
                    "floor_position_reference": result.floor_position_reference,
                    "mall_id": result.mall_id,
                    "zone_id": result.zone_id,
                    "size_m2": float(result.size_m2) if result.size_m2 else None,
                    "floor_id": result.floor_id,
                    "is_available": result.is_available,
                    "verify_status": result.verify_status,
                    "requirement": result.requirement,
                    "status": result.status,
                    "rent_price": float(result.rent_price) if result.rent_price else None,
                    "price_is_current": result.price_is_current,
                    "effective_from": str(result.effective_from) if result.effective_from else None,
                    "effective_to": str(result.effective_to) if result.effective_to else None,
                    "zone_description": result.zone_description,
                    "shape": result.shape,
                    "ceiling_height_m": float(result.ceiling_height_m) if result.ceiling_height_m else None,
                    "frontage_width_m": float(result.frontage_width_m) if result.frontage_width_m else None,
                    "has_windows": result.has_windows,
                    "has_column_obstacles": result.has_column_obstacles,
                    "has_electricity": result.has_electricity,
                    "electricity_capacity_kw": (
                        float(result.electricity_capacity_kw) if result.electricity_capacity_kw else None
                    ),
                    "has_water_supply": result.has_water_supply,
                    "has_gas_line": result.has_gas_line,
                    "has_drainage": result.has_drainage,
                    "has_ventilation": result.has_ventilation,
                    "has_grease_trap": result.has_grease_trap,
                    "has_internet": result.has_internet,
                    "has_storage_area": result.has_storage_area,
                    "storage_area_m2": float(result.storage_area_m2) if result.storage_area_m2 else None,
                    "description": result.description,
                    "categories_id": result.categories_id,
                    "floor_level": result.floor_level,
                    "mall_name": result.mall_name,
                }

                log_access_message(
                    logger=api_logger,
                    log_level="info",
                    event_type="db_found",
                    entity_type="booth",
                    entity_id=booth_id,
                )

                try:
                    cache.set(cache_key, booth, expire=1800)
                except RedisOperationError:
                    pass

                return booth

            log_access_message(
                logger=api_logger,
                log_level="warning",
                event_type="db_not_found",
                entity_type="booth",
                entity_id=booth_id,
            )
            return None

        except Exception as e:
            log_access_message(
                logger=api_logger,
                log_level="error",
                event_type="db_error",
                entity_type="booth",
                entity_id=booth_id,
                message=str(e),
                exc_info=True,
            )
            return None
        finally:
            db.close()


BoothRepositoryInstance = BoothRepository()
