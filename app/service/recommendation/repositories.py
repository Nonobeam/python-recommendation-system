import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.db import get_db
from app.config.redis import cache
from app.exception.cache_exceptions import RedisOperationError
from app.utils.logger import api_logger


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
                api_logger.debug(f"Cache hit for {self.key_prefix} entity: {entity_id}")
                return cached_data
            else:
                api_logger.debug(f"Cache miss for {self.key_prefix} entity: {entity_id}")
                return None
        except RedisOperationError as e:
            api_logger.error(f"Redis operation error for {entity_id}: {str(e)}")
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
            query = text(
                f"""
                SELECT meta_data, created_at
                FROM platform_service.{self.table_name}
                WHERE {'brand_id' if 'brand' in self.table_name else 'mall_id'} = :entity_id
                LIMIT 1
            """
            )

            result = db.execute(query, {"entity_id": entity_id}).fetchone()

            if result:
                meta_data = result.meta_data
                if isinstance(meta_data, str):
                    meta_data = json.loads(meta_data)

                return {"meta_data": meta_data, "created_at": str(result.created_at)}
            return None
        except Exception as e:
            api_logger.error(f"Database query error for {entity_id}: {str(e)}")
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
            return cached_data

        self.cache_misses += 1
        db_data = self.postgres_repo.get_by_id(entity_id)

        if db_data:
            api_logger.info(f"Retrieved and cached {entity_id} from database")
            return db_data

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
