from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.db import get_db
from app.utils.logger import api_logger, log_access_message


class BrandRepository:
    def __init__(self):
        pass

    def get_all_active_brand_ids(self) -> List[str]:
        db: Session = next(get_db())
        try:
            query = text("SELECT brand_id FROM brand WHERE status = 'ACTIVE'")
            results = db.execute(query).fetchall()
            return [row.brand_id for row in results]
        except Exception as e:
            api_logger.error(f"Error fetching brand IDs: {str(e)}")
            return []
        finally:
            db.close()

    def get_active_brand_ids_limited(self, limit: int) -> List[str]:
        """Get only `limit` active brand IDs from the database."""
        db: Session = next(get_db())
        try:
            query = text("SELECT brand_id FROM brand WHERE status = 'ACTIVE' LIMIT :limit")
            results = db.execute(query, {"limit": limit}).fetchall()
            return [row.brand_id for row in results]
        except Exception as e:
            api_logger.error(f"Error fetching limited brand IDs: {str(e)}")
            return []
        finally:
            db.close()

    def get_simple_brand_info_limited(self, limit: int, exclude_for_mall_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Get brand_id, name, logo, phone_number, mail, short_description, and category_name
        for `limit` active brands in ONE query.
        Returns dict keyed by brand_id for easy lookup.

        Args:
            limit: Maximum number of brands to return
            exclude_for_mall_id: Required. Excludes brands that have:
                - Active rental request for a booth in this mall
                - Active rental information for a booth in this mall

        Raises:
            ValueError: If exclude_for_mall_id is not provided
        """
        if not exclude_for_mall_id:
            raise ValueError("exclude_for_mall_id is required")

        db: Session = next(get_db())
        try:
            query = text(
                """
                SELECT b.brand_id, b.name AS brand_name, b.logo AS brand_logo,
                       b.phone_number, b.mail, b.short_description,
                       c.name AS category_name
                FROM brand b
                LEFT JOIN categories c ON b.categories_id = c.categories_id
                WHERE b.status = 'ACTIVE'
                AND NOT EXISTS (
                    SELECT 1
                    FROM booth_rental_request brr
                    JOIN booth booth
                        ON brr.booth_id = booth.booth_id
                    WHERE brr.brand_id = b.brand_id
                        AND booth.mall_id = :mall_id
                        AND brr.status = 'ACTIVE'
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM rental_information ri
                    JOIN booth booth
                        ON ri.booth_id = booth.booth_id
                    WHERE ri.brand_id = b.brand_id
                        AND booth.mall_id = :mall_id
                        AND ri.status = 'ACTIVE'
                )
                LIMIT :limit;
                """
            )
            results = db.execute(query, {"limit": limit, "mall_id": exclude_for_mall_id}).fetchall()

            brands = {}
            for row in results:
                brands[row.brand_id] = {
                    "brand_id": row.brand_id,
                    "brand_name": row.brand_name,
                    "brand_logo": row.brand_logo,
                    "phone_number": row.phone_number,
                    "mail": row.mail,
                    "short_description": row.short_description,
                    "category_name": row.category_name,
                }
            return brands
        except Exception as e:
            api_logger.error(f"Error fetching simple brand info: {str(e)}")
            return {}
        finally:
            db.close()

    def get_brands_by_ids(self, brand_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        db: Session = next(get_db())
        try:
            if not brand_ids:
                return {}

            placeholders = ",".join([f":brand_id_{i}" for i in range(len(brand_ids))])
            query = text(
                f"""
        SELECT
          b.brand_id,
          b.name as brand_name,
          b.logo as brand_logo
        FROM brand b
        WHERE b.brand_id IN ({placeholders})
          AND b.status = 'ACTIVE'
      """
            )

            params = {f"brand_id_{i}": brand_id for i, brand_id in enumerate(brand_ids)}

            log_access_message(
                logger=api_logger,
                log_level="info",
                event_type="db_query",
                entity_type="brand",
                message=f"Querying {len(brand_ids)} brands",
            )

            results = db.execute(query, params).fetchall()

            brands = {}
            for row in results:
                brands[row.brand_id] = {
                    "brand_id": row.brand_id,
                    "brand_name": row.brand_name,
                    "brand_logo": row.brand_logo,
                }

            log_access_message(
                logger=api_logger,
                log_level="info",
                event_type="db_found",
                entity_type="brand",
                message=f"Found {len(brands)} brands",
            )

            return brands
        except Exception as e:
            api_logger.error(f"Error fetching brands: {str(e)}")
            return {}
        finally:
            db.close()


BrandRepositoryInstance = BrandRepository()
