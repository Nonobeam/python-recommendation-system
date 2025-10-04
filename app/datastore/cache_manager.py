from ..config.redis import cache
from ..exception.cache_exceptions import RedisOperationError, CacheError
import os
from dotenv import load_dotenv

load_dotenv()

DEMOGRAPHIC_PREFIX = os.getenv("REDIS_CACHE_DEMOGRAPHIC_KEY_PREFIX", "mall_demographic_")
BUSINESS_PREFIX = os.getenv("REDIS_CACHE_BUSINESS_KEY_PREFIX", "mall_business_")


def cache_mall_demographic(mall_id: str, demographic_data: dict, expire: int = 3600):
    cache_key = f"{DEMOGRAPHIC_PREFIX}{mall_id}"
    success = cache.set(cache_key, demographic_data, expire=expire)
    if not success:
        raise RedisOperationError(f"Failed to cache demographic data for mall {mall_id}")
    return success


def get_cached_mall_demographic(mall_id: str):
    cache_key = f"{DEMOGRAPHIC_PREFIX}{mall_id}"
    cached = cache.get(cache_key)
    if cached:
        print(f"✓ Retrieved cached demographic data for mall {mall_id}")
    else:
        print(f"✗ No cached demographic data for mall {mall_id}")
    return cached


def cache_business_data(business_id: str, business_data: dict, expire: int = 3600):
    cache_key = f"{BUSINESS_PREFIX}{business_id}"
    success = cache.set(cache_key, business_data, expire=expire)
    if not success:
        raise RedisOperationError(f"Failed to cache business data for business {business_id}")
    return success


def get_cached_business_data(business_id: str):
    cache_key = f"{BUSINESS_PREFIX}{business_id}"
    cached = cache.get(cache_key)
    if cached:
        print(f"✓ Retrieved cached business data for business {business_id}")
    else:
        print(f"✗ No cached business data for business {business_id}")
    return cached


def cache_recommendations(recommendations: list, cache_key: str = "recommendations", expire: int = 1800):
    success = cache.set(cache_key, recommendations, expire=expire)
    if not success:
        raise RedisOperationError(f"Failed to cache recommendations with key: {cache_key}")
    return success


def get_cached_recommendations(cache_key: str = "recommendations"):
    cached = cache.get(cache_key)
    if cached:
        print(f"✓ Retrieved cached recommendations with key: {cache_key}")
    return cached


def cache_data(data: list, cache_key: str, expire: int = 3600):
    success = cache.set(cache_key, data, expire=expire)
    if not success:
        raise RedisOperationError(f"Failed to cache data with key: {cache_key}")
    return success


def get_cached_data(cache_key: str):
    cached = cache.get(cache_key)
    if cached:
        print(f"✓ Retrieved cached data with key: {cache_key}")
    else:
        print(f"✗ No cached data found for key: {cache_key}")
    return cached


def clear_data_cache():
    keys_to_clear = ["mall_data", "business_data", "recommendations"]
    cleared_count = 0
    
    for key in keys_to_clear:
        if cache.delete(key):
            cleared_count += 1
            print(f"✓ Cleared cache key: {key}")
    
    demographic_pattern = f"{DEMOGRAPHIC_PREFIX}*"
    business_pattern = f"{BUSINESS_PREFIX}*"
    
    print(f"✓ Cleared {cleared_count} general cache keys")
    print(f"Note: To clear demographic/business caches, use clear_all_demographic_cache() or clear_all_business_cache()")
    return cleared_count


def clear_all_demographic_cache():
    print(f"✓ Clearing all demographic cache entries with pattern: {DEMOGRAPHIC_PREFIX}*")
    

def clear_all_business_cache():
    print(f"✓ Clearing all business cache entries with pattern: {BUSINESS_PREFIX}*")


def clear_specific_mall_demographic(mall_id: str):
    cache_key = f"{DEMOGRAPHIC_PREFIX}{mall_id}"
    success = cache.delete(cache_key)
    if success:
        print(f"✓ Cleared demographic cache for mall {mall_id}")
    else:
        print(f"✗ Failed to clear demographic cache for mall {mall_id}")
    return success


def clear_cache_key(cache_key: str):
    success = cache.delete(cache_key)
    if success:
        print(f"✓ Cleared cache key: {cache_key}")
    else:
        print(f"✗ Failed to clear cache key: {cache_key}")
    return success


def get_cache_status():
    keys_to_check = ["recommendations"]
    status = {}
    
    for key in keys_to_check:
        status[key] = cache.exists(key)
    
    status["demographic_cache_note"] = f"Individual mall demographics cached with pattern: {DEMOGRAPHIC_PREFIX}[mall_id]"
    status["business_cache_note"] = f"Individual business data cached with pattern: {BUSINESS_PREFIX}[business_id]"
    
    return status


def check_cache_key_exists(cache_key: str):
    return cache.exists(cache_key)


def get_all_cache_info():
    status = get_cache_status()
    
    print("=== CACHE STATUS ===")
    for key, exists in status.items():
        status_icon = "✓" if exists else "✗"
        print(f"{status_icon} {key}: {'Cached' if exists else 'Not cached'}")
    
    return status


def invalidate_recommendations_cache():
    keys_to_clear = ["recommendations", "latest_recommendations", "top_matches"]
    cleared_count = 0
    
    for key in keys_to_clear:
        if cache.delete(key):
            cleared_count += 1
            print(f"✓ Invalidated recommendation cache: {key}")
    
    return cleared_count