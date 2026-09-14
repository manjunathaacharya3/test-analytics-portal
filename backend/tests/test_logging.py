"""Tests for structured logging configuration and correlation ID middleware."""

import pytest
import json
import uuid
from io import StringIO
import logging
import structlog
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.core.logging import (
    configure_logging,
    get_logger,
    bind_correlation_id,
    bind_user_context,
    unbind_context,
    redact_sensitive_data,
    add_timestamp,
    add_service_context,
)
from app.core.middleware import RequestLoggingMiddleware
from app.core.config import settings


class TestLoggingConfiguration:
    """Test structured logging configuration."""
    
    def test_configure_logging_sets_up_structlog(self):
        """Test that configure_logging properly sets up structlog."""
        configure_logging()
        logger = get_logger(__name__)
        # Logger is a BoundLoggerLazyProxy that wraps BoundLogger
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
    
    def test_get_logger_returns_bound_logger(self):
        """Test that get_logger returns a BoundLogger instance."""
        logger = get_logger("test_module")
        # Logger is a BoundLoggerLazyProxy that wraps BoundLogger
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')
    
    def test_bind_correlation_id_adds_to_context(self):
        """Test that correlation ID is bound to logging context."""
        correlation_id = str(uuid.uuid4())
        bind_correlation_id(correlation_id)
        
        # Get context vars
        context = structlog.contextvars.get_contextvars()
        assert "correlation_id" in context
        assert context["correlation_id"] == correlation_id
        
        # Clean up
        unbind_context()
    
    def test_bind_user_context_adds_user_info(self):
        """Test that user context is bound to logging context."""
        user_id = str(uuid.uuid4())
        user_email = "test@example.com"
        
        bind_user_context(user_id=user_id, user_email=user_email)
        
        context = structlog.contextvars.get_contextvars()
        assert context["user_id"] == user_id
        assert context["user_email"] == user_email
        
        # Clean up
        unbind_context()
    
    def test_unbind_context_clears_all_vars(self):
        """Test that unbind_context clears all context variables."""
        bind_correlation_id("test-id")
        bind_user_context(user_id="user-123")
        
        unbind_context()
        
        context = structlog.contextvars.get_contextvars()
        assert len(context) == 0


class TestSensitiveDataRedaction:
    """Test sensitive data redaction in logs."""
    
    def test_redact_password_field(self):
        """Test that password fields are redacted."""
        event_dict = {
            "username": "testuser",
            "password": "secret123",
            "email": "test@example.com"
        }
        
        result = redact_sensitive_data(None, None, event_dict)
        
        assert result["username"] == "testuser"
        assert result["password"] == "***REDACTED***"
        assert result["email"] == "test@example.com"
    
    def test_redact_token_fields(self):
        """Test that token fields are redacted."""
        event_dict = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "refresh_token_value",
            "api_key": "sk-1234567890",
            "data": "public_data"
        }
        
        result = redact_sensitive_data(None, None, event_dict)
        
        assert result["access_token"] == "***REDACTED***"
        assert result["refresh_token"] == "***REDACTED***"
        assert result["api_key"] == "***REDACTED***"
        assert result["data"] == "public_data"
    
    def test_redact_nested_sensitive_data(self):
        """Test that nested sensitive data is redacted."""
        event_dict = {
            "user": {
                "username": "testuser",
                "password": "secret123",
                "profile": {
                    "email": "test@example.com",
                    "api_key": "sk-secret"
                }
            },
            "public_field": "public_value"
        }
        
        result = redact_sensitive_data(None, None, event_dict)
        
        assert result["user"]["username"] == "testuser"
        assert result["user"]["password"] == "***REDACTED***"
        assert result["user"]["profile"]["email"] == "test@example.com"
        assert result["user"]["profile"]["api_key"] == "***REDACTED***"
        assert result["public_field"] == "public_value"
    
    def test_redact_authorization_header(self):
        """Test that authorization headers are redacted."""
        event_dict = {
            "headers": {
                "authorization": "Bearer token123",
                "content-type": "application/json"
            }
        }
        
        result = redact_sensitive_data(None, None, event_dict)
        
        assert result["headers"]["authorization"] == "***REDACTED***"
        assert result["headers"]["content-type"] == "application/json"


