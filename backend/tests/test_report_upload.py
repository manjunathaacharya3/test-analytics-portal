"""Unit tests for report upload API."""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from io import BytesIO

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reports.service import ReportService
from app.modules.reports.cucumber_parser import CucumberParser
from app.modules.reports.task_status import TaskStatusService, TaskStatus


class TestCucumberParser:
    """Test Cucumber JSON parser."""
    
    def test_validate_format_valid(self):
        """Test validation of valid Cucumber JSON."""
        valid_json = json.dumps([
            {
                "name": "Test Feature",
                "elements": [
                    {
                        "name": "Test Scenario",
                        "type": "scenario",
                        "steps": []
                    }
                ]
            }
        ])
        
        assert CucumberParser.validate_format(valid_json) is True
    
    def test_validate_format_invalid_not_array(self):
        """Test validation fails for non-array JSON."""
        invalid_json = json.dumps({"key": "value"})
        assert CucumberParser.validate_format(invalid_json) is False
    
    def test_validate_format_invalid_empty(self):
        """Test validation fails for empty array."""
        invalid_json = json.dumps([])
        assert CucumberParser.validate_format(invalid_json) is False
    
    def test_parse_valid_cucumber_json(self):
        """Test parsing valid Cucumber JSON."""
        cucumber_json = json.dumps([
            {
                "name": "Login Feature",
                "elements": [
                    {
                        "name": "Successful login",
                        "type": "scenario",
                        "tags": [{"name": "@smoke"}],
                        "steps": [
                            {
                                "name": "Given user is on login page",
                                "result": {"status": "passed", "duration": 1000000000}
                            },
                            {
                                "name": "When user enters credentials",
                                "result": {"status": "passed", "duration": 2000000000}
                            }
                        ]
                    },
                    {
                        "name": "Failed login",
                        "type": "scenario",
                        "steps": [
                            {
                                "name": "Given user is on login page",
                                "result": {"status": "passed", "duration": 1000000000}
                            },
                            {
                                "name": "When user enters wrong credentials",
                                "result": {
                                    "status": "failed",
                                    "duration": 1000000000,
                                    "error_message": "AssertionError: Login failed\nStack trace here"
                                }
                            }
                        ]
                    }
                ]
            }
        ])
        
        result = CucumberParser.parse(cucumber_json)
        
        assert result["total_scenarios"] == 2
        assert result["passed_scenarios"] == 1
        assert result["failed_scenarios"] == 1
        assert result["skipped_scenarios"] == 0
        assert len(result["scenarios"]) == 2
        assert result["scenarios"][0]["name"] == "Successful login"
        assert result["scenarios"][0]["status"] == "passed"
        assert result["scenarios"][0]["tags"] == "@smoke"
        assert result["scenarios"][1]["status"] == "failed"
        assert result["scenarios"][1]["error_message"] == "AssertionError: Login failed"
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON raises ValueError."""
        invalid_json = "not valid json"
        
        with pytest.raises(ValueError, match="Invalid JSON format"):
            CucumberParser.parse(invalid_json)


class TestTaskStatusService:
    """Test task status service."""
    
    @pytest.mark.asyncio
    async def test_create_task(self):
        """Test task creation."""
        service = TaskStatusService()
        
        with patch.object(service, 'set_status', return_value=True) as mock_set:
            task_id = await service.create_task()
            
            assert task_id is not None
            assert len(task_id) == 36  # UUID length
            mock_set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_progress(self):
        """Test progress update."""
        service = TaskStatusService()
        task_id = "test-task-id"
        
        # Mock get_status to return existing status
        from app.modules.reports.task_status import TaskStatusData
        existing_status = TaskStatusData(
            task_id=task_id,
            status=TaskStatus.PROCESSING,
            progress=0
        )
        
        with patch.object(service, 'get_status', return_value=existing_status):
            with patch.object(service, 'set_status', return_value=True) as mock_set:
                result = await service.update_progress(task_id, 50)
                
                assert result is True
                mock_set.assert_called_once()
                # Check that progress was updated
                call_args = mock_set.call_args[0]
                assert call_args[1].progress == 50
    
    @pytest.mark.asyncio
    async def test_mark_completed(self):
        """Test marking task as completed."""
        service = TaskStatusService()
        task_id = "test-task-id"
        result_data = {"report_id": "123", "scenarios_processed": 10}
        
        from app.modules.reports.task_status import TaskStatusData
        existing_status = TaskStatusData(
            task_id=task_id,
            status=TaskStatus.PROCESSING,
            progress=50
        )
        
        with patch.object(service, 'get_status', return_value=existing_status):
            with patch.object(service, 'set_status', return_value=True) as mock_set:
                result = await service.mark_completed(task_id, result_data)
                
                assert result is True
                call_args = mock_set.call_args[0]
                assert call_args[1].status == TaskStatus.COMPLETED
                assert call_args[1].progress == 100
                assert call_args[1].result == result_data


class TestReportService:
    """Test report service."""
    
    @pytest.mark.asyncio
    async def test_validate_upload_file_valid(self):
        """Test file validation with valid file."""
        # Create mock UploadFile
        valid_json = json.dumps([
            {"name": "Feature", "elements": [{"name": "Scenario", "type": "scenario", "steps": []}]}
        ])
        file_content = valid_json.encode('utf-8')
        
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test_report.json"
        mock_file.read = AsyncMock(return_value=file_content)
        mock_file.seek = AsyncMock()
        
        mock_db = Mock(spec=AsyncSession)
        service = ReportService(mock_db)
        
        # Should not raise exception
        await service.validate_upload_file(mock_file)
    
    @pytest.mark.asyncio
    async def test_validate_upload_file_invalid_extension(self):
        """Test file validation fails for non-JSON file."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test_report.txt"
        
        mock_db = Mock(spec=AsyncSession)
        service = ReportService(mock_db)
        
        with pytest.raises(ValueError, match="File must be a JSON file"):
            await service.validate_upload_file(mock_file)
    
    @pytest.mark.asyncio
    async def test_validate_upload_file_too_large(self):
        """Test file validation fails for files > 10MB."""
        # Create file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)
        
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test_report.json"
        mock_file.read = AsyncMock(return_value=large_content)
        
        mock_db = Mock(spec=AsyncSession)
        service = ReportService(mock_db)
        
        with pytest.raises(ValueError, match="File size .* exceeds maximum"):
            await service.validate_upload_file(mock_file)
    
    @pytest.mark.asyncio
    async def test_validate_upload_file_invalid_format(self):
        """Test file validation fails for invalid Cucumber format."""
        invalid_json = json.dumps({"not": "cucumber"})
        file_content = invalid_json.encode('utf-8')
        
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test_report.json"
        mock_file.read = AsyncMock(return_value=file_content)
        
        mock_db = Mock(spec=AsyncSession)
        service = ReportService(mock_db)
        
        with pytest.raises(ValueError, match="not in valid Cucumber JSON format"):
            await service.validate_upload_file(mock_file)
