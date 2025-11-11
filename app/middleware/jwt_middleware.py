from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.model.error_code import ErrorCode
from app.model.response_helper import error
from app.service.jwt_service import jwt_service
from app.utils.logger import get_app_logger

logger = get_app_logger("auth_middleware")


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    - Allows all requests to /pub paths
    - Requires JWT token for /pri paths
    """

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """
        Handle incoming requests and validate JWT for private paths
        """
        path = request.url.path
        method = request.method

        logger.debug(f"Processing request: {method} {path}")

        if path.startswith("/pub") or path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            logger.debug(f"Public path accessed: {path}")
            response = await call_next(request)
            return response

        if path.startswith("/pri"):
            logger.debug(f"Private path accessed, validating JWT: {path}")

            auth_header = request.headers.get("Authorization")
            if not auth_header:
                logger.warning(f"Missing Authorization header for private path: {path}")
                return error(ErrorCode.AUTHENTICATION_ERROR, "Authorization header required")

            if not auth_header.startswith("Bearer "):
                logger.warning(f"Invalid Authorization header format for path: {path}")
                return error(ErrorCode.AUTHENTICATION_ERROR, "Authorization header must be Bearer token")

            token = auth_header.split(" ")[1] if len(auth_header.split(" ")) == 2 else None
            if not token:
                logger.warning(f"Empty token in Authorization header for path: {path}")
                return error(ErrorCode.AUTHENTICATION_ERROR, "Authorization token is empty")

            logger.debug(f"Received token (first 20 chars): {token[:20]}...")

            is_valid, error_message = jwt_service.validate_token(token)
            if not is_valid:
                logger.warning(f"Invalid JWT token for path: {path}, reason: {error_message}")
                return error(ErrorCode.AUTHENTICATION_ERROR, error_message or "JWT token is invalid or expired")

            payload = jwt_service.get_token_payload(token)
            if payload:
                request.state.user = payload
                logger.debug(f"JWT validated successfully for user: {payload.get('sub', 'unknown')}")

            response = await call_next(request)
            return response

        logger.debug(f"Other path accessed without authentication: {path}")
        response = await call_next(request)
        return response
