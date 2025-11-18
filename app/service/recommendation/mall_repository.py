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


MallRepositoryInstance = MallRepository()
