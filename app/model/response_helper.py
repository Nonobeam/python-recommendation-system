from typing import TypeVar

from fastapi import status
from fastapi.responses import JSONResponse

from app.model.api_models import ApiResp, ErrorResp
from app.model.error_code import ErrorCode

T = TypeVar("T")


def success(data: T, status_code: int = status.HTTP_200_OK) -> JSONResponse:
    """
    Create a successful API response.

    Args:
        data: The data to return in the response
        status_code: HTTP status code (default: 200)

    Returns:
        JSONResponse with success=true and data
    """
    response = ApiResp(success=True, data=data, error=None)
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(exclude_none=True),
    )


def error(error_code: ErrorCode, message: str, details: dict = None) -> JSONResponse:
    """
    Create an error API response.

    Args:
        error_code: The error code enum
        message: Error message
        details: Optional additional error details

    Returns:
        JSONResponse with success=false and error details
    """
    error_resp = ErrorResp(code=error_code.get_code, message=message, details=details)
    response = ApiResp(success=False, data=None, error=error_resp)
    return JSONResponse(
        status_code=error_code.get_http_status_code,
        content=response.model_dump(exclude_none=True),
    )
