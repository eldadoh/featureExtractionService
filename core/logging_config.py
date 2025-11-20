"""
Structured logging configuration using structlog.
Provides consistent, machine-readable logs with metadata.

Example Usage:
    from core.logging_config import get_logger
    
    logger = get_logger(__name__)
    logger.info("Processing image", image_id="123", latency_ms=45.2)
    
Output (JSON):
    {
        "event": "Processing image",
        "image_id": "123",
        "latency_ms": 45.2,
        "timestamp": "2025-11-19T10:30:45.123Z",
        "level": "info",
        "logger": "services.feature_service"
    }
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from core.config import settings


def configure_logging() -> None:
    """
    Configure structured logging for the application.
    
    Sets up:
    - JSON formatting for production
    - Console formatting for development
    - Consistent timestamp format
    - Exception formatting
    - Log level filtering
    """
    
    # Shared processors for all loggers
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Choose renderer based on environment
    if settings.log_format == "json":
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    
    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured structured logger
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Request processed", request_id="abc123", duration_ms=42)
    """
    return structlog.get_logger(name)


# Initialize logging on module import
configure_logging()

