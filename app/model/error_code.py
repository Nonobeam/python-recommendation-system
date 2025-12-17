from enum import Enum


class ErrorCode(Enum):
    INVALID_REQUEST_PARAMETER = ("E_101_400_001", 400)
    INVALID_FILE_TYPE = ("E_101_400_005", 400)
    FILE_SIZE_EXCEEDED = ("E_101_400_006", 400)
    DOCUMENT_FILE_TYPE_NOT_SUPPORTED = ("E_201_400_011", 400)
    DOCUMENT_FILE_SIZE_LIMIT_EXCEEDED = ("E_201_400_012", 400)
    PAGE_SIZE_EXCEEDED = ("E_101_400_009", 400)
    INVALID_DATE_RANGE = ("E_101_400_015", 400)
    NO_AVAILABLE_BOOTHS = ("E_101_400_020", 400)
    NO_ACTIVE_COMMISSION_CONTRACT = ("E_101_400_021", 400)

    UNAUTHORIZED = ("E_101_401_001", 401)
    INVALID_CREDENTIALS = ("E_201_401_001", 401)
    INVALID_OTP = ("E_101_401_002", 401)
    OTP_EXPIRED = ("E_101_401_003", 401)

    FORBIDDEN = ("E_101_403_001", 403)

    USER_NOT_FOUND = ("E_101_404_001", 404)
    BRAND_NOT_FOUND = ("E_101_404_004", 404)
    BOOTH_NOT_FOUND = ("E_101_404_005", 404)
    MALL_NOT_FOUND = ("E_101_404_007", 404)
    NOT_FOUND = ("E_101_404_003", 404)

    DUPLICATE_EMAIL = ("E_101_409_001", 409)
    DUPLICATE_PHONE_NUMBER = ("E_101_409_002", 409)

    RATE_LIMIT_EXCEEDED = ("E_101_429_001", 429)

    INTERNAL_ERROR_SERVER = ("E_101_500_001", 500)
    INTERNAL_SERVER_ERROR = ("E_101_500_001", 500)
    INTERNAL_AUTH_SERVICE_ERROR = ("E_101_500_001", 500)
    INTERNAL_CALLING_ERROR = ("E_101_500_002", 500)

    SERVICE_UNAVAILABLE = ("E_101_503_001", 503)

    VALIDATION_ERROR = ("E_101_400_001", 400)
    AUTHENTICATION_ERROR = ("E_101_401_001", 401)
    AUTHORIZATION_ERROR = ("E_101_403_001", 403)
    BAD_REQUEST = ("E_101_400_001", 400)
    GEMINI_API_ERROR = ("E_101_503_001", 503)
    ELASTICSEARCH_ERROR = ("E_101_503_001", 503)
    DATABASE_ERROR = ("E_101_500_001", 500)
    REDIS_ERROR = ("E_101_500_001", 500)
    SCORE_CALCULATION_ERROR = ("E_101_500_001", 500)
    DEMOGRAPHICS_ERROR = ("E_101_404_001", 404)

    def __init__(self, system_code: str, http_status: int):
        self.system_code = system_code
        self.http_status = http_status

    @property
    def get_code(self) -> str:
        return self.system_code

    @property
    def get_http_status_code(self) -> int:
        return self.http_status

    def __str__(self) -> str:
        return self.system_code
