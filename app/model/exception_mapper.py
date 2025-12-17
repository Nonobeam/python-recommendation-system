from app.exception.api_exceptions import APIError, AuthenticationError, NotFoundError, ValidationError
from app.exception.cache_exceptions import RedisConnectionError, RedisOperationError
from app.exception.custom_exceptions import ElasticsearchConnectionError, GeminiAPIError
from app.exception.database_exceptions import DatabaseError, QueryExecutionError
from app.exception.recommendation_exceptions import (
    DemographicsError,
    NoActiveCommissionContractError,
    NoAvailableBoothsError,
    ScoreCalculationError,
)
from app.model.error_code import ErrorCode


def map_exception_to_error_code(exception: Exception) -> tuple[ErrorCode, str]:
    """
    Map an exception to an ErrorCode and message.

    Args:
        exception: The exception to map

    Returns:
        Tuple of (ErrorCode, message)
    """
    if isinstance(exception, ValidationError):
        return ErrorCode.VALIDATION_ERROR, str(exception)
    elif isinstance(exception, AuthenticationError):
        return ErrorCode.AUTHENTICATION_ERROR, str(exception)
    elif isinstance(exception, NotFoundError):
        return ErrorCode.NOT_FOUND, str(exception)
    elif isinstance(exception, DemographicsError):
        return ErrorCode.DEMOGRAPHICS_ERROR, str(exception)
    elif isinstance(exception, ScoreCalculationError):
        return ErrorCode.SCORE_CALCULATION_ERROR, str(exception)
    elif isinstance(exception, NoAvailableBoothsError):
        return ErrorCode.NO_AVAILABLE_BOOTHS, str(exception)
    elif isinstance(exception, NoActiveCommissionContractError):
        return ErrorCode.NO_ACTIVE_COMMISSION_CONTRACT, str(exception)
    elif isinstance(exception, GeminiAPIError):
        return ErrorCode.GEMINI_API_ERROR, str(exception)
    elif isinstance(exception, ElasticsearchConnectionError):
        return ErrorCode.ELASTICSEARCH_ERROR, str(exception)
    elif isinstance(exception, DatabaseError) or isinstance(exception, QueryExecutionError):
        return ErrorCode.DATABASE_ERROR, str(exception)
    elif isinstance(exception, RedisConnectionError) or isinstance(exception, RedisOperationError):
        return ErrorCode.REDIS_ERROR, str(exception)
    elif isinstance(exception, APIError):
        status_code = exception.status_code
        if status_code == 400:
            return ErrorCode.BAD_REQUEST, str(exception)
        elif status_code == 401:
            return ErrorCode.AUTHENTICATION_ERROR, str(exception)
        elif status_code == 403:
            return ErrorCode.AUTHORIZATION_ERROR, str(exception)
        elif status_code == 404:
            return ErrorCode.NOT_FOUND, str(exception)
        elif status_code == 503:
            return ErrorCode.SERVICE_UNAVAILABLE, str(exception)
        else:
            return ErrorCode.INTERNAL_SERVER_ERROR, str(exception)
    else:
        return ErrorCode.INTERNAL_SERVER_ERROR, str(exception)
