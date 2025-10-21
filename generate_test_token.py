#!/usr/bin/env python3
"""
JWT Token Generator for Testing
Creates a valid JWT token using the same configuration as the service
"""

import jwt
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

# Add the app directory to the path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from config.jwt_config import jwt_config

def generate_test_token(user_id: str = "test_user", expires_in_hours: int = 24):
    """Generate a test JWT token"""
    
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(hours=expires_in_hours)
    
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int(expiration.timestamp()),
        "iss": jwt_config.issuer,
        "user_id": user_id,
        "username": "test_user"
    }
    
    token = jwt.encode(
        payload,
        jwt_config.secret,
        algorithm=jwt_config.algorithm
    )
    
    print(f"Generated JWT Token:")
    print(f"Token: {token}")
    print(f"")
    print(f"Config used:")
    print(f"- Secret: {jwt_config.secret[:20]}...")
    print(f"- Algorithm: {jwt_config.algorithm}")
    print(f"- Issuer: {jwt_config.issuer}")
    print(f"")
    print(f"Payload:")
    print(f"- Subject: {payload['sub']}")
    print(f"- Issued at: {datetime.fromtimestamp(payload['iat'], timezone.utc)}")
    print(f"- Expires at: {datetime.fromtimestamp(payload['exp'], timezone.utc)}")
    print(f"- Issuer: {payload['iss']}")
    print(f"")
    print(f"To test with curl:")
    print(f'curl -H "Authorization: Bearer {token}" http://localhost:8000/pri/api/v1/recommendations')
    
    return token

if __name__ == "__main__":
    generate_test_token()