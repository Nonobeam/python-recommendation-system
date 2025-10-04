import uvicorn
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def startup_checks():
    """Perform startup health checks"""
    print("=== STARTUP CHECKS ===")
    
    from app.config.redis import startup_redis_check
    
    if not startup_redis_check():
        print("✗ Redis connection failed - service may not work properly")
        return False
    
    print("✓ All startup checks passed")
    return True

if __name__ == "__main__":
    startup_checks()
    
    print("=== STARTING API SERVICE ===")
    uvicorn.run(
        "app.rest.api:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )