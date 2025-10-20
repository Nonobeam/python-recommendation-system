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

# MCP Server Exceptions
class MCPServerError(Exception):
    """Base exception for MCP server related errors"""
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class MCPConnectionError(MCPServerError):
    """Exception raised when MCP server connection fails"""
    
    def __init__(self, message: str = "Failed to connect to MCP server"):
        super().__init__(message, "MCP_CONNECTION_ERROR")

class MCPToolExecutionError(MCPServerError):
    """Exception raised when MCP tool execution fails"""
    
    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' execution failed: {message}", "MCP_TOOL_ERROR")

class MCPAuthenticationError(MCPServerError):
    """Exception raised when MCP server authentication fails"""
    
    def __init__(self, message: str = "MCP server authentication failed"):
        super().__init__(message, "MCP_AUTH_ERROR")

class MCPTimeoutError(MCPServerError):
    """Exception raised when MCP server request times out"""
    
    def __init__(self, timeout_seconds: int = 30):
        super().__init__(f"MCP server request timed out after {timeout_seconds} seconds", "MCP_TIMEOUT_ERROR")
        self.timeout_seconds = timeout_seconds

class MCPValidationError(MCPServerError):
    """Exception raised when MCP server input validation fails"""
    
    def __init__(self, message: str, field_name: str = None):
        self.field_name = field_name
        super().__init__(f"Validation error: {message}", "MCP_VALIDATION_ERROR")

class MCPSecurityError(MCPServerError):
    """Exception raised when MCP server security check fails"""
    
    def __init__(self, message: str = "Security validation failed"):
        super().__init__(message, "MCP_SECURITY_ERROR")

class MCPConfigurationError(MCPServerError):
    """Exception raised when MCP server configuration is invalid"""
    
    def __init__(self, message: str = "MCP server configuration error"):
        super().__init__(message, "MCP_CONFIG_ERROR")

class MCPToolNotFoundError(MCPServerError):
    """Exception raised when requested MCP tool is not found"""
    
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"MCP tool '{tool_name}' not found", "MCP_TOOL_NOT_FOUND")

class MCPDatabaseError(MCPServerError):
    """Exception raised when MCP server database operations fail"""
    
    def __init__(self, message: str, query: str = None):
        self.query = query
        super().__init__(f"Database error: {message}", "MCP_DATABASE_ERROR")

class GeminiAPIError(MCPServerError):
    """Exception raised when Gemini API calls fail"""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(f"Gemini API error: {message}", "GEMINI_API_ERROR")