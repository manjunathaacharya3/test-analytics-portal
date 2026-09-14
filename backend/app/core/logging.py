"""Structured logging configuration with JSON formatting and correlation ID support.

This module configures structlog for production-ready JSON logging with:
- Correlation IDs for request tracing
- Automatic context propagation
- Sensitive data redaction
- Environment-based log levels
- Stack trace inclusion for errors
"""

import logging
import sys
from typing import Any, Dict, Optional
import structlog
from structlog.types import EventDict, Processor
from datetime import datetime, timezone

from app.core.config import settings


# Sensitive fields that should be redacted from logs
SENSITIVE_FIELDS = {
    "password",
    "hashed_password",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "api_key",
    "secret",
    "jwt",
    "bearer",
}


def redact_sensitive_data(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Redact sensitive data from log entries.
    
    Args:
        logger: Logger instance
        method_name: Name of the logging method
        event_dict: Event dictionary to process
        
    Returns:
        Event dictionary with sensitive data redacted
    """
    def _redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact sensitive fields in dictionaries."""
        redacted = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = _redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = [_redact_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                redacted[key] = value
        return redacted
    
    # Redact sensitive data from the event dict
    return _redact_dict(event_dict)


def add_timestamp(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add ISO 8601 timestamp to log entries.
    
    Args:
        logger: Logger instance
        method_name: Name of the logging method
        event_dict: Event dictionary to process
        
    Returns:
        Event dictionary with timestamp added
    """
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return event_dict


def add_service_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add service context to log entries.
    
    Args:
        logger: Logger instance
        method_name: Name of the logging method
        event_dict: Event dictionary to process
        
    Returns:
        Event dictionary with service context added
    """
    event_dict["service"] = "taps-backend"
    event_dict["environment"] = settings.environment
    return event_dict


def extract_from_record(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Extract useful information from the logging record.
    
    Args:
        logger: Logger instance
        method_name: Name of the logging method
        event_dict: Event dictionary to process
        
    Returns:
        Event dictionary with record information extracted
    """
    record = event_dict.get("_record")
    if record:
        event_dict["logger_name"] = record.name
        event_dict["module"] = record.module
        event_dict["function"] = record.funcName
        event_dict["line_number"] = record.lineno
    return event_dict


def configure_logging() -> None:
    """Configure structured logging for the application.
    
    Sets up structlog with:
    - JSON formatting for production
    - Console formatting for development
    - Correlation ID support
    - Sensitive data redaction
    - Automatic context propagation
    """
    # Determine log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Define processors for structlog
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,  # Merge context variables (correlation_id, etc.)
        structlog.stdlib.add_log_level,  # Add log level
        structlog.stdlib.add_logger_name,  # Add logger name
        add_timestamp,  # Add ISO 8601 timestamp
        add_service_context,  # Add service and environment context
        structlog.stdlib.PositionalArgumentsFormatter(),  # Format positional args
        structlog.processors.StackInfoRenderer(),  # Render stack info if present
        structlog.processors.format_exc_info,  # Format exception info
        redact_sensitive_data,  # Redact sensitive data
    ]
    
    # Add appropriate renderer based on environment
    if settings.environment == "development" and settings.debug:
        # Pretty console output for development
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        )
    else:
        # JSON output for production
        processors.append(
            structlog.processors.JSONRenderer()
        )
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (defaults to calling module)
        
    Returns:
        Configured structlog logger instance
    """
    return structlog.get_logger(name)


def bind_correlation_id(correlation_id: str) -> None:
    """Bind correlation ID to the current context.
    
    This makes the correlation ID available to all log entries
    within the current request context.
    
    Args:
        correlation_id: Unique request correlation ID
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def bind_user_context(user_id: Optional[str] = None, user_email: Optional[str] = None) -> None:
    """Bind user context to the current logging context.
    
    Args:
        user_id: User ID if authenticated
        user_email: User email if authenticated
    """
    if user_id:
        structlog.contextvars.bind_contextvars(user_id=user_id)
    if user_email:
        structlog.contextvars.bind_contextvars(user_email=user_email)


def unbind_context() -> None:
    """Clear all context variables.
    
    Should be called at the end of request processing to prevent
    context leakage between requests.
    """
    structlog.contextvars.clear_contextvars()


# Configure logging on module import
configure_logging()


# Export commonly used functions
__all__ = [
    "configure_logging",
    "get_logger",
    "bind_correlation_id",
    "bind_user_context",
    "unbind_context",
]
