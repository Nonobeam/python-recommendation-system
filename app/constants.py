"""
Global constants for the Mall-Business Recommendation System

This module contains all application-wide constants used across different controllers and services.
Following Python best practices, constants are defined in UPPER_CASE with descriptive names.
"""

# API Header Constants
X_BR_KEY_HEADER = "X-BR-KEY"

# JWT Configuration Constants
JWT_ALGORITHM = "HS256"
JWT_TOKEN_TYPE = "Bearer"

# Pagination Constants
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1

# Search Constants
DEFAULT_SEARCH_LIMIT = 50
MAX_SEARCH_HISTORY_LIMIT = 1000
MIN_SEARCH_HISTORY_LIMIT = 1

# Cache Constants
CACHE_EXPIRY_SECONDS = 3600  # 1 hour
DEFAULT_CACHE_TTL = 86400  # 24 hours

# Database Constants
DEFAULT_DB_TIMEOUT = 30
MAX_DB_CONNECTIONS = 20

# Elasticsearch Constants
DEFAULT_ES_TIMEOUT = 30
MAX_ES_RESULTS = 10000

# API Response Constants
SUCCESS_STATUS = True
ERROR_STATUS = False

# HTTP Status Messages
HTTP_401_MESSAGE = "Authentication required"
HTTP_403_MESSAGE = "Access forbidden"
HTTP_404_MESSAGE = "Resource not found"
HTTP_500_MESSAGE = "Internal server error"
HTTP_503_MESSAGE = "Service unavailable"

# Service Names
SERVICE_NAME = "mall-recommendation-system"
SERVICE_VERSION = "1.0.0"

# Log Levels
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
