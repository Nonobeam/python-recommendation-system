from .cache_exceptions import (
    RedisConnectionError,
    RedisOperationError,
    CacheError,
    CacheMissError,
    DemographicDataError,
    BusinessDataError
)

from .custom_exceptions import (
    AIProcessingError,
    ElasticsearchConnectionError,
    SearchValidationError,
    RecommendationError,
    DatabaseConnectionError,
    MCPServerError,
    MCPConnectionError,
    MCPToolExecutionError,
    MCPAuthenticationError,
    MCPTimeoutError,
    MCPValidationError,
    MCPSecurityError,
    MCPConfigurationError,
    MCPToolNotFoundError,
    MCPDatabaseError,
    GeminiAPIError
)

from .api_exceptions import (
    APIError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ServiceUnavailableError,
    ExternalServiceError
)

from .database_exceptions import (
    DatabaseError,
    QueryExecutionError,
    TransactionError,
    IntegrityConstraintError,
    UniqueConstraintError,
    ForeignKeyConstraintError,
    DataMigrationError,
    ModelValidationError
)

from .recommendation_exceptions import (
    InsufficientDataError,
    FeatureExtractionError,
    ModelTrainingError,
    ScoreCalculationError,
    DemographicsError,
    TrafficAnalysisError,
    BudgetCompatibilityError
)

__all__ = [
    # Cache exceptions
    "RedisConnectionError",
    "RedisOperationError", 
    "CacheError",
    "CacheMissError",
    "DemographicDataError",
    "BusinessDataError",
    
    # Custom exceptions
    "AIProcessingError",
    "ElasticsearchConnectionError",
    "SearchValidationError",
    "RecommendationError",
    "DatabaseConnectionError",
    
    # MCP exceptions
    "MCPServerError",
    "MCPConnectionError",
    "MCPToolExecutionError",
    "MCPAuthenticationError",
    "MCPTimeoutError",
    "MCPValidationError",
    "MCPSecurityError",
    "MCPConfigurationError",
    "MCPToolNotFoundError",
    "MCPDatabaseError",
    "GeminiAPIError",
    
    # API exceptions
    "APIError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ServiceUnavailableError",
    "ExternalServiceError",
    
    # Database exceptions
    "DatabaseError",
    "QueryExecutionError",
    "TransactionError",
    "IntegrityConstraintError",
    "UniqueConstraintError",
    "ForeignKeyConstraintError",
    "DataMigrationError",
    "ModelValidationError",
    
    # Recommendation exceptions
    "InsufficientDataError",
    "FeatureExtractionError",
    "ModelTrainingError",
    "ScoreCalculationError",
    "DemographicsError",
    "TrafficAnalysisError",
    "BudgetCompatibilityError"
]