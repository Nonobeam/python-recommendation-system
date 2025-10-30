class AIProcessingError(Exception):
    """Exception raised when AI processing fails"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

    def __str__(self):
        if self.original_error:
            return f"{self.message}: {str(self.original_error)}"
        return self.message


class ElasticsearchConnectionError(Exception):
    """Exception raised when Elasticsearch connection fails"""

    pass


class SearchValidationError(Exception):
    """Exception raised when search input validation fails"""

    pass


class RecommendationError(Exception):
    """Exception raised when recommendation processing fails"""

    pass


class DatabaseConnectionError(Exception):
    """Exception raised when database connection fails"""

    pass


class MCPServerError(Exception):
    """Base exception for MCP server related errors"""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class MCPValidationError(MCPServerError):
    """Exception raised when MCP server input validation fails"""

    def __init__(self, message: str, field_name: str = None):
        self.field_name = field_name
        super().__init__(f"Validation error: {message}", "MCP_VALIDATION_ERROR")


class GeminiAPIError(MCPServerError):
    """Exception raised when Gemini API calls fail"""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(f"Gemini API error: {message}", "GEMINI_API_ERROR")
