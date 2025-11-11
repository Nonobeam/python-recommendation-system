from app.model.error_code import ErrorCode


class ApplicationException(Exception):
    """Base application exception with error code support"""

    def __init__(self, error_code: ErrorCode, *args):
        self.error_code = error_code
        self.args = args
        super().__init__(str(error_code))


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


class NotFoundError(APIError):
    """Exception raised when resource is not found"""

    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", 404)
