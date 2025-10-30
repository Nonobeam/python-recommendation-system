import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

root_path = Path(__file__).parent.parent.parent
env_path = root_path / ".env"
load_dotenv(dotenv_path=env_path)


def setup_logger(
    name: str, level: Optional[str] = None, log_file: Optional[str] = None, format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup a logger with consistent formatting and configuration

    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for file logging
        format_string: Custom format string

    Returns:
        Configured logger instance
    """

    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()

    if not format_string:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level, logging.INFO))
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_app_logger(component: str) -> logging.Logger:
    """
    Get a standardized logger for application components

    Args:
        component: Component name (e.g., 'elasticsearch', 'redis', 'api')

    Returns:
        Configured logger for the component
    """
    log_file = os.getenv("LOG_FILE")
    if log_file:
        log_file = os.path.join(Path(__file__).parent.parent.parent, "logs", f"{component}.log")

    return setup_logger(name=f"recommendation_system.{component}", log_file=log_file)


elasticsearch_logger = get_app_logger("elasticsearch")
redis_logger = get_app_logger("redis")
api_logger = get_app_logger("api")
etl_logger = get_app_logger("etl")
cache_logger = get_app_logger("cache")
app_logger = get_app_logger("app")


def log_access_message(
    logger: logging.Logger,
    log_level: str,
    event_type: str,
    entity_type: str,
    entity_id: str = None,
    message: str = None,
    **kwargs,
):
    """
    Log a standardized access message for cache/database/events.

    Args:
        logger: Logger object to use (e.g. api_logger)
        log_level: Log level string ('debug', 'info', etc.)
        event_type: Type of event/action (e.g. 'cache_hit', 'cache_miss', 'db_query', etc.)
        entity_type: Type of entity (e.g. 'brand', 'mall')
        entity_id: ID of the involved entity (optional)
        message: Free-form message (optional, will append to auto-structured string)
        **kwargs: Any extra context
    """
    level_method = getattr(logger, log_level.lower(), None)
    if not level_method:
        logger.info("[log_access_message] Unknown log level: %s", log_level)
        level_method = logger.info
    parts = [f"{event_type.upper()} [{entity_type}"]
    if entity_id:
        parts[-1] += f":{entity_id}"  # Merge entity type and id
    parts[-1] += "]"
    if message:
        parts.append(message)
    if kwargs:
        # Log extra context as JSON-like dictionary for grep/searchability
        parts.append(str(kwargs))
    level_method(" ".join(parts))
