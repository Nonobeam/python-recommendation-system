from typing import Any, List, Optional, TypeVar, Union

from fastapi import status
from fastapi.responses import JSONResponse

from app.model.api_models import ApiResp, ErrorResp, FieldError
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


def _convert_validation_errors_to_field_errors(errors: List[dict]) -> List[FieldError]:
    """
    Convert FastAPI validation errors to FieldError list.

    Args:
        errors: List of FastAPI validation error dictionaries

    Returns:
        List of FieldError objects
    """
    field_errors = []
    for error in errors:
        field_path = ".".join(str(loc) for loc in error.get("loc", []))
        if field_path == "body":
            field_path = error.get("loc", [])[-1] if len(error.get("loc", [])) > 1 else "body"
        else:
            field_path = field_path.replace("body.", "")

        field_errors.append(FieldError(field=field_path, message=error.get("msg", "Validation error")))
    return field_errors


def error(
    error_code: ErrorCode, message: str, details: Optional[Union[List[FieldError], List[dict], dict, Any]] = None
) -> JSONResponse:
    """
    Create an error API response.

    Args:
        error_code: The error code enum
        message: Error message
        details: Optional additional error details. Can be:
            - List[FieldError]: Field-level validation errors
            - List[dict]: FastAPI validation errors (will be converted to FieldError)
            - dict: Other error details
            - Any: Other error details

    Returns:
        JSONResponse with success=false and error details
    """
    processed_details = None

    if details is not None:
        if isinstance(details, list) and len(details) > 0:
            if isinstance(details[0], dict) and "loc" in details[0]:
                processed_details = _convert_validation_errors_to_field_errors(details)
            elif isinstance(details[0], FieldError):
                processed_details = details
            else:
                processed_details = details
        else:
            processed_details = details

    error_resp = ErrorResp(code=error_code.get_code, message=message, details=processed_details)
    response = ApiResp(success=False, data=None, error=error_resp)
    return JSONResponse(
        status_code=error_code.get_http_status_code,
        content=response.model_dump(exclude_none=True),
    )
