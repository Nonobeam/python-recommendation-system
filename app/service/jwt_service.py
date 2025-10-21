import jwt
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.config.jwt_config import jwt_config
from app.utils.logger import get_app_logger

logger = get_app_logger("jwt")

class JWTService:
    """JWT Service for token validation only"""
    
    def __init__(self):
        self.config = jwt_config
        
    def validate_token(self, token: str) -> bool:
        """
        Validate JWT token using the algorithm specified in the token
        Returns True if token is valid, False otherwise
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
            token_algorithm = unverified_header.get('alg')
            
            if not token_algorithm:
                logger.error("Token missing algorithm in header")
                return False
                
            allowed_algorithms = ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
            if token_algorithm not in allowed_algorithms:
                logger.error(f"Token uses unsupported algorithm: {token_algorithm}")
                return False
            
            logger.debug(f"Validating token with algorithm: {token_algorithm}")
            
            payload = jwt.decode(
                token,
                self.config.secret,
                algorithms=[token_algorithm]
            )
            
            logger.debug(f"Token decoded successfully, payload: {payload}")
            
            exp = payload.get('exp')
            if exp:
                exp_time = datetime.fromtimestamp(exp, timezone.utc)
                current_time = datetime.now(timezone.utc)
                logger.debug(f"Token expires at: {exp_time}, Current time: {current_time}")
                
                if exp_time < current_time:
                    logger.error("Expired JWT token")
                    return False
                
            logger.debug("JWT token validated successfully")
            return True
            
        except jwt.InvalidSignatureError as e:
            logger.error(f"Invalid JWT signature: {str(e)}")
        except jwt.ExpiredSignatureError as e:
            logger.error(f"Expired JWT token: {str(e)}")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {str(e)}")
        except Exception as e:
            logger.error(f"JWT validation error: {str(e)}")
            
        return False
    
    def get_token_payload(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get payload from JWT token using the token's algorithm
        Returns payload dict if successful, None otherwise
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
            token_algorithm = unverified_header.get('alg')
            
            if not token_algorithm:
                logger.error("Token missing algorithm in header")
                return None
                
            allowed_algorithms = ['HS512']
            if token_algorithm not in allowed_algorithms:
                logger.error(f"Token uses unsupported algorithm: {token_algorithm}")
                return None
            
            payload = jwt.decode(
                token,
                self.config.secret,
                algorithms=[token_algorithm]
            )
            return payload
                    
        except Exception as e:
            logger.error(f"Error getting token payload: {str(e)}")
            return None

jwt_service = JWTService()