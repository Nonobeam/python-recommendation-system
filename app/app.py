import uvicorn
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def startup_checks():
    from app.config.redis import startup_redis_check
    from app.config.elasticsearch import startup_elasticsearch_check
    
    if not startup_redis_check():
        print("Redis connection failed - service may not work properly")
        return False
    
    if not startup_elasticsearch_check():
        print("Elasticsearch connection failed - search features will be unavailable")
        print("Make sure Elasticsearch is running on http://localhost:9200")
        return False

    print("All startup checks passed")
    return True

if __name__ == "__main__":
    startup_checks()

    port = int(os.getenv("PORT", 8000))

    print(f"Starting server at http://0.0.0.0:{port}")
    uvicorn.run(
        "app.rest.main:app",
        host="0.0.0.0", 
        port=port,
        reload=True,
        log_level="info"
    )