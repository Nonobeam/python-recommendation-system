from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.db import get_db
from app.utils.logger import api_logger, log_access_message


class MallRepository:
    def __init__(self):
        pass

    def get_malls_by_ids(self, mall_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        db: Session = next(get_db())
        try:
            if not mall_ids:
                return {}

            placeholders = ",".join([f":mall_id_{i}" for i in range(len(mall_ids))])
            query = text(
                f"""
        SELECT
          m.mall_id,
          m.name as mall_name,
          m.logo as mall_logo,
          m.address as mall_address
        FROM platform_service.mall m
        WHERE m.mall_id IN ({placeholders})
          AND m.status = 'ACTIVE'
      """
            )

            params = {f"mall_id_{i}": mall_id for i, mall_id in enumerate(mall_ids)}

            log_access_message(
                logger=api_logger,
                log_level="info",
                event_type="db_query",
                entity_type="mall",
                message=f"Querying {len(mall_ids)} malls",
            )

            results = db.execute(query, params).fetchall()

            malls = {}
            for row in results:
                malls[row.mall_id] = {
                    "mall_id": row.mall_id,
                    "mall_name": row.mall_name,
                    "mall_logo": row.mall_logo,
                    "mall_address": row.mall_address,
                }

            log_access_message(
                logger=api_logger,
                log_level="info",
                event_type="db_found",
                entity_type="mall",
                message=f"Found {len(malls)} malls",
            )

            return malls
        except Exception as e:
            api_logger.error(f"Error fetching malls: {str(e)}")
            return {}
        finally:
            db.close()

    def get_all_active_mall_ids(self) -> List[str]:
        db: Session = next(get_db())
        try:
            query = text("SELECT mall_id FROM platform_service.mall WHERE status = 'ACTIVE'")
            results = db.execute(query).fetchall()
            return [row.mall_id for row in results]
        except Exception as e:
            api_logger.error(f"Error fetching mall IDs: {str(e)}")
            return []
        finally:
            db.close()

    def has_available_booths(self, mall_id: str) -> bool:
        """
        Check if a mall has any available booths.

        Args:
            mall_id: Mall identifier

        Returns:
            True if the mall has at least one active booth with is_available = true
        """
        db: Session = next(get_db())
        try:
            query = text(
                """
                SELECT EXISTS(
                    SELECT 1 FROM platform_service.booth
                    WHERE mall_id = :mall_id
                    AND status = 'ACTIVE'
                    AND is_available = true
                    LIMIT 1
                ) as has_booths
            """
            )
            result = db.execute(query, {"mall_id": mall_id}).fetchone()
            return result.has_booths if result else False
        except Exception as e:
            api_logger.error(f"Error checking available booths for mall {mall_id}: {str(e)}")
            return False
        finally:
            db.close()

    def get_excluded_brand_ids_for_mall(self, mall_id: str) -> set:
        """
        Get brand IDs that should be excluded from recommendations for a mall.

        Excludes brands that have:
        1. Active rental request (status = 'ACTIVE') for a booth in this mall
        2. Active rental information (status = 'ACTIVE') for a booth in this mall

        Args:
            mall_id: Mall identifier

        Returns:
            Set of brand IDs to exclude from recommendations
        """
        db: Session = next(get_db())
        try:
            # Query brands with active rental requests for booths in this mall
            rental_request_query = text(
                """
                SELECT DISTINCT brr.brand_id
                FROM platform_service.booth_rental_request brr
                JOIN platform_service.booth b ON brr.booth_id = b.booth_id
                WHERE b.mall_id = :mall_id
                AND brr.status = 'ACTIVE'
            """
            )

            # Query brands with active rental information for booths in this mall
            rental_info_query = text(
                """
                SELECT DISTINCT ri.brand_id
                FROM platform_service.rental_information ri
                JOIN platform_service.booth b ON ri.booth_id = b.booth_id
                WHERE b.mall_id = :mall_id
                AND ri.status = 'ACTIVE'
            """
            )

            excluded_brand_ids = set()

            # Execute rental request query
            rental_request_results = db.execute(rental_request_query, {"mall_id": mall_id}).fetchall()
            for row in rental_request_results:
                excluded_brand_ids.add(row.brand_id)

            # Execute rental information query
            rental_info_results = db.execute(rental_info_query, {"mall_id": mall_id}).fetchall()
            for row in rental_info_results:
                excluded_brand_ids.add(row.brand_id)

            if excluded_brand_ids:
                api_logger.info(
                    f"Excluding {len(excluded_brand_ids)} brands from recommendations for mall {mall_id} "
                    f"(active rental requests/information)"
                )

            return excluded_brand_ids
        except Exception as e:
            api_logger.error(f"Error fetching excluded brand IDs for mall {mall_id}: {str(e)}")
            return set()
        finally:
            db.close()


MallRepositoryInstance = MallRepository()
