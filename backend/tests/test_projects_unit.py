"""Unit tests for optimized project repository methods."""
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.projects.repository import ProjectRepository
from app.projects.models import Project, Module
from app.modules.reports.models import Report


class TestProjectRepositoryOptimization:
    """Unit tests for optimized project repository methods."""
    
    @pytest.mark.asyncio
    async def test_get_all_with_metrics_returns_correct_structure(self):
        """Test that get_all_with_metrics returns correct data structure."""
        # Mock database session
        db = AsyncMock()
        
        # Create mock project
        project = MagicMock(spec=Project)
        project.id = str(uuid.uuid4())
        project.name = "Test Project"
        project.description = "Test Description"
        project.owner = "test@example.com"
        project.is_active = True
        project.created_at = datetime.utcnow()
        
        # Mock query result
        mock_row = (
            project,  # Project
            1,        # modules_count
            100,      # total_tests
            85,       # passed_tests
            10,       # failed_tests
            datetime.utcnow()  # last_run
        )
        
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        
        db.execute = AsyncMock(return_value=mock_result)
        
        # Test the repository method
        repository = ProjectRepository(db)
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
    async def test_get_all_with_metrics_aggregates_multiple_reports(self):
        """Test that metrics are correctly aggregated across multiple reports."""
        # Mock database session
        db = AsyncMock()
        
        # Create mock project
        project = MagicMock(spec=Project)
        project.id = str(uuid.uuid4())
        project.name = "Multi Report Project"
        project.owner = "test@example.com"
        project.is_active = True
        
        # Mock query result with aggregated data from multiple reports
        mock_row = (
            project,  # Project
            1,        # modules_count
            150,      # total_tests (100 + 50)
            125,      # passed_tests (80 + 45)
            18,       # failed_tests (15 + 3)
            datetime.utcnow()  # last_run
        )
        
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        
        db.execute = AsyncMock(return_value=mock_result)
        
        # Test the repository method
        repository = ProjectRepository(db)
        result = await repository.get_all_with_metrics(page=1, size=10)
        
        # Assertions
        assert len(result) == 1
        project_data = result[0]
        
        # Total tests should be sum of all reports
        assert project_data["total_tests"] == 150
        # Pass rate should be 125 / 150 * 100 = 83.33
        assert abs(project_data["pass_rate"] - 83.33) < 0.01
    
    @pytest.mark.asyncio
    async def test_get_all_with_metrics_handles_no_reports(self):
        """Test that projects without reports are handled correctly."""
        # Mock database session
        db = AsyncMock()
        
        # Create mock project without reports
        project = MagicMock(spec=Project)
        project.id = str(uuid.uuid4())
        project.name = "Empty Project"
        project.owner = "test@example.com"
        project.is_active = True
        
        # Mock query result with no reports (all aggregates are None/0)
        mock_row = (
            project,  # Project
            0,        # modules_count
            None,     # total_tests (NULL from SUM)
            None,     # passed_tests (NULL from SUM)
            None,     # failed_tests (NULL from SUM)
            None      # last_run (NULL from MAX)
        )
        
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        
        db.execute = AsyncMock(return_value=mock_result)
        
        # Test the repository method
        repository = ProjectRepository(db)
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
    async def test_get_all_with_metrics_status_determination(self):
        """Test that last_status is correctly determined based on test results."""
        # Mock database session
        db = AsyncMock()
        
        # Test all passed
        project_passed = MagicMock(spec=Project)
        project_passed.name = "All Passed Project"
        
        mock_row_passed = (
            project_passed,
            1,        # modules_count
            100,      # total_tests
            100,      # passed_tests
            0,        # failed_tests (0 = all passed)
            datetime.utcnow()
        )
        
        # Test all failed
        project_failed = MagicMock(spec=Project)
        project_failed.name = "All Failed Project"
        
        mock_row_failed = (
            project_failed,
            1,        # modules_count
            100,      # total_tests
            0,        # passed_tests (0 = all failed)
            100,      # failed_tests
            datetime.utcnow()
        )
        
        # Test mixed
        project_mixed = MagicMock(spec=Project)
        project_mixed.name = "Mixed Project"
        
        mock_row_mixed = (
            project_mixed,
            1,        # modules_count
            100,      # total_tests
            85,       # passed_tests
            10,       # failed_tests (both > 0 = mixed)
            datetime.utcnow()
        )
        
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row_passed, mock_row_failed, mock_row_mixed]
        
        db.execute = AsyncMock(return_value=mock_result)
        
        # Test the repository method
        repository = ProjectRepository(db)
        result = await repository.get_all_with_metrics(page=1, size=10)
        
        # Find projects by name
        passed_project = next(p for p in result if p["project"].name == "All Passed Project")
        failed_project = next(p for p in result if p["project"].name == "All Failed Project")
        mixed_project = next(p for p in result if p["project"].name == "Mixed Project")
        
        assert passed_project["last_status"] == "passed"
        assert failed_project["last_status"] == "failed"
        assert mixed_project["last_status"] == "mixed"
    
    @pytest.mark.asyncio
    async def test_get_all_with_metrics_uses_single_query(self):
        """Test that get_all_with_metrics uses a single optimized query."""
        # Mock database session
        db = AsyncMock()
        
        mock_result = MagicMock()
        mock_result.all.return_value = []
        
        db.execute = AsyncMock(return_value=mock_result)
        
        # Test the repository method
        repository = ProjectRepository(db)
        await repository.get_all_with_metrics(page=1, size=100)
        
        # Verify execute was called exactly once (single query)
        assert db.execute.call_count == 1
        
        # Verify the query includes JOINs and aggregations
        call_args = db.execute.call_args[0][0]
        query_str = str(call_args)
        
        # Check for key components of optimized query
        assert "count" in query_str.lower() or "COUNT" in query_str
        assert "sum" in query_str.lower() or "SUM" in query_str
        assert "max" in query_str.lower() or "MAX" in query_str
