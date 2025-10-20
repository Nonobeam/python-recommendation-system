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

class TransactionError(DatabaseError):
    """Exception raised when database transaction fails"""
    
    def __init__(self, message: str = "Database transaction failed"):
        super().__init__(message)

class IntegrityConstraintError(DatabaseError):
    """Exception raised when database integrity constraint is violated"""
    
    def __init__(self, constraint: str, message: str = None):
        self.constraint = constraint
        if message:
            super().__init__(message)
        else:
            super().__init__(f"Integrity constraint violation: {constraint}")

class UniqueConstraintError(IntegrityConstraintError):
    """Exception raised when unique constraint is violated"""
    
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"unique_{field}", f"Duplicate value '{value}' for field '{field}'")

class ForeignKeyConstraintError(IntegrityConstraintError):
    """Exception raised when foreign key constraint is violated"""
    
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"fk_{field}", f"Foreign key constraint violation: '{value}' not found in referenced table")

class DataMigrationError(DatabaseError):
    """Exception raised during data migration operations"""
    
    def __init__(self, migration_name: str, message: str):
        self.migration_name = migration_name
        super().__init__(f"Migration '{migration_name}' failed: {message}")

class ModelValidationError(DatabaseError):
    """Exception raised when model validation fails"""
    
    def __init__(self, model_name: str, field: str, value: any, message: str = None):
        self.model_name = model_name
        self.field = field
        self.value = value
        if message:
            super().__init__(message)
        else:
            super().__init__(f"Validation failed for {model_name}.{field} with value '{value}'")