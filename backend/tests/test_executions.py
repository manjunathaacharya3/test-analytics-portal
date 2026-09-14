"""Unit tests for execution API."""
import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.executions.repository import ExecutionRepository
from app.executions.service import ExecutionService
from app.executions.schemas import (
    ExecutionResponse,
    ExecutionListResponse,
    ScenarioResponse,
    ScenarioListResponse
)
from app.core.exceptions import NotFoundError


# Mock Report and Scenario classes to avoid SQLAlchemy model initialization issues
class MockReport:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.__dict__.update(kwargs)


class MockScenario:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.__dict__.update(kwargs)


class TestExecutionRepository:
    """Test ExecutionRepository methods."""
    
    @pytest.mark.asyncio
    async def test_get_by_id_found(self):
        """Test getting execution by ID when it exists."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        
        # Create mock report
        report_id = str(uuid.uuid4())
        mock_report = MockReport(
            id=report_id,
            project_id=str(uuid.uuid4()),
            module_id=str(uuid.uuid4()),
            file_name="test_report.json",
            file_size=1024,
            total_scenarios=10,
            passed_scenarios=8,
            failed_scenarios=2,
            skipped_scenarios=0,
            duration=120.5,
            uploaded_by="test@example.com"
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_report
        db.execute.return_value = mock_result
        
        repo = ExecutionRepository(db)
        result = await repo.get_by_id(report_id)
        
        assert result is not None
        assert result.id == report_id
        assert result.total_scenarios == 10
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """Test getting execution by ID when it doesn't exist."""
        db = AsyncMock(spec=AsyncSession)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result
        
        repo = ExecutionRepository(db)
        result = await repo.get_by_id(str(uuid.uuid4()))
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_project(self):
        """Test getting executions by project ID."""
        db = AsyncMock(spec=AsyncSession)
        
        # Create mock reports
        project_id = str(uuid.uuid4())
        mock_reports = [
            MockReport(
                id=str(uuid.uuid4()),
                project_id=project_id,
                module_id=str(uuid.uuid4()),
                file_name=f"report_{i}.json",
                file_size=1024,
                total_scenarios=10,
                passed_scenarios=8,
                failed_scenarios=2,
                skipped_scenarios=0,
                uploaded_by="test@example.com"
            )
            for i in range(3)
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_reports
        db.execute.return_value = mock_result
        
        repo = ExecutionRepository(db)
        result = await repo.get_by_project(project_id, page=1, size=20)
        
        assert len(result) == 3
        assert all(r.project_id == project_id for r in result)
    
    @pytest.mark.asyncio
    async def test_get_scenarios_by_execution(self):
        """Test getting scenarios for an execution."""
        db = AsyncMock(spec=AsyncSession)
        
        execution_id = str(uuid.uuid4())
        mock_scenarios = [
            MockScenario(
                id=str(uuid.uuid4()),
                report_id=execution_id,
                name=f"Scenario {i}",
                status="passed" if i % 2 == 0 else "failed",
                duration=1.5
            )
            for i in range(5)
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_scenarios
        db.execute.return_value = mock_result
        
        repo = ExecutionRepository(db)
        result = await repo.get_scenarios_by_execution(execution_id, page=1, size=50)
        
        assert len(result) == 5
        assert all(s.report_id == execution_id for s in result)
    
    @pytest.mark.asyncio
    async def test_count_by_project(self):
        """Test counting executions for a project."""
        db = AsyncMock(spec=AsyncSession)
        
        mock_result = MagicMock()
        mock_result.scalar.return_value = 15
        db.execute.return_value = mock_result
        
        repo = ExecutionRepository(db)
        result = await repo.count_by_project(str(uuid.uuid4()))
        
        assert result == 15


class TestExecutionService:
    """Test ExecutionService methods."""
    
    def test_calculate_pass_rate(self):
        """Test pass rate calculation."""
        report = MockReport(
            id=str(uuid.uuid4()),
            project_id=str(uuid.uuid4()),
            module_id=str(uuid.uuid4()),
            file_name="test.json",
            file_size=1024,
            total_scenarios=10,
            passed_scenarios=8,
            failed_scenarios=2,
            skipped_scenarios=0,
            uploaded_by="test@example.com"
        )
        
        pass_rate = ExecutionService._calculate_pass_rate(report)
        assert pass_rate == 80.0
    
    def test_calculate_pass_rate_zero_scenarios(self):
        """Test pass rate calculation with zero scenarios."""
        report = MockReport(
            id=str(uuid.uuid4()),
            project_id=str(uuid.uuid4()),
            module_id=str(uuid.uuid4()),
            file_name="test.json",
            file_size=1024,
            total_scenarios=0,
            passed_scenarios=0,
            failed_scenarios=0,
            skipped_scenarios=0,
            uploaded_by="test@example.com"
        )
        
        pass_rate = ExecutionService._calculate_pass_rate(report)
        assert pass_rate == 0.0
    
    def test_determine_status_passed(self):
        """Test status determination for all passed scenarios."""
        report = MockReport(
            id=str(uuid.uuid4()),
            project_id=str(uuid.uuid4()),
            module_id=str(uuid.uuid4()),
            file_name="test.json",
            file_size=1024,
            total_scenarios=10,
            passed_scenarios=10,
            failed_scenarios=0,
            skipped_scenarios=0,
            uploaded_by="test@example.com"
        )
        
        status = ExecutionService._determine_status(report)
        assert status == "passed"
    
    def test_determine_status_failed(self):
        """Test status determination for failed scenarios."""
        report = MockReport(
            id=str(uuid.uuid4()),
            project_id=str(uuid.uuid4()),
            module_id=str(uuid.uuid4()),
            file_name="test.json",
            file_size=1024,
            total_scenarios=10,
            passed_scenarios=8,
            failed_scenarios=2,
            skipped_scenarios=0,
            uploaded_by="test@example.com"
        )
        
        status = ExecutionService._determine_status(report)
        assert status == "failed"
    
    def test_determine_status_mixed(self):
        """Test status determination for mixed scenarios with skipped."""
        report = MockReport(
            id=str(uuid.uuid4()),
            project_id=str(uuid.uuid4()),
            module_id=str(uuid.uuid4()),
            file_name="test.json",
            file_size=1024,
            total_scenarios=10,
            passed_scenarios=8,
            failed_scenarios=0,
            skipped_scenarios=2,
            uploaded_by="test@example.com"
        )
        
        status = ExecutionService._determine_status(report)
        assert status == "mixed"
    
    @pytest.mark.asyncio
    async def test_get_execution_by_id_success(self):
        """Test getting execution by ID successfully."""
        db = AsyncMock(spec=AsyncSession)
        execution_id = str(uuid.uuid4())
        
        # Create mock report
        mock_report = MockReport(
            id=execution_id,
            project_id=str(uuid.uuid4()),
            module_id=str(uuid.uuid4()),
            file_name="test_report.json",
            file_size=1024,
            total_scenarios=10,
            passed_scenarios=8,
            failed_scenarios=2,
            skipped_scenarios=0,
            duration=120.5,
            uploaded_by="test@example.com"
        )
        mock_report.created_at = datetime.utcnow()
        
        # Mock repository
        with patch('app.executions.service.ExecutionRepository') as MockRepo:
            mock_repo_instance = MockRepo.return_value
            mock_repo_instance.get_by_id = AsyncMock(return_value=mock_report)
            
            # Mock cache miss
            with patch('app.executions.service.cache_service') as mock_cache:
                mock_cache.get = AsyncMock(return_value=None)
                mock_cache.set = AsyncMock(return_value=True)
                
                result = await ExecutionService.get_execution_by_id(db, execution_id, use_cache=True)
                
                assert isinstance(result, ExecutionResponse)
                assert result.id == uuid.UUID(execution_id)
                assert result.total_scenarios == 10
                assert result.pass_rate == 80.0
                assert result.status == "failed"
                
                # Verify cache was set
                mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_execution_by_id_not_found(self):
        """Test getting execution by ID when it doesn't exist."""
        db = AsyncMock(spec=AsyncSession)
        execution_id = str(uuid.uuid4())
        
        # Mock repository returning None
        with patch('app.executions.service.ExecutionRepository') as MockRepo:
            mock_repo_instance = MockRepo.return_value
            mock_repo_instance.get_by_id = AsyncMock(return_value=None)
            
            # Mock cache miss
            with patch('app.executions.service.cache_service') as mock_cache:
                mock_cache.get = AsyncMock(return_value=None)
                
                with pytest.raises(NotFoundError):
                    await ExecutionService.get_execution_by_id(db, execution_id)
    
    @pytest.mark.asyncio
    async def test_get_execution_by_id_cache_hit(self):
        """Test getting execution from cache."""
        db = AsyncMock(spec=AsyncSession)
        execution_id = str(uuid.uuid4())
        
        # Mock cached data
        cached_data = {
            "id": execution_id,
            "project_id": str(uuid.uuid4()),
            "module_id": str(uuid.uuid4()),
            "file_name": "test.json",
            "file_size": 1024,
            "total_scenarios": 10,
            "passed_scenarios": 8,
            "failed_scenarios": 2,
            "skipped_scenarios": 0,
            "duration": 120.5,
            "uploaded_by": "test@example.com",
            "created_at": datetime.utcnow().isoformat(),
            "pass_rate": 80.0,
            "status": "failed"
        }
        
        with patch('app.executions.service.cache_service') as mock_cache:
            mock_cache.get = AsyncMock(return_value=cached_data)
            
            result = await ExecutionService.get_execution_by_id(db, execution_id, use_cache=True)
            
            assert isinstance(result, ExecutionResponse)
            assert str(result.id) == execution_id
            # Repository should not be called
            db.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_executions_by_project(self):
        """Test getting executions for a project."""
        db = AsyncMock(spec=AsyncSession)
        project_id = str(uuid.uuid4())
        
        # Create mock reports
        mock_reports = [
            MockReport(
                id=str(uuid.uuid4()),
                project_id=project_id,
                module_id=str(uuid.uuid4()),
                file_name=f"report_{i}.json",
                file_size=1024,
                total_scenarios=10,
                passed_scenarios=8,
                failed_scenarios=2,
                skipped_scenarios=0,
                uploaded_by="test@example.com"
            )
            for i in range(3)
        ]
        for report in mock_reports:
            report.created_at = datetime.utcnow()
        
        with patch('app.executions.service.ExecutionRepository') as MockRepo:
            mock_repo_instance = MockRepo.return_value
            mock_repo_instance.get_by_project = AsyncMock(return_value=mock_reports)
            mock_repo_instance.count_by_project = AsyncMock(return_value=3)
            
            with patch('app.executions.service.cache_service') as mock_cache:
                mock_cache.get = AsyncMock(return_value=None)
                mock_cache.set = AsyncMock(return_value=True)
                
                result = await ExecutionService.get_executions_by_project(
                    db, project_id, page=1, size=20, use_cache=True
                )
                
                assert isinstance(result, ExecutionListResponse)
                assert len(result.executions) == 3
                assert result.total == 3
                assert result.page == 1
                assert result.size == 20
                assert result.total_pages == 1
    
    @pytest.mark.asyncio
    async def test_invalidate_execution_caches(self):
        """Test cache invalidation."""
        project_id = str(uuid.uuid4())
        module_id = str(uuid.uuid4())
        execution_id = str(uuid.uuid4())
        
        with patch('app.executions.service.cache_service') as mock_cache:
            mock_cache.invalidate_pattern = AsyncMock(return_value=True)
            mock_cache.delete = AsyncMock(return_value=True)
            
            await ExecutionService.invalidate_execution_caches(
                project_id=project_id,
                module_id=module_id,
                execution_id=execution_id
            )
            
            # Verify cache invalidation was called
            assert mock_cache.invalidate_pattern.call_count == 3
            assert mock_cache.delete.call_count == 1


class TestExecutionSchemas:
    """Test execution Pydantic schemas."""
    
    def test_execution_response_schema(self):
        """Test ExecutionResponse schema."""
        execution_data = {
            "id": uuid.uuid4(),
            "project_id": uuid.uuid4(),
            "module_id": uuid.uuid4(),
            "file_name": "test.json",
            "file_size": 1024,
            "total_scenarios": 10,
            "passed_scenarios": 8,
            "failed_scenarios": 2,
            "skipped_scenarios": 0,
            "duration": 120.5,
            "uploaded_by": "test@example.com",
            "created_at": datetime.utcnow(),
            "pass_rate": 80.0,
            "status": "failed"
        }
        
        response = ExecutionResponse(**execution_data)
        
        assert response.total_scenarios == 10
        assert response.pass_rate == 80.0
        assert response.status == "failed"
    
    def test_scenario_response_schema(self):
        """Test ScenarioResponse schema."""
        scenario_data = {
            "id": uuid.uuid4(),
            "report_id": uuid.uuid4(),
            "name": "Test Scenario",
            "status": "passed",
            "duration": 1.5,
            "created_at": datetime.utcnow()
        }
        
        response = ScenarioResponse(**scenario_data)
        
        assert response.name == "Test Scenario"
        assert response.status == "passed"
        assert response.duration == 1.5
