import json
import os
from pathlib import Path
from typing import Any, Optional

import redis
from dotenv import load_dotenv

from app.exception import RedisConnectionError, RedisOperationError
from app.utils.logger import redis_logger

root_path = Path(__file__).parent.parent.parent
env_path = root_path / ".env"
load_dotenv(dotenv_path=env_path)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DECODE_RESPONSES = True

redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=REDIS_DECODE_RESPONSES,
    max_connections=20,
)

redis_logger.info(f"Connecting to Redis at redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

redis_client = redis.Redis(connection_pool=redis_pool)


class RedisCache:
    """Redis cache utility class"""

    def __init__(self, client: redis.Redis = redis_client):
        self.client = client

    def get(self, key: str) -> Optional[Any]:
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except redis.RedisError as e:
            raise RedisOperationError("get", key, str(e))
        except json.JSONDecodeError as e:
            raise RedisOperationError("get", key, f"JSON decode error: {str(e)}")

    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        try:
            json_value = json.dumps(value, default=str)
            return self.client.setex(key, expire, json_value)
        except redis.RedisError as e:
            raise RedisOperationError("set", key, str(e))
        except json.JSONEncodeError as e:
            raise RedisOperationError("set", key, f"JSON encode error: {str(e)}")

    def delete(self, key: str) -> bool:
        try:
            return self.client.delete(key) > 0
        except redis.RedisError as e:
            raise RedisOperationError("delete", key, str(e))

    def exists(self, key: str) -> bool:
        try:
            return self.client.exists(key) > 0
        except redis.RedisError as e:
            raise RedisOperationError("exists", key, str(e))

    def flush_all(self) -> bool:
        try:
            return self.client.flushdb()
        except redis.RedisError as e:
            raise RedisOperationError("flush_all", message=str(e))


def startup_redis_check() -> bool:
    try:
        redis_client.ping()
        redis_logger.info("Redis connection successful")
        return True
    except redis.RedisError as e:
        redis_logger.error(f"Redis connection failed: {str(e)}")
        raise RedisConnectionError(f"Redis connection failed: {str(e)}")


cache = RedisCache()

if __name__ == "__main__":
    startup_redis_check()
