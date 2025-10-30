class DatabaseError(Exception):
    """Base exception for database-related errors"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class DatabaseConnectionError(DatabaseError):
    """Exception raised when database connection fails"""

    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message)


class QueryExecutionError(DatabaseError):
    """Exception raised when SQL query execution fails"""

    def __init__(self, query: str, message: str, original_error: Exception = None):
        self.query = query
        super().__init__(f"Query execution failed: {message}", original_error)
