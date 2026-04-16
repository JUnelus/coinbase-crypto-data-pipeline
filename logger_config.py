"""Logging configuration for the Coinbase crypto pipeline.

Provides structured logging with both console and file output.
"""

import logging
import logging.handlers
from config import settings


def setup_logging():
    """Configure logging for the application.

    Sets up both console and file handlers with consistent formatting.
    Should be called once at application startup.
    """
    logger = logging.getLogger("crypto_pipeline")

    # Only configure if not already configured
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Create formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10_485_760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Module name, typically __name__

    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"crypto_pipeline.{name}")


# Initialize logging at module import
logger = setup_logging()

__all__ = ["setup_logging", "get_logger", "logger"]

