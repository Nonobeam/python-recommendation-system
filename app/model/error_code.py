from enum import Enum


class ErrorCode(Enum):
    VALIDATION_ERROR = 400
    AUTHENTICATION_ERROR = 401
    AUTHORIZATION_ERROR = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503
    BAD_REQUEST = 400
    GEMINI_API_ERROR = 503
    ELASTICSEARCH_ERROR = 503
    DATABASE_ERROR = 500
    REDIS_ERROR = 500
    SCORE_CALCULATION_ERROR = 500
    DEMOGRAPHICS_ERROR = 404

    @property
    def get_code(self) -> str:
        return self.name

    @property
    def get_http_status_code(self) -> int:
        return self.value

    def __str__(self) -> str:
        return self.name
