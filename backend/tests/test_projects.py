"""Integration tests for Projects API."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.projects.models import Project, Module
from app.modules.auth.models import User
from app.modules.reports.models import Report
from app.projects.repository import ProjectRepository


class TestProjectsAPI:
    """Test suite for Projects API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_project_success(self, client: AsyncClient, auth_headers: dict):
        """Test successful project creation."""
        project_data = {
            "name": "Test Project",
            "description": "Test Description",
            "repository_url": "https://github.com/test/repo",
            "owner": "test@example.com"
        }
        
        response = await client.post(
            "/api/v1/projects",
            json=project_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["owner"] == project_data["owner"]
        assert "id" in data
        assert data["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_create_project_unauthorized(self, client: AsyncClient):
        """Test project creation without authentication."""
        project_data = {
            "name": "Test Project",
            "owner": "test@example.com"
        }
        
        response = await client.post(
            "/api/v1/projects",
            json=project_data
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_project_validation_error(self, client: AsyncClient, auth_headers: dict):
        """Test project creation with invalid data."""
        project_data = {
            "name": "AB",  # Too short (min 3 chars)
            "owner": "test@example.com"
        }
        
        response = await client.post(
            "/api/v1/projects",
            json=project_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_list_projects(self, client: AsyncClient, auth_headers: dict, test_projects: list):
        """Test listing projects with pagination."""
        response = await client.get(
            "/api/v1/projects?page=1&size=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    @pytest.mark.asyncio
    async def test_list_projects_with_filters(self, client: AsyncClient, auth_headers: dict, test_projects: list):
        """Test listing projects with filters."""
        response = await client.get(
            "/api/v1/projects?is_active=true&owner=test@example.com",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for project in data:
            assert project["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_get_project_by_id(self, client: AsyncClient, auth_headers: dict, test_project: Project):
        """Test getting single project by ID."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id
        assert data["name"] == test_project.name
    
    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent project."""
        response = await client.get(
            "/api/v1/projects/non-existent-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_project(self, client: AsyncClient, auth_headers: dict, test_project: Project):
        """Test updating project."""
        update_data = {
            "name": "Updated Project Name",
            "description": "Updated Description"
        }
        
        response = await client.put(
            f"/api/v1/projects/{test_project.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
    
    @pytest.mark.asyncio
    async def test_soft_delete_project(self, client: AsyncClient, auth_headers: dict, test_project: Project):
        """Test soft deleting project."""
        response = await client.delete(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify project is soft deleted (is_active = False)
        get_response = await client.get(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_list_project_modules(self, client: AsyncClient, auth_headers: dict, test_project: Project):
        """Test listing modules for a project."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/modules",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_pagination(self, client: AsyncClient, auth_headers: dict, test_projects: list):
        """Test pagination works correctly."""
        # Get first page
        response1 = await client.get(
            "/api/v1/projects?page=1&size=5",
            headers=auth_headers
        )
        assert response1.status_code == 200
        page1_data = response1.json()
        assert len(page1_data) <= 5
        
        # Get second page
        response2 = await client.get(
            "/api/v1/projects?page=2&size=5",
            headers=auth_headers
        )
        assert response2.status_code == 200
        page2_data = response2.json()
        
        # Ensure different data on different pages
        if len(page1_data) > 0 and len(page2_data) > 0:
            assert page1_data[0]["id"] != page2_data[0]["id"]


class TestProjectRepositoryOptimization:
    """Unit tests for optimized project repository methods."""
    
    @pytest.mark.asyncio
    async def test_get_all_with_metrics_returns_correct_structure(self, test_db_session: AsyncSession):
        """Test that get_all_with_metrics returns correct data structure."""
        # Create test data
        project = Project(
            name="Test Project",
            description="Test Description",
            repository_url="https://github.com/test/repo",
            owner="test@example.com",
            is_active=True
        )
        test_db_session.add(project)
        await test_db_session.flush()
        
        module = Module(
            name="Test Module",
            description="Test Module Description",
            project_id=project.id,
            is_active=True
        )
        test_db_session.add(module)
        await test_db_session.flush()
        
        report = Report(
            project_id=project.id,
            module_id=module.id,
            file_name="test_report.json",
            file_size=1024,
            total_scenarios=100,
            passed_scenarios=85,
            failed_scenarios=10,
            skipped_scenarios=5,
            duration=120.5,
            uploaded_by="test@example.com"
        )
        test_db_session.add(report)
        await test_db_session.commit()
        
        # Test the repository method
        repository = ProjectRepository(test_db_session)
        result = await repository.get_all_with_metrics(page=1, size=10)
        
        # Assertions
        assert len(result) == 1
        project_data = result[0]
        
        assert "project" in project_data
        assert "modules" in project_data
        assert "total_tests" in project_data
        assert "pass_rate" in project_data
        assert "last_status" in project_data
        assert "last_run" in project_data
        
        assert project_data["modules"] == 1
        assert project_data["total_tests"] == 100
        assert project_data["pass_rate"] == 85.0
        assert project_data["last_status"] == "mixed"
    
    @pytest.mark.asyncio
    async def test_get_all_with_metrics_aggregates_multiple_reports(self, test_db_session: AsyncSession):
        """Test that metrics are correctly aggregated across multiple reports."""
        # Create test data
        project = Project(
            name="Multi Report Project",
            description="Test Description",
            repository_url="https://github.com/test/repo",
            owner="test@example.com",
            is_active=True
        )
        test_db_session.add(project)
        await test_db_session.flush()
        
        module = Module(
            name="Test Module",
            description="Test Module Description",
            project_id=project.id,
            is_active=True
        )
        test_db_session.add(module)
        await test_db_session.flush()
        
        # Create multiple reports
        report1 = Report(
            project_id=project.id,
            module_id=module.id,
            file_name="report1.json",
            file_size=1024,
            total_scenarios=100,
            passed_scenarios=80,
            failed_scenarios=15,
            skipped_scenarios=5,
            duration=120.5,
            uploaded_by="test@example.com"
        )
        report2 = Report(
            project_id=project.id,
            module_id=module.id,
            file_name="report2.json",
            file_size=2048,
            total_scenarios=50,
            passed_scenarios=45,
            failed_scenarios=3,
            skipped_scenarios=2,
            duration=60.0,
            uploaded_by="test@example.com"
        )
        test_db_session.add_all([report1, report2])
        await test_db_session.commit()
        
        # Test the repository method
        repository = ProjectRepository(test_db_session)
        result = await repository.get_all_with_metrics(page=1, size=10)
        
        # Assertions
        assert len(result) == 1
        project_data = result[0]
        
        # Total tests should be sum of all reports
        assert project_data["total_tests"] == 150  # 100 + 50
        # Pass rate should be (80 + 45) / 150 * 100 = 83.33
        assert abs(project_data["pass_rate"] - 83.33) < 0.01
    
    @pytest.mark.asyncio
    async def test_get_all_with_metrics_handles_no_reports(self, test_db_session: AsyncSession):
        """Test that projects without reports are handled correctly."""
        # Create project without reports
        project = Project(
            name="Empty Project",
            description="Test Description",
            repository_url="https://github.com/test/repo",
            owner="test@example.com",
            is_active=True
        )
        test_db_session.add(project)
        await test_db_session.commit()
        
        # Test the repository method
        repository = ProjectRepository(test_db_session)
        result = await repository.get_all_with_metrics(page=1, size=10)
        
        # Assertions
        assert len(result) == 1
        project_data = result[0]
        
        assert project_data["modules"] == 0
        assert project_data["total_tests"] == 0
        assert project_data["pass_rate"] == 0.0
        assert project_data["last_status"] is None
        assert project_data["last_run"] is None
    
    @pytest.mark.asyncio
    async def test_get_all_with_metrics_filtering(self, test_db_session: AsyncSession):
        """Test that filtering by is_active and owner works correctly."""
        # Create multiple projects
        project1 = Project(
            name="Active Project",
            description="Active",
            repository_url="https://github.com/test/repo1",
            owner="owner1@example.com",
            is_active=True
        )
        project2 = Project(
            name="Inactive Project",
            description="Inactive",
            repository_url="https://github.com/test/repo2",
            owner="owner2@example.com",
            is_active=False
        )
        test_db_session.add_all([project1, project2])
        await test_db_session.commit()
        
        # Test filtering by is_active
        repository = ProjectRepository(test_db_session)
        result = await repository.get_all_with_metrics(page=1, size=10, is_active=True)
        
        assert len(result) == 1
        assert result[0]["project"].name == "Active Project"
        
        # Test filtering by owner
        result = await repository.get_all_with_metrics(page=1, size=10, owner="owner2@example.com")
        
        assert len(result) == 1
        assert result[0]["project"].name == "Inactive Project"
    
    @pytest.mark.asyncio
    async def test_get_all_with_metrics_status_determination(self, test_db_session: AsyncSession):
        """Test that last_status is correctly determined based on test results."""
        # Test all passed
        project_passed = Project(
            name="All Passed Project",
            owner="test@example.com",
            is_active=True
        )
        test_db_session.add(project_passed)
        await test_db_session.flush()
        
        module_passed = Module(
            name="Module",
            project_id=project_passed.id,
            is_active=True
        )
        test_db_session.add(module_passed)
        await test_db_session.flush()
        
        report_passed = Report(
            project_id=project_passed.id,
            module_id=module_passed.id,
            file_name="passed.json",
            file_size=1024,
            total_scenarios=100,
            passed_scenarios=100,
            failed_scenarios=0,
            skipped_scenarios=0,
            uploaded_by="test@example.com"
        )
        test_db_session.add(report_passed)
        
        # Test all failed
        project_failed = Project(
            name="All Failed Project",
            owner="test@example.com",
            is_active=True
        )
        test_db_session.add(project_failed)
        await test_db_session.flush()
        
        module_failed = Module(
            name="Module",
            project_id=project_failed.id,
            is_active=True
        )
        test_db_session.add(module_failed)
        await test_db_session.flush()
        
        report_failed = Report(
            project_id=project_failed.id,
            module_id=module_failed.id,
            file_name="failed.json",
            file_size=1024,
            total_scenarios=100,
            passed_scenarios=0,
            failed_scenarios=100,
            skipped_scenarios=0,
            uploaded_by="test@example.com"
        )
        test_db_session.add(report_failed)
        await test_db_session.commit()
        
        # Test the repository method
        repository = ProjectRepository(test_db_session)
        result = await repository.get_all_with_metrics(page=1, size=10)
        
        # Find projects by name
        passed_project = next(p for p in result if p["project"].name == "All Passed Project")
        failed_project = next(p for p in result if p["project"].name == "All Failed Project")
        
        assert passed_project["last_status"] == "passed"
        assert failed_project["last_status"] == "failed"
