class RedisConnectionError(Exception):
    """Raised when Redis connection fails"""

    def __init__(self, message="Redis connection failed"):
        self.message = message
        super().__init__(self.message)


class RedisOperationError(Exception):
    """Raised when Redis operations fail"""

    def __init__(self, operation, key=None, message=None):
        if message:
            self.message = message
        elif key:
            self.message = f"Redis {operation} operation failed for key: {key}"
        else:
            self.message = f"Redis {operation} operation failed"
        super().__init__(self.message)


class CacheError(Exception):
    """Base exception for cache-related errors"""

    def __init__(self, message="Cache operation failed"):
        self.message = message
        super().__init__(self.message)


class DemographicDataError(CacheError):
    """Raised when demographic data is missing or invalid"""

    def __init__(self, entity_id, entity_type="entity", message=None):
        if message:
            self.message = message
        else:
            self.message = f"Demographic data not available for {entity_type} {entity_id} - demographic data must be in Redis cache"
        super().__init__(self.message)


class BusinessDataError(CacheError):
    """Raised when business data is missing or invalid"""

    def __init__(self, business_id, message=None):
        if message:
            self.message = message
        else:
            self.message = f"Business demographic data not available for business {business_id} - demographic data must be in Redis cache"
        super().__init__(self.message)
