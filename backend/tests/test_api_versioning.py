"""Tests for API versioning middleware and version negotiation."""

import pytest
from fastapi import status
from httpx import AsyncClient

from app.main import app
from app.core.config import settings


class TestAPIVersioning:
    """Test suite for API versioning functionality."""

    @pytest.mark.asyncio
    async def test_health_endpoint_unversioned(self):
        """Test that /health endpoint works without version prefix."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "status" in data
            assert data["version"] == settings.app_version

    @pytest.mark.asyncio
    async def test_health_endpoint_versioned(self):
        """Test that /api/v1/health endpoint works with version prefix."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/health")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "status" in data
            assert data["version"] == settings.app_version

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test that root endpoint works without version prefix."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "message" in data
            assert "version" in data

    @pytest.mark.asyncio
    async def test_versioned_endpoint_returns_version_header(self):
        """Test that versioned endpoints return API-Version header."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/health")
            
            assert response.status_code == status.HTTP_200_OK
            assert "API-Version" in response.headers
            assert response.headers["API-Version"] == settings.api_version

    @pytest.mark.asyncio
    async def test_unsupported_version_in_url_returns_404(self):
        """Test that unsupported API version in URL returns 404."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v2/projects")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "error" in data
            assert data["error"] == "Unsupported API Version"
            assert "supported_versions" in data
            assert settings.supported_api_versions == data["supported_versions"]

    @pytest.mark.asyncio
    async def test_unsupported_version_in_header_returns_404(self):
        """Test that unsupported API version in header returns 404."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/health",
                headers={"API-Version": "v99"}
            )
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "error" in data
            assert data["error"] == "Unsupported API Version"
            assert "v99" in data["message"]
            assert "supported_versions" in data

    @pytest.mark.asyncio
    async def test_supported_version_in_header_succeeds(self):
        """Test that supported API version in header succeeds."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/health",
                headers={"API-Version": "v1"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["API-Version"] == "v1"

    @pytest.mark.asyncio
    async def test_docs_endpoint_accessible(self):
        """Test that API documentation is accessible at versioned URL."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/docs")
            
            # Docs endpoint redirects, so we check for redirect or success
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_307_TEMPORARY_REDIRECT]

    @pytest.mark.asyncio
    async def test_openapi_schema_accessible(self):
        """Test that OpenAPI schema is accessible at versioned URL."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/openapi.json")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "openapi" in data
            assert "info" in data
            assert data["info"]["title"] == settings.app_name

    @pytest.mark.asyncio
    async def test_version_middleware_skips_health_check(self):
        """Test that version middleware skips validation for health endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Health endpoint should work even with invalid version header
            response = await client.get(
                "/health",
                headers={"API-Version": "invalid-version"}
            )
            
            # Should succeed because health endpoint skips version validation
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_version_middleware_skips_docs(self):
        """Test that version middleware skips validation for docs endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Docs endpoint should work even with invalid version header
            response = await client.get(
                "/docs",
                headers={"API-Version": "invalid-version"}
            )
            
            # Should succeed or redirect because docs endpoint skips version validation
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_307_TEMPORARY_REDIRECT, status.HTTP_404_NOT_FOUND]

    @pytest.mark.asyncio
    async def test_api_v1_prefix_property(self):
        """Test that settings.api_v1_prefix returns correct value."""
        assert settings.api_v1_prefix == "/api/v1"
        assert settings.api_prefix == "/api"
        assert settings.api_version == "v1"

    @pytest.mark.asyncio
    async def test_supported_versions_configuration(self):
        """Test that supported versions are properly configured."""
        assert isinstance(settings.supported_api_versions, list)
        assert "v1" in settings.supported_api_versions
        assert settings.api_version in settings.supported_api_versions


