from fastapi import HTTPException, Request, status

from app.service.jwt_service import jwt_service
from app.utils.logger import get_app_logger

logger = get_app_logger("token_data")


class TokenData:
    """Token data extracted from JWT payload"""

    def __init__(self, user_id: str, role: str = None, email: str = None):
        self.user_id = user_id
        self.role = role
        self.email = email

    def __str__(self):
        return f"TokenData(user_id={self.user_id}, role={self.role}, email={self.email})"


def get_current_user(request: Request) -> TokenData:
    """Extract and validate current user from JWT token"""
    try:
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            logger.warning("Missing Authorization header")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header required")

        if not auth_header.startswith("Bearer "):
            logger.warning("Invalid Authorization header format")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format")

        token = auth_header.split(" ")[1]

        is_valid, error_message = jwt_service.validate_token(token)
        if not is_valid:
            logger.warning(f"Invalid JWT token provided: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=error_message or "Invalid or expired token"
            )

        payload = jwt_service.get_token_payload(token)
        if not payload:
            logger.error("Unable to extract payload from valid token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token payload extraction failed")

        user_id = payload.get("userId")
        if not user_id:
            logger.warning("Token missing required 'userId' claim")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing user identification")

        token_data = TokenData(user_id=user_id, role=payload.get("role"), email=payload.get("email"))

        return token_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")
