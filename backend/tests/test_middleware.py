"""Unit tests for middleware components including rate limiting, validation, and security headers."""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.middleware import (
    SecurityHeadersMiddleware,
    setup_middleware,
)
from app.core.validators import (
    RequestSizeLimitMiddleware,
    ContentTypeValidationMiddleware,
    RequestValidationMiddleware,
    validate_json_payload,
    validate_field_types,
)
from app.core.rate_limiter import RateLimiter, RateLimitMiddleware


# Test fixtures
@pytest.fixture
def app():
    """Create a test FastAPI application."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.post("/test-post")
    async def test_post_endpoint(data: dict):
        return {"received": data}
    
    @app.post("/api/v1/reports/upload")
    async def upload_endpoint():
        return {"uploaded": True}
    
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


class TestSecurityHeadersMiddleware:
    """Test security headers middleware."""
    
    def test_security_headers_added(self, app, client):
        """Test that security headers are added to responses."""
        app.add_middleware(SecurityHeadersMiddleware)
        
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
        assert response.headers["Content-Security-Policy"] == "default-src 'self'"
    
    def test_security_headers_on_all_endpoints(self, app, client):
        """Test that security headers are added to all endpoints."""
        app.add_middleware(SecurityHeadersMiddleware)
        
        # Test GET endpoint
        response = client.get("/test")
        assert "X-Content-Type-Options" in response.headers
        
        # Test POST endpoint
        response = client.post("/test-post", json={"key": "value"})
        assert "X-Content-Type-Options" in response.headers


class TestRequestSizeLimitMiddleware:
    """Test request size limit middleware."""
    
    def test_request_within_size_limit(self, app, client):
        """Test that requests within size limit are allowed."""
        app.add_middleware(RequestSizeLimitMiddleware, max_size=1024 * 1024)  # 1MB
        
        response = client.post(
            "/test-post",
            json={"data": "x" * 1000},  # Small payload
            headers={"Content-Length": "1000"}
        )
        
        assert response.status_code == 200
    
    def test_request_exceeds_size_limit(self, app, client):
        """Test that requests exceeding size limit are rejected."""
        app.add_middleware(RequestSizeLimitMiddleware, max_size=100)  # 100 bytes
        
        response = client.post(
            "/test-post",
            json={"data": "x" * 1000},
            headers={"Content-Length": "1000"}
        )
        
        assert response.status_code == 413
        assert "Request Too Large" in response.json()["error"]
    
    def test_get_requests_skip_size_check(self, app, client):
        """Test that GET requests skip size validation."""
        app.add_middleware(RequestSizeLimitMiddleware, max_size=100)
        
        response = client.get("/test")
        
        assert response.status_code == 200
    
    def test_request_without_content_length(self, app, client):
        """Test that requests without Content-Length header are allowed."""
        app.add_middleware(RequestSizeLimitMiddleware, max_size=100)
        
        # POST without Content-Length should pass (will be checked by FastAPI)
        response = client.post("/test-post", json={"key": "value"})
        
        # Should either succeed or fail at FastAPI level, not middleware
        assert response.status_code in [200, 422]


class TestContentTypeValidationMiddleware:
    """Test content type validation middleware."""
    
    def test_valid_json_content_type(self, app, client):
        """Test that valid JSON content type is accepted."""
        app.add_middleware(ContentTypeValidationMiddleware)
        
        response = client.post(
            "/test-post",
            json={"key": "value"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
    
    def test_valid_form_data_content_type(self, app, client):
        """Test that form data content type is accepted."""
        app.add_middleware(ContentTypeValidationMiddleware)
        
        response = client.post(
            "/test-post",
            data={"key": "value"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code in [200, 422]  # May fail at endpoint level
    
    def test_invalid_content_type(self, app, client):
        """Test that invalid content type is rejected."""
        app.add_middleware(ContentTypeValidationMiddleware, strict=True)
        
        response = client.post(
            "/test-post",
            data="invalid data",
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code == 415
        assert "Unsupported Media Type" in response.json()["error"]
    
    def test_get_requests_skip_validation(self, app, client):
        """Test that GET requests skip content type validation."""
        app.add_middleware(ContentTypeValidationMiddleware, strict=True)
        
        response = client.get("/test")
        
        assert response.status_code == 200
    
    def test_missing_content_type_non_strict(self, app, client):
        """Test that missing Content-Type is allowed in non-strict mode."""
        app.add_middleware(ContentTypeValidationMiddleware, strict=False)
        
        response = client.post("/test-post", json={"key": "value"})
        
        # Should succeed (TestClient adds Content-Type automatically)
        assert response.status_code == 200


class TestRequestValidationMiddleware:
    """Test request validation middleware."""
    
    def test_valid_http_methods(self, app, client):
        """Test that valid HTTP methods are allowed."""
        app.add_middleware(RequestValidationMiddleware)
        
        # Test GET
        response = client.get("/test")
        assert response.status_code == 200
        
        # Test POST
        response = client.post("/test-post", json={"key": "value"})
        assert response.status_code == 200
    
    def test_health_endpoints_skip_validation(self, app, client):
        """Test that health endpoints skip validation."""
        app.add_middleware(RequestValidationMiddleware)
        
        # Add health endpoint
        @app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        response = client.get("/health")
        assert response.status_code == 200


class TestValidationHelpers:
    """Test validation helper functions."""
    
    def test_validate_json_payload_success(self):
        """Test successful JSON payload validation."""
        payload = {"name": "test", "email": "test@example.com"}
        required_fields = ["name", "email"]
        
        result = validate_json_payload(payload, required_fields)
        
        assert result is None
    
    def test_validate_json_payload_missing_fields(self):
        """Test JSON payload validation with missing fields."""
        payload = {"name": "test"}
        required_fields = ["name", "email", "password"]
        
        result = validate_json_payload(payload, required_fields)
        
        assert result is not None
        assert "email" in result
        assert "password" in result
    
    def test_validate_field_types_success(self):
        """Test successful field type validation."""
        payload = {"name": "test", "age": 25, "active": True}
        field_types = {"name": str, "age": int, "active": bool}
        
        result = validate_field_types(payload, field_types)
        
        assert result is None
    
    def test_validate_field_types_incorrect_type(self):
        """Test field type validation with incorrect types."""
        payload = {"name": "test", "age": "twenty-five"}
        field_types = {"name": str, "age": int}
        
        result = validate_field_types(payload, field_types)
        
        assert result is not None
        assert "age" in result
        assert "int" in result


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_within_limit(self):
        """Test that requests within rate limit are allowed."""
        limiter = RateLimiter()
        
        with patch.object(limiter, '_get_client') as mock_client:
            # Mock Redis client
            redis_mock = AsyncMock()
            redis_mock.incr.return_value = 1
            redis_mock.expire.return_value = True
            mock_client.return_value = redis_mock
            
            is_limited, current, remaining = await limiter.is_rate_limited(
                "test_key", limit=100, window=60
            )
            
            assert is_limited is False
            assert current == 1
            assert remaining == 99
    
    @pytest.mark.asyncio
    async def test_rate_limiter_exceeds_limit(self):
        """Test that requests exceeding rate limit are blocked."""
        limiter = RateLimiter()
        
        with patch.object(limiter, '_get_client') as mock_client:
            # Mock Redis client
            redis_mock = AsyncMock()
            redis_mock.incr.return_value = 101  # Exceeds limit of 100
            mock_client.return_value = redis_mock
            
            is_limited, current, remaining = await limiter.is_rate_limited(
                "test_key", limit=100, window=60
            )
            
            assert is_limited is True
            assert current == 101
            assert remaining == 0
    
    @pytest.mark.asyncio
    async def test_rate_limiter_redis_failure(self):
        """Test that rate limiter fails open on Redis errors."""
        limiter = RateLimiter()
        
        with patch.object(limiter, '_get_client') as mock_client:
            # Mock Redis client to raise exception
            mock_client.side_effect = Exception("Redis connection failed")
            
            is_limited, current, remaining = await limiter.is_rate_limited(
                "test_key", limit=100, window=60
            )
            
            # Should fail open (allow request)
            assert is_limited is False
            assert current == 0
            assert remaining == 100


class TestRateLimitMiddleware:
    """Test rate limit middleware."""
    
    @pytest.mark.asyncio
    async def test_health_endpoints_skip_rate_limiting(self, app, client):
        """Test that health endpoints skip rate limiting."""
        app.add_middleware(RateLimitMiddleware)
        
        # Add health endpoint
        @app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response.headers
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers_added(self, app, client):
        """Test that rate limit headers are added to responses."""
        app.add_middleware(RateLimitMiddleware)
        
        with patch('app.core.rate_limiter.RateLimiter.is_rate_limited') as mock_limit:
            mock_limit.return_value = (False, 1, 99)  # Not limited
            
            response = client.get("/test")
            
            assert response.status_code == 200
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_response(self, app, client):
        """Test that 429 response is returned when rate limit exceeded."""
        app.add_middleware(RateLimitMiddleware)
        
        with patch('app.core.rate_limiter.RateLimiter.is_rate_limited') as mock_limit:
            mock_limit.return_value = (True, 101, 0)  # Limited
            
            response = client.get("/test")
            
            assert response.status_code == 429
            assert "Rate Limit Exceeded" in response.json()["error"]
            assert "Retry-After" in response.headers
    
    @pytest.mark.asyncio
    async def test_upload_endpoint_requires_auth(self, app, client):
        """Test that upload endpoints require authentication."""
        app.add_middleware(RateLimitMiddleware)
        
        # Request without auth token
        response = client.post("/api/v1/reports/upload")
        
        assert response.status_code == 401
        assert "Authentication Required" in response.json()["error"]


class TestMiddlewareIntegration:
    """Test middleware integration and setup."""
    
    def test_setup_middleware_registers_all(self):
        """Test that setup_middleware registers all middleware components."""
        app = FastAPI()
        
        # Setup all middleware
        setup_middleware(app)
        
        # Check that middleware is registered (by checking user_middleware list)
        middleware_classes = [m.cls for m in app.user_middleware]
        
        # Should include our custom middleware
        assert SecurityHeadersMiddleware in middleware_classes
        assert RequestSizeLimitMiddleware in middleware_classes
        assert RateLimitMiddleware in middleware_classes
    
    def test_middleware_execution_order(self, app, client):
        """Test that middleware executes in correct order."""
        # Add middleware in setup order
        setup_middleware(app)
        
        response = client.get("/test")
        
        # All middleware should have executed
        assert response.status_code == 200
        assert "X-Content-Type-Options" in response.headers  # Security headers
        assert "X-Correlation-ID" in response.headers  # Request logging
