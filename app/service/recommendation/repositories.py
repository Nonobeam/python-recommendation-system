import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.db import get_db
from app.config.redis import cache
from app.exception.cache_exceptions import RedisOperationError
from app.utils.logger import api_logger, log_access_message


class DemographicRepository(ABC):
    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_batch(self, entity_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        pass


class RedisDemographicRepository(DemographicRepository):
    def __init__(self, key_prefix: str):
        self.key_prefix = key_prefix

    def _get_cache_key(self, entity_id: str) -> str:
        return f"{self.key_prefix}:{entity_id}"

    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        try:
            cache_key = self._get_cache_key(entity_id)
            cached_data = cache.get(cache_key)
            if cached_data:
                log_access_message(
                    logger=api_logger,
                    log_level="debug",
                    event_type="cache_hit",
                    entity_type=self.key_prefix,
                    entity_id=entity_id,
                )
                return cached_data
            else:
                log_access_message(
                    logger=api_logger,
                    log_level="debug",
                    event_type="cache_miss",
                    entity_type=self.key_prefix,
                    entity_id=entity_id,
                )
                return None
        except RedisOperationError as e:
            log_access_message(
                logger=api_logger,
                log_level="error",
                event_type="redis_error",
                entity_type=self.key_prefix,
                entity_id=entity_id,
                message=str(e),
            )
            return None

    def get_batch(self, entity_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        results = {}
        for entity_id in entity_ids:
            data = self.get_by_id(entity_id)
            if data:
                results[entity_id] = data
        return results


class PostgresDemographicRepository(DemographicRepository):
    def __init__(self, table_name: str):
        self.table_name = table_name

    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        db: Session = next(get_db())
        try:
            id_column = "brand_id" if "brand" in self.table_name else "mall_id"
            query = text(
                f"""
                SELECT meta_data, created_at
                FROM platform_service.{self.table_name}
                WHERE {id_column} = :entity_id
                LIMIT 1
            """
            )

            log_access_message(
                logger=api_logger,
                log_level="info",
                event_type="db_query",
                entity_type=self.table_name,
                entity_id=entity_id,
            )
            result = db.execute(query, {"entity_id": entity_id}).fetchone()

            if result:
                meta_data = result.meta_data
                if isinstance(meta_data, str):
                    meta_data = json.loads(meta_data)

                log_access_message(
                    logger=api_logger,
                    log_level="info",
                    event_type="db_found",
                    entity_type=self.table_name,
                    entity_id=entity_id,
                )
                return {
                    "meta_data": meta_data,
                    "created_at": str(result.created_at),
                }

            log_access_message(
                logger=api_logger,
                log_level="warning",
                event_type="db_not_found",
                entity_type=self.table_name,
                entity_id=entity_id,
            )
            return None
        except Exception as e:
            log_access_message(
                logger=api_logger,
                log_level="error",
                event_type="db_error",
                entity_type=self.table_name,
                entity_id=entity_id,
                message=str(e),
                exc_info=True,
            )
            return None
        finally:
            db.close()

    def get_batch(self, entity_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        results = {}
        for entity_id in entity_ids:
            data = self.get_by_id(entity_id)
            if data:
                results[entity_id] = data
        return results


class DemographicDataSource:
    def __init__(
        self,
        redis_repo: RedisDemographicRepository,
        postgres_repo: PostgresDemographicRepository,
        cache_ttl: int = 3600,
    ):
        self.redis_repo = redis_repo
        self.postgres_repo = postgres_repo
        self.cache_ttl = cache_ttl
        self.cache_hits = 0
        self.cache_misses = 0

    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        cached_data = self.redis_repo.get_by_id(entity_id)

        if cached_data:
            self.cache_hits += 1
            log_access_message(
                logger=api_logger,
                log_level="debug",
                event_type="cache_hit",
                entity_type="entity",
                entity_id=entity_id,
            )
            return cached_data

        self.cache_misses += 1
        log_access_message(
            logger=api_logger,
            log_level="info",
            event_type="cache_miss",
            entity_type="entity",
            entity_id=entity_id,
            message="Querying database...",
        )
        db_data = self.postgres_repo.get_by_id(entity_id)

        if db_data:
            log_access_message(
                logger=api_logger,
                log_level="info",
                event_type="db_found",
                entity_type="entity",
                entity_id=entity_id,
                message="Retrieved from database",
            )
            return db_data

        log_access_message(
            logger=api_logger,
            log_level="error",
            event_type="not_found",
            entity_type="entity",
            entity_id=entity_id,
            message="No data found in database",
        )
        return None

    def get_batch(self, entity_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        results = {}

        for entity_id in entity_ids:
            data = self.get_by_id(entity_id)
            if data:
                results[entity_id] = data

        return results

    def get_cache_stats(self) -> Dict[str, int]:
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": (
                self.cache_hits / (self.cache_hits + self.cache_misses)
                if (self.cache_hits + self.cache_misses) > 0
                else 0
            ),
        }


BrandDemographicDataSource = DemographicDataSource(
    redis_repo=RedisDemographicRepository("brand:demographics"),
    postgres_repo=PostgresDemographicRepository("brand_demographics"),
)

MallDemographicDataSource = DemographicDataSource(
    redis_repo=RedisDemographicRepository("mall:demographics"),
    postgres_repo=PostgresDemographicRepository("mall_demographics"),
)
