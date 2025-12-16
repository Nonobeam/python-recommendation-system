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
            query = text("SELECT brand_id FROM platform_service.brand WHERE status = 'ACTIVE'")
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
            query = text("SELECT brand_id FROM platform_service.brand WHERE status = 'ACTIVE' LIMIT :limit")
            results = db.execute(query, {"limit": limit}).fetchall()
            return [row.brand_id for row in results]
        except Exception as e:
            api_logger.error(f"Error fetching limited brand IDs: {str(e)}")
            return []
        finally:
            db.close()

    def get_simple_brand_info_limited(self, limit: int) -> Dict[str, Dict[str, Any]]:
        """
        Get brand_id, name, and logo for `limit` active brands in ONE query.
        Returns dict keyed by brand_id for easy lookup.
        """
        db: Session = next(get_db())
        try:
            query = text(
                """
                SELECT brand_id, name as brand_name, logo as brand_logo
                FROM platform_service.brand
                WHERE status = 'ACTIVE'
                LIMIT :limit
            """
            )
            results = db.execute(query, {"limit": limit}).fetchall()

            brands = {}
            for row in results:
                brands[row.brand_id] = {
                    "brand_id": row.brand_id,
                    "brand_name": row.brand_name,
                    "brand_logo": row.brand_logo,
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
        FROM platform_service.brand b
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
