import os

import uvicorn

from app.utils.logger import app_logger


def startup_checks():
    from app.config.elasticsearch import startup_elasticsearch_check
    from app.config.redis import startup_redis_check

    if not startup_redis_check():
        app_logger.warning("Redis connection failed - service may not work properly")
        return False

    # Build Elasticsearch connection string from environment variables
    es_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
    es_port = os.getenv("ELASTICSEARCH_PORT", "9200")
    es_protocol = os.getenv("ELASTICSEARCH_PROTOCOL", "http")
    connection = f"{es_protocol}://{es_host}:{es_port}"

    if not startup_elasticsearch_check(connection):
        app_logger.warning("Elasticsearch connection failed - search features will be unavailable")
        app_logger.info("Make sure Elasticsearch is running on " + connection)
        return False

    app_logger.info("All startup checks passed")
    return True


if __name__ == "__main__":
    startup_checks()

    port = int(os.getenv("PORT", 8000))

    app_logger.info(f"Starting server at http://0.0.0.0:{port}")
    uvicorn.run("app.rest.main:app", host="0.0.0.0", port=port, reload=True, log_level="info")
