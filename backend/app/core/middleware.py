"""Middleware for CORS, request logging, error handling, security headers, and request validation."""

import logging
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.exceptions import (
    TAPSException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    DatabaseError,
    ExternalServiceError,
)
from app.core.validators import RequestSizeLimitMiddleware
from app.core.rate_limiter import RateLimitMiddleware
from app.core.logging import get_logger, bind_correlation_id, bind_user_context, unbind_context

logger = get_logger(__name__)
stdlib_logger = logging.getLogger(__name__)  # Fallback for compatibility


class APIVersionMiddleware(BaseHTTPMiddleware):
    """Middleware to handle API version negotiation and validation."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate API version from header or URL path.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
            
        Returns:
            HTTP response or 404 for unsupported versions
        """
        # Skip version check for health endpoints, root, and API documentation
        if request.url.path in ["/", "/health", "/api/v1/docs", "/api/v1/redoc", "/api/v1/openapi.json"]:
            return await call_next(request)
        
        # Check API-Version header if provided
        api_version_header = request.headers.get("API-Version")
        
        if api_version_header:
            # Validate version from header
            if api_version_header not in settings.supported_api_versions:
                stdlib_logger.warning(
                    f"Unsupported API version requested: {api_version_header}",
                    extra={
                        "path": request.url.path,
                        "requested_version": api_version_header,
                        "supported_versions": settings.supported_api_versions,
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "error": "Unsupported API Version",
                        "message": f"API version '{api_version_header}' is not supported",
                        "supported_versions": settings.supported_api_versions,
                    },
                )
        
        # Extract version from URL path if present
        path_parts = request.url.path.split("/")
        if len(path_parts) >= 3 and path_parts[1] == "api":
            url_version = path_parts[2]
            if url_version not in settings.supported_api_versions:
                stdlib_logger.warning(
                    f"Unsupported API version in URL: {url_version}",
                    extra={
                        "path": request.url.path,
                        "requested_version": url_version,
                        "supported_versions": settings.supported_api_versions,
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "error": "Unsupported API Version",
                        "message": f"API version '{url_version}' is not supported",
                        "supported_versions": settings.supported_api_versions,
                    },
                )
        
        # Process request
        response = await call_next(request)
        
        # Add current API version to response headers
        response.headers["API-Version"] = settings.api_version
        
        return response


def setup_cors(app: FastAPI) -> None:
    """Configure CORS middleware.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming requests and responses with structured logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details with correlation ID.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
            
        Returns:
            HTTP response
        """
        # Generate correlation ID for request tracing
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Bind correlation ID to logging context
        bind_correlation_id(correlation_id)
        
        # Extract client information
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request start
        start_time = time.time()
        logger.info(
            "Request started",
            method=request.method,
            endpoint=str(request.url.path),
            url=str(request.url),
            client_host=client_host,
            user_agent=user_agent,
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log request completion
            logger.info(
                "Request completed",
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            # Calculate duration even for failed requests
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log error with stack trace
            logger.error(
                "Request failed with exception",
                method=request.method,
                endpoint=str(request.url.path),
                duration_ms=duration_ms,
                error=str(e),
                exc_info=True,
            )
            raise
        finally:
            # Clear context to prevent leakage between requests
            unbind_context()


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions and return appropriate responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle exceptions.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
            
        Returns:
            HTTP response
        """
        try:
            return await call_next(request)
        except ValidationError as e:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": "Validation Error",
                    "message": e.message,
                    "details": e.details,
                },
            )
        except AuthenticationError as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Authentication Error",
                    "message": e.message,
                    "details": e.details,
                },
            )
        except AuthorizationError as e:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Authorization Error",
                    "message": e.message,
                    "details": e.details,
                },
            )
        except NotFoundError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "Not Found",
                    "message": e.message,
                    "details": e.details,
                },
            )
        except ConflictError as e:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": "Conflict",
                    "message": e.message,
                    "details": e.details,
                },
            )
        except DatabaseError as e:
            logger.error(
                "Database error occurred",
                error_message=e.message,
                details=e.details,
                exc_info=True,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Database Error",
                    "message": "An error occurred while accessing the database",
                },
            )
        except ExternalServiceError as e:
            logger.error(
                "External service error occurred",
                error_message=e.message,
                details=e.details,
                exc_info=True,
            )
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "External Service Error",
                    "message": "An external service is temporarily unavailable",
                },
            )
        except TAPSException as e:
            logger.error(
                "Application error occurred",
                error_message=e.message,
                details=e.details,
                exc_info=True,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Application Error",
                    "message": e.message,
                    "details": e.details,
                },
            )
        except Exception as e:
            logger.error(
                "Unhandled exception occurred",
                error=str(e),
                exc_info=True,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                },
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
            
        Returns:
            HTTP response with security headers
        """
        response = await call_next(request)
        
        # Skip strict CSP for Swagger UI and ReDoc documentation pages
        is_docs_page = request.url.path in ["/api/v1/docs", "/api/v1/redoc"]
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Relax CSP for documentation pages to allow Swagger UI assets
        if is_docs_page:
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; img-src 'self' data: cdn.jsdelivr.net"
        else:
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the application.
    
    Args:
        app: FastAPI application instance
    """
    # Add CORS middleware
    setup_cors(app)
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add request size limit middleware (10MB limit)
    app.add_middleware(RequestSizeLimitMiddleware)
    
    # Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware)
    
    # Add API version validation middleware
    app.add_middleware(APIVersionMiddleware)
    
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Add error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)
