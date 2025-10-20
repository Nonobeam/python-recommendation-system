class APIError(Exception):
    """Base exception for API-related errors"""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(APIError):
    """Exception raised when request validation fails"""
    
    def __init__(self, message: str, field_name: str = None):
        self.field_name = field_name
        super().__init__(message, 400)

class AuthenticationError(APIError):
    """Exception raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)

class AuthorizationError(APIError):
    """Exception raised when authorization fails"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, 403)

class NotFoundError(APIError):
    """Exception raised when resource is not found"""
    
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", 404)

class ConflictError(APIError):
    """Exception raised when there's a conflict with existing data"""
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, 409)

class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message, 429)

class ServiceUnavailableError(APIError):
    """Exception raised when service is temporarily unavailable"""
    
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(message, 503)

class ExternalServiceError(APIError):
    """Exception raised when external service calls fail"""
    
    def __init__(self, service_name: str, message: str, status_code: int = 502):
        self.service_name = service_name
        super().__init__(f"{service_name} service error: {message}", status_code)