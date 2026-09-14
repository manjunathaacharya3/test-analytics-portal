"""Tests for /api/v1/health endpoint."""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint_success():
    """Test health endpoint returns 200 when all services are healthy."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        with patch("app.core.database.engine.begin") as mock_db, \
             patch("app.core.redis_client.check_redis_health", return_value=True):
            
            # Mock successful database connection
            mock_conn = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_conn
            
            response = await client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "version" in data
            assert "environment" in data
            assert "services" in data
            assert data["services"]["database"] == "connected"
            assert data["services"]["cache"] == "connected"


@pytest.mark.asyncio
async def test_health_endpoint_database_failure():
    """Test health endpoint returns unhealthy when database is down."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        with patch("app.core.database.engine.begin", side_effect=Exception("DB connection failed")), \
             patch("app.core.redis_client.check_redis_health", return_value=True):
            
            response = await client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "unhealthy"
            assert data["services"]["database"] == "disconnected"
            assert data["services"]["cache"] == "connected"


@pytest.mark.asyncio
async def test_health_endpoint_redis_failure():
    """Test health endpoint returns degraded when Redis is down."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        with patch("app.core.database.engine.begin") as mock_db, \
             patch("app.core.redis_client.check_redis_health", return_value=False):
            
            # Mock successful database connection
            mock_conn = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_conn
            
            response = await client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "degraded"
            assert data["services"]["database"] == "connected"
            assert data["services"]["cache"] == "disconnected"


@pytest.mark.asyncio
async def test_health_endpoint_all_services_down():
    """Test health endpoint when both database and Redis are down."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        with patch("app.core.database.engine.begin", side_effect=Exception("DB connection failed")), \
             patch("app.core.redis_client.check_redis_health", return_value=False):
            
            response = await client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "unhealthy"
            assert data["services"]["database"] == "disconnected"
            assert data["services"]["cache"] == "disconnected"


@pytest.mark.asyncio
async def test_health_endpoint_response_structure():
    """Test health endpoint returns correct response structure."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        with patch("app.core.database.engine.begin") as mock_db, \
             patch("app.core.redis_client.check_redis_health", return_value=True):
            
            # Mock successful database connection
            mock_conn = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_conn
            
            response = await client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify all required fields are present
            required_fields = ["status", "timestamp", "version", "environment", "services"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Verify services structure
            assert "database" in data["services"]
            assert "cache" in data["services"]
            
            # Verify timestamp format (ISO 8601)
            assert data["timestamp"].endswith("Z")
            assert "T" in data["timestamp"]
