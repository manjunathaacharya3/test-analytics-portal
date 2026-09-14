"""Request validation middleware for payload size, content type, and schema validation."""

import logging
from typing import Callable, List, Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request size limits."""
    
    def __init__(self, app, max_size: int = None):
        """Initialize request size limit middleware.
        
        Args:
            app: FastAPI application instance
            max_size: Maximum request size in bytes (default from settings)
        """
        super().__init__(app)
        self.max_size = max_size or settings.max_request_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and enforce size limit.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
            
        Returns:
            HTTP response or 413 if request too large
        """
        # Skip size check for GET requests (no body)
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)
        
        # Check Content-Length header
        content_length = request.headers.get("Content-Length")
        
        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size:
                logger.warning(
                    f"Request size {content_length} bytes exceeds limit {self.max_size} bytes",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                        "content_length": content_length,
                        "max_size": self.max_size,
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "error": "Request Too Large",
                        "message": f"Request size {content_length} bytes exceeds maximum allowed size of {self.max_size} bytes ({self.max_size // (1024 * 1024)} MB)",
                        "max_size_bytes": self.max_size,
                        "max_size_mb": self.max_size // (1024 * 1024),
                    }
                )
        
        # Process request
        response = await call_next(request)
        return response


class ContentTypeValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate request content types."""
    
    # Default allowed content types for different endpoints
    DEFAULT_ALLOWED_TYPES = [
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data",
    ]
    
    def __init__(
        self,
        app,
        allowed_types: Optional[List[str]] = None,
        strict: bool = False
    ):
        """Initialize content type validation middleware.
        
        Args:
            app: FastAPI application instance
            allowed_types: List of allowed content types (default: JSON, form data)
            strict: If True, reject requests with no Content-Type header
        """
        super().__init__(app)
        self.allowed_types = allowed_types or self.DEFAULT_ALLOWED_TYPES
        self.strict = strict
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and validate content type.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
            
        Returns:
            HTTP response or 415 if unsupported media type
        """
        # Skip validation for GET, HEAD, OPTIONS, DELETE (no body expected)
        if request.method in ["GET", "HEAD", "OPTIONS", "DELETE"]:
            return await call_next(request)
        
        # Skip validation for health and docs endpoints
        if request.url.path in ["/", "/health", "/api/v1/health", "/api/v1/docs", "/api/v1/redoc", "/api/v1/openapi.json"]:
            return await call_next(request)
        
        # Get Content-Type header
        content_type = request.headers.get("Content-Type", "").lower()
        
        # Handle missing Content-Type
        if not content_type:
            if self.strict:
                logger.warning(
                    f"Request missing Content-Type header",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={
                        "error": "Missing Content-Type",
                        "message": "Content-Type header is required for this request",
                        "allowed_types": self.allowed_types,
                    }
                )
            # Non-strict mode: allow requests without Content-Type
            return await call_next(request)
        
        # Extract base content type (remove charset, boundary, etc.)
        base_content_type = content_type.split(";")[0].strip()
        
        # Check if content type is allowed
        is_allowed = any(
            allowed_type in base_content_type
            for allowed_type in self.allowed_types
        )
        
        if not is_allowed:
            logger.warning(
                f"Unsupported content type: {base_content_type}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "content_type": base_content_type,
                    "allowed_types": self.allowed_types,
                }
            )
            return JSONResponse(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                content={
                    "error": "Unsupported Media Type",
                    "message": f"Content-Type '{base_content_type}' is not supported",
                    "received_type": base_content_type,
                    "allowed_types": self.allowed_types,
                }
            )
        
        # Process request
        response = await call_next(request)
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Combined middleware for request validation (size, content type, headers)."""
    
    def __init__(self, app):
        """Initialize request validation middleware.
        
        Args:
            app: FastAPI application instance
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and perform validation checks.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
            
        Returns:
            HTTP response or error if validation fails
        """
        # Skip validation for health and docs endpoints
        if request.url.path in ["/", "/health", "/api/v1/health", "/api/v1/docs", "/api/v1/redoc", "/api/v1/openapi.json"]:
            return await call_next(request)
        
        # Validate required headers for API requests
        if request.url.path.startswith("/api/v1/"):
            # Check for common security headers
            user_agent = request.headers.get("User-Agent")
            if not user_agent:
                logger.debug(
                    f"Request missing User-Agent header",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                    }
                )
                # Don't reject, just log for monitoring
        
        # Validate request method
        allowed_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
        if request.method not in allowed_methods:
            logger.warning(
                f"Unsupported HTTP method: {request.method}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                }
            )
            return JSONResponse(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                content={
                    "error": "Method Not Allowed",
                    "message": f"HTTP method '{request.method}' is not allowed",
                    "allowed_methods": allowed_methods,
                }
            )
        
        # Process request
        response = await call_next(request)
        return response


def validate_json_payload(payload: dict, required_fields: List[str]) -> Optional[str]:
    """Validate JSON payload has required fields.
    
    Args:
        payload: JSON payload dictionary
        required_fields: List of required field names
        
    Returns:
        Error message if validation fails, None if valid
    """
    missing_fields = []
    for field in required_fields:
        if field not in payload:
            missing_fields.append(field)
    
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
    
    return None


def validate_field_types(payload: dict, field_types: dict) -> Optional[str]:
    """Validate field types in JSON payload.
    
    Args:
        payload: JSON payload dictionary
        field_types: Dictionary mapping field names to expected types
        
    Returns:
        Error message if validation fails, None if valid
    """
    type_errors = []
    for field, expected_type in field_types.items():
        if field in payload:
            value = payload[field]
            if not isinstance(value, expected_type):
                type_errors.append(
                    f"Field '{field}' must be of type {expected_type.__name__}, got {type(value).__name__}"
                )
    
    if type_errors:
        return "; ".join(type_errors)
    
    return None