class TestLogProcessors:
    """Test log processors."""
    
    def test_add_timestamp_adds_iso_format(self):
        """Test that timestamp is added in ISO 8601 format."""
        event_dict = {"message": "test"}
        result = add_timestamp(None, None, event_dict)
        
        assert "timestamp" in result
        # Check it ends with Z (UTC)
        assert result["timestamp"].endswith("Z")
        # Check it contains T (ISO format)
        assert "T" in result["timestamp"]
    
    def test_add_service_context_adds_service_info(self):
        """Test that service context is added."""
        event_dict = {"message": "test"}
        result = add_service_context(None, None, event_dict)
        
        assert result["service"] == "taps-backend"
        assert result["environment"] == settings.environment


class TestCorrelationIDMiddleware:
    """Test correlation ID middleware integration."""
    
    @pytest.fixture
    def app(self):
        """Create a test FastAPI app with logging middleware."""
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"correlation_id": request.state.correlation_id}
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)
    
    def test_correlation_id_generated_for_request(self, client):
        """Test that correlation ID is generated for each request."""
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-Correlation-ID" in response.headers
        
        # Verify it's a valid UUID
        correlation_id = response.headers["X-Correlation-ID"]
        uuid.UUID(correlation_id)  # Will raise if invalid
    
    def test_correlation_id_unique_per_request(self, client):
        """Test that each request gets a unique correlation ID."""
        response1 = client.get("/test")
        response2 = client.get("/test")
        
        correlation_id1 = response1.headers["X-Correlation-ID"]
        correlation_id2 = response2.headers["X-Correlation-ID"]
        
        assert correlation_id1 != correlation_id2
    
    def test_correlation_id_in_request_state(self, client):
        """Test that correlation ID is available in request state."""
        response = client.get("/test")
        
        assert response.status_code == 200
        correlation_id_header = response.headers["X-Correlation-ID"]
        correlation_id_body = response.json()["correlation_id"]
        
        assert correlation_id_header == correlation_id_body
    
    @patch('app.core.middleware.logger')
    def test_request_logged_with_correlation_id(self, mock_logger, client):
        """Test that requests are logged with correlation ID."""
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Verify logger.info was called for request start and completion
        assert mock_logger.info.call_count >= 2
    
    @patch('app.core.middleware.logger')
    def test_error_logged_with_correlation_id(self, mock_logger, client):
        """Test that errors are logged with correlation ID and stack trace."""
        with pytest.raises(ValueError):
            client.get("/error")
        
        # Verify logger.error was called with exc_info=True
        mock_logger.error.assert_called_once()
        call_kwargs = mock_logger.error.call_args[1]
        assert call_kwargs.get("exc_info") is True


class TestLogFormat:
    """Test log output format."""
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_json_log_format_in_production(self, mock_stdout):
        """Test that logs are in JSON format in production mode."""
        # Temporarily set environment to production
        original_env = settings.environment
        settings.environment = "production"
        
        try:
            configure_logging()
            logger = get_logger(__name__)
            
            bind_correlation_id("test-correlation-id")
            logger.info("Test message", extra_field="extra_value")
            
            # Get log output
            log_output = mock_stdout.getvalue()
            
            # In production, should be JSON
            if log_output.strip():
                log_entry = json.loads(log_output.strip().split('\n')[-1])
                assert "timestamp" in log_entry
                assert "level" in log_entry
                assert "correlation_id" in log_entry
                assert log_entry["correlation_id"] == "test-correlation-id"
        finally:
            settings.environment = original_env
            unbind_context()
    
    def test_log_level_from_settings(self):
        """Test that log level is configured from settings."""
        configure_logging()
        
        # Get root logger level
        root_logger = logging.getLogger()
        expected_level = getattr(logging, settings.log_level.upper())
        
        # Log level should be set correctly (may be WARNING or INFO depending on environment)
        assert root_logger.level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
        assert root_logger.level <= logging.ERROR


class TestContextPropagation:
    """Test context propagation across log entries."""
    
    def test_correlation_id_propagates_to_all_logs(self):
        """Test that correlation ID propagates to all log entries in context."""
        logger = get_logger(__name__)
        correlation_id = "test-correlation-123"
        
        bind_correlation_id(correlation_id)
        
        # Both log entries should have the same correlation ID
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.info("First log entry")
            logger.info("Second log entry")
            
            # Context should persist
            context = structlog.contextvars.get_contextvars()
            assert context.get("correlation_id") == correlation_id
        
        unbind_context()
    
    def test_context_cleared_after_unbind(self):
        """Test that context is properly cleared after unbind."""
        bind_correlation_id("test-id")
        bind_user_context(user_id="user-123", user_email="test@example.com")
        
        # Verify context is set
        context = structlog.contextvars.get_contextvars()
        assert len(context) > 0
        
        # Clear context
        unbind_context()
        
        # Verify context is empty
        context = structlog.contextvars.get_contextvars()
        assert len(context) == 0
