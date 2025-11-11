from datetime import datetime, timezone
from typing import Any, Dict, Optional

import jwt

from app.config.jwt_config import jwt_config
from app.utils.logger import get_app_logger


def get_system_time_utc() -> datetime:
    """
    Get current system time in UTC.
    Uses the system clock and returns time in UTC timezone.
    """
    import time

    system_timestamp = time.time()
    logger.info(system_timestamp)
    return datetime.fromtimestamp(system_timestamp, timezone.utc)


logger = get_app_logger("jwt")


class JWTService:
    """JWT Service for token validation only"""

    def __init__(self, leeway_seconds: int = 60):
        self.config = jwt_config
        self.leeway_seconds = leeway_seconds

    def validate_token(self, token: str) -> tuple[bool, Optional[str]]:
        """
        Validate JWT token using the algorithm specified in the token
        Returns tuple of (is_valid: bool, error_message: Optional[str])
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
            token_algorithm = unverified_header.get("alg")

            if not token_algorithm:
                error_msg = "Token missing algorithm in header"
                logger.error(error_msg)
                return False, error_msg

            allowed_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
            if token_algorithm not in allowed_algorithms:
                error_msg = f"Token uses unsupported algorithm: {token_algorithm}"
                logger.error(error_msg)
                return False, error_msg

            logger.debug(f"Validating token with algorithm: {token_algorithm}")

            payload = jwt.decode(token, self.config.secret, algorithms=[token_algorithm], options={"verify_exp": False})

            logger.debug(f"Token decoded successfully, payload: {payload}")

            exp = payload.get("exp")
            if exp:
                exp_time = datetime.fromtimestamp(exp, timezone.utc)
                current_time = get_system_time_utc()
                time_diff = (exp_time - current_time).total_seconds()

                logger.debug(
                    f"Token expires at: {exp_time.isoformat()}, "
                    f"Current system time (UTC): {current_time.isoformat()}, "
                    f"Time difference: {time_diff:.1f} seconds"
                )

                if time_diff < -self.leeway_seconds:
                    error_msg = (
                        f"Token expired {abs(time_diff):.0f} seconds ago "
                        f"(expired at {exp_time.isoformat()} UTC, "
                        f"current system time: {current_time.isoformat()} UTC)"
                    )
                    logger.error(error_msg)
                    return False, error_msg

            logger.debug("JWT token validated successfully")
            return True, None

        except jwt.InvalidSignatureError as e:
            error_msg = "Invalid JWT signature - secret key may not match"
            logger.error(f"{error_msg}: {str(e)}")
            return False, error_msg
        except jwt.ExpiredSignatureError as e:
            try:
                unverified_payload = jwt.decode(token, key="", options={"verify_signature": False, "verify_exp": False})
                exp = unverified_payload.get("exp")
                if exp:
                    exp_time = datetime.fromtimestamp(exp, timezone.utc)
                    current_time = get_system_time_utc()
                    time_diff = (current_time - exp_time).total_seconds()
                    import time

                    local_timestamp = time.time()
                    local_time = datetime.fromtimestamp(local_timestamp)
                    error_msg = (
                        f"Token expired {time_diff:.0f} seconds ago "
                        f"(expired at {exp_time.isoformat()} UTC, "
                        f"current system time: {local_time.isoformat()} / "
                        f"{current_time.isoformat()} UTC)"
                    )
                else:
                    error_msg = f"Token has expired: {str(e)}"
            except Exception:
                error_msg = f"Token has expired: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except jwt.DecodeError as e:
            error_msg = f"Token decode error - invalid token format: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except jwt.InvalidTokenError as e:
            error_msg = f"Invalid JWT token: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"JWT validation error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_token_payload(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get payload from JWT token using the token's algorithm
        Returns payload dict if successful, None otherwise
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
            token_algorithm = unverified_header.get("alg")

            if not token_algorithm:
                logger.error("Token missing algorithm in header")
                return None

            allowed_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
            if token_algorithm not in allowed_algorithms:
                logger.error(f"Token uses unsupported algorithm: {token_algorithm}")
                return None

            payload = jwt.decode(token, self.config.secret, algorithms=[token_algorithm], options={"verify_exp": False})

            exp = payload.get("exp")
            if exp:
                exp_time = datetime.fromtimestamp(exp, timezone.utc)
                current_time = get_system_time_utc()
                time_diff = (exp_time - current_time).total_seconds()

                if time_diff < -self.leeway_seconds:
                    logger.error(f"Token expired when getting payload: {abs(time_diff):.0f} seconds ago")
                    return None

            return payload

        except Exception as e:
            logger.error(f"Error getting token payload: {str(e)}")
            return None


jwt_service = JWTService()
