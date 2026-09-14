"""Rate limiting middleware using Redis for distributed rate limiting."""

import logging
from typing import Optional, Tuple

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-backed rate limiter with support for per-IP and per-user limits."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.redis_client = None
    
    async def _get_client(self):
        """Get Redis client instance."""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    async def is_rate_limited(
        self,
        key: str,
        limit: int,
        window: int
    ) -> Tuple[bool, int, int]:
        """Check if a request should be rate limited.
        
        Args:
            key: Redis key for rate limiting (e.g., 'rate_limit:ip:127.0.0.1')
            limit: Maximum number of requests allowed in the window
            window: Time window in seconds
            
        Returns:
            Tuple of (is_limited, current_count, remaining_requests)
        """
        try:
            client = await self._get_client()
            
            # Increment counter
            current = await client.incr(key)
            
            # Set expiration on first request
            if current == 1:
                await client.expire(key, window)
            
            # Check if limit exceeded
            is_limited = current > limit
            remaining = max(0, limit - current)
            
            return is_limited, current, remaining
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if Redis is unavailable
            return False, 0, limit
    
    async def get_rate_limit_info(
        self,
        key: str,
        limit: int
    ) -> Tuple[int, int]:
        """Get current rate limit information.
        
        Args:
            key: Redis key for rate limiting
            limit: Maximum number of requests allowed
            
        Returns:
            Tuple of (current_count, remaining_requests)
        """
        try:
            client = await self._get_client()
            current = await client.get(key)
            current = int(current) if current else 0
            remaining = max(0, limit - current)
            return current, remaining
        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
            return 0, limit


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting on API endpoints."""
    
    def __init__(self, app):
        """Initialize rate limit middleware.
        
        Args:
            app: FastAPI application instance
        """
        super().__init__(app)
        self.limiter = RateLimiter()
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header for proxied requests
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _is_upload_endpoint(self, path: str) -> bool:
        """Check if the endpoint is an upload endpoint.
        
        Args:
            path: Request path
            
        Returns:
            True if upload endpoint, False otherwise
        """
        upload_patterns = ["/upload", "/reports/upload", "/api/v1/reports/upload"]
        return any(pattern in path for pattern in upload_patterns)
    
    async def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from JWT token if present.
        
        Args:
            request: FastAPI request object
            
        Returns:
            User ID if authenticated, None otherwise
        """
        try:
            # Check for Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            # Extract token
            token = auth_header.split(" ")[1]
            
            # Decode token to get user ID
            from app.core.security import decode_access_token
            payload = decode_access_token(token)
            return payload.get("sub")
            
        except Exception as e:
            logger.debug(f"Failed to extract user ID from token: {e}")
            return None
    
    async def _get_user_role(self, user_id: str) -> Optional[str]:
        """Get user role from database.
        
        Args:
            user_id: User ID
            
        Returns:
            User role if found, None otherwise
        """
        try:
            from app.core.database import AsyncSessionLocal
            from app.modules.auth.models import User
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                return user.role if user else None
                
        except Exception as e:
            logger.error(f"Error fetching user role: {e}")
            return None
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and enforce rate limiting.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
            
        Returns:
            HTTP response or 429 if rate limited
        """
        # Skip rate limiting for health check and docs endpoints
        if request.url.path in ["/", "/health", "/api/v1/health", "/api/v1/docs", "/api/v1/redoc", "/api/v1/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Try to get user ID from token
        user_id = await self._get_user_id(request)
        
        # Determine rate limit based on authentication and endpoint
        if self._is_upload_endpoint(request.url.path):
            # Upload endpoints: 10 requests per hour per user
            if user_id:
                key = f"rate_limit:upload:user:{user_id}"
                limit = settings.rate_limit_upload_per_hour
                window = 3600  # 1 hour
            else:
                # TEMPORARILY DISABLED FOR TESTING: Allow anonymous uploads
                # Use IP-based rate limiting for anonymous users
                client_ip = self._get_client_ip(request)
                key = f"rate_limit:upload:ip:{client_ip}"
                limit = settings.rate_limit_upload_per_hour
                window = 3600  # 1 hour
                logger.warning(f"Anonymous upload from IP {client_ip} - auth temporarily disabled for testing")
        elif user_id:
            # Authenticated users: Check if admin for bypass
            user_role = await self._get_user_role(user_id)
            
            if user_role == "admin" and settings.rate_limit_bypass_admin:
                # Admin bypass - skip rate limiting
                logger.debug(f"Admin user {user_id} bypassing rate limit")
                response = await call_next(request)
                return response
            
            # Authenticated users: 1000 requests per minute
            key = f"rate_limit:user:{user_id}:{request.url.path}"
            limit = settings.rate_limit_authenticated_per_minute
            window = 60  # 1 minute
        else:
            # Anonymous users: 100 requests per minute per IP
            key = f"rate_limit:ip:{client_ip}:{request.url.path}"
            limit = settings.rate_limit_anonymous_per_minute
            window = 60  # 1 minute
        
        # Check rate limit
        is_limited, current, remaining = await self.limiter.is_rate_limited(
            key, limit, window
        )
        
        if is_limited:
            logger.warning(
                f"Rate limit exceeded",
                extra={
                    "key": key,
                    "limit": limit,
                    "current": current,
                    "ip": client_ip,
                    "user_id": user_id,
                    "path": request.url.path,
                }
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate Limit Exceeded",
                    "message": f"Too many requests. Limit: {limit} requests per {window} seconds",
                    "limit": limit,
                    "remaining": 0,
                    "retry_after": window,
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(window),
                    "Retry-After": str(window),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(window)
        
        return response