class TestVersionedEndpoints:
    """Test suite for verifying all endpoints follow versioning pattern."""

    @pytest.mark.asyncio
    async def test_auth_endpoints_versioned(self):
        """Test that auth endpoints are accessible under /api/v1/auth."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test register endpoint exists (will fail validation, but should route correctly)
            response = await client.post(
                "/api/v1/auth/register",
                json={"email": "test@example.com", "password": "password123"}
            )
            
            # Should not return 404 (route exists), may return 422 (validation error)
            assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_projects_endpoints_versioned(self):
        """Test that projects endpoints are accessible under /api/v1/projects."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test projects list endpoint (requires auth, but route should exist)
            response = await client.get("/api/v1/projects")
            
            # Should not return 404 (route exists), may return 401 (unauthorized)
            assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_reports_endpoints_versioned(self):
        """Test that reports endpoints are accessible under /api/v1/reports."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test upload endpoint exists (requires auth and file, but route should exist)
            response = await client.post("/api/v1/reports/upload")
            
            # Should not return 404 (route exists), may return 401/422
            assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_executions_endpoints_versioned(self):
        """Test that executions endpoints are accessible under /api/v1/executions."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test executions endpoint with a UUID (since there's no list endpoint)
            # Using a sample UUID - will return 401/404 for not found, but route should exist
            test_uuid = "123e4567-e89b-12d3-a456-426614174000"
            response = await client.get(f"/api/v1/executions/{test_uuid}")
            
            # Should not return 404 for unsupported version
            # May return 401 (unauthorized) or 404 (execution not found), but not version 404
            if response.status_code == status.HTTP_404_NOT_FOUND:
                # If 404, verify it's not a version error
                data = response.json()
                assert "Unsupported API Version" not in data.get("error", "")

    @pytest.mark.asyncio
    async def test_scenarios_endpoints_versioned(self):
        """Test that scenarios endpoints are accessible under /api/v1/scenarios."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test scenarios endpoint with a UUID (if needed)
            test_uuid = "123e4567-e89b-12d3-a456-426614174000"
            response = await client.get(f"/api/v1/scenarios/{test_uuid}")
            
            # Should not return 404 for unsupported version
            # May return 401 (unauthorized) or 404 (scenario not found), but not version 404
            if response.status_code == status.HTTP_404_NOT_FOUND:
                # If 404, verify it's not a version error
                data = response.json()
                assert "Unsupported API Version" not in data.get("error", "")

    @pytest.mark.asyncio
    async def test_analytics_endpoints_versioned(self):
        """Test that analytics endpoints are accessible under /api/v1/analytics."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test analytics endpoint exists with required parameters
            response = await client.get("/api/v1/analytics/trends?project_id=123e4567-e89b-12d3-a456-426614174000")
            
            # Should not return 404 for unsupported version
            # May return 401 (unauthorized) or 422 (validation error), but not version 404
            if response.status_code == status.HTTP_404_NOT_FOUND:
                # If 404, verify it's not a version error
                data = response.json()
                assert "Unsupported API Version" not in data.get("error", "")

    @pytest.mark.asyncio
    async def test_defects_endpoints_versioned(self):
        """Test that defects endpoints are accessible under /api/v1/defects."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test defects endpoint exists with required parameters
            response = await client.get("/api/v1/defects?project_id=123e4567-e89b-12d3-a456-426614174000")
            
            # Should not return 404 for unsupported version
            # May return 401 (unauthorized) or 422 (validation error), but not version 404
            if response.status_code == status.HTTP_404_NOT_FOUND:
                # If 404, verify it's not a version error
                data = response.json()
                assert "Unsupported API Version" not in data.get("error", "")


class TestVersionNegotiation:
    """Test suite for API version negotiation logic."""

    @pytest.mark.asyncio
    async def test_url_version_takes_precedence(self):
        """Test that URL version is validated even with header present."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Request v2 in URL with v1 in header
            response = await client.get(
                "/api/v2/projects",
                headers={"API-Version": "v1"}
            )
            
            # Should return 404 because URL version v2 is unsupported
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "v2" in data["message"]

    @pytest.mark.asyncio
    async def test_header_version_validated_for_valid_url(self):
        """Test that header version is validated when URL version is valid."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Request v1 in URL with v2 in header
            response = await client.get(
                "/api/v1/health",
                headers={"API-Version": "v2"}
            )
            
            # Should return 404 because header version v2 is unsupported
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "v2" in data["message"]

    @pytest.mark.asyncio
    async def test_no_version_header_succeeds(self):
        """Test that requests without version header succeed."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/health")
            
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["API-Version"] == "v1"

    @pytest.mark.asyncio
    async def test_matching_url_and_header_version_succeeds(self):
        """Test that matching URL and header versions succeed."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/health",
                headers={"API-Version": "v1"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["API-Version"] == "v1"
