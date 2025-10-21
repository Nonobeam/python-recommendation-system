import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

root_path = Path(__file__).parent.parent.parent
env_path = root_path / ".env"
load_dotenv(dotenv_path=env_path)

@dataclass
class JWTConfig:
    """JWT Configuration from environment variables"""
    secret: str
    expiration: int
    refresh_expiration: int
    issuer: str
    algorithm: str = "HS256"
    
    @classmethod
    def from_env(cls) -> 'JWTConfig':
        """Create JWT config from environment variables"""
        return cls(
            secret=os.getenv("JWT_SECRET", "mySecretKey123456789012345678901234567890"),
            expiration=int(os.getenv("JWT_EXPIRATION", "86400")),  # 24 hours
            refresh_expiration=int(os.getenv("JWT_REFRESH_EXPIRATION", "604800")),  # 7 days
            issuer=os.getenv("JWT_ISSUER", "platform-service"),
            algorithm="HS256"
        )

jwt_config = JWTConfig.from_env()