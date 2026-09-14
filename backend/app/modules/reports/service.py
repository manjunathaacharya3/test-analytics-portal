"""Business logic for report upload and processing."""
import uuid
import logging
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reports.repository import ReportRepository
from app.modules.reports.cucumber_parser import CucumberParser
from app.modules.reports.task_status import task_status_service, TaskStatus
from app.modules.reports.schemas import (
    ReportResponse,
    UploadTaskStatus,
    UploadResponse,
)
from app.core.cache import cache_service

logger = logging.getLogger(__name__)

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


class ReportService:
    """Service layer for report upload and processing."""
    
    def __init__(self, db: AsyncSession):
        """Initialize service with database session.
        
        Args:
            db: Async database session
        """
        self.repository = ReportRepository(db)
        self.db = db
    
    def validate_upload_file(self, file_content: bytes, filename: str) -> str:
        """Validate uploaded file content.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Decoded file content as string
            
        Raises:
            ValueError: If file is invalid
        """
        # Check file extension
        if not filename or not filename.endswith('.json'):
            raise ValueError("File must be a JSON file (.json extension)")
        
        # Check file size
        file_size = len(file_content)
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"File size ({file_size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)")
        
        # Validate JSON format
        try:
            content_str = file_content.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError("File must be UTF-8 encoded")
        
        # Validate Cucumber format
        if not CucumberParser.validate_format(content_str):
            raise ValueError("File is not in valid Cucumber JSON format")
        
        return content_str
    
    async def initiate_upload(
        self,
        file_content: bytes,
        filename: str,
        project_id: str,
        module_id: str,
        uploaded_by: str
    ) -> UploadResponse:
        """Initiate report upload and return task ID.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            project_id: Project ID
            module_id: Module ID
            uploaded_by: User email who uploaded the report
            
        Returns:
            Upload response with task ID
            
        Raises:
            ValueError: If file is invalid
        """
        # Validate file content
        self.validate_upload_file(file_content, filename)
        
        # Create task
        task_id = await task_status_service.create_task()
        
        logger.info(f"Initiated report upload: task_id={task_id}, file={filename}, project={project_id}")
        
        return UploadResponse(
            task_id=task_id,
            status="processing",
            message="Report upload started"
        )
    
    async def process_upload(
        self,
        task_id: str,
        file_content: bytes,
        filename: str,
        project_id: str,
        module_id: str,
        uploaded_by: str
    ) -> None:
        """Process uploaded report in background.
        
        This method is called as a background task.
        
        Args:
            task_id: Task ID for status tracking
            file_content: File content as bytes
            filename: Original filename
            project_id: Project ID
            module_id: Module ID
            uploaded_by: User email who uploaded the report
        """
        try:
            logger.info(f"Processing upload task {task_id}")
            
            # Update progress: 10%
            await task_status_service.update_progress(task_id, 10)
            
            # Decode file content
            file_size = len(file_content)
            content_str = file_content.decode('utf-8')
            
            # Update progress: 30%
            await task_status_service.update_progress(task_id, 30)
            
            # Parse Cucumber JSON
            logger.debug(f"Parsing Cucumber JSON for task {task_id}")
            parsed_data = CucumberParser.parse(content_str)
            
            # Update progress: 50%
            await task_status_service.update_progress(task_id, 50)
            
            # Create report in database
            report_data = {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "module_id": module_id,
                "file_name": filename,
                "file_size": file_size,
                "total_scenarios": parsed_data["total_scenarios"],
                "passed_scenarios": parsed_data["passed_scenarios"],
                "failed_scenarios": parsed_data["failed_scenarios"],
                "skipped_scenarios": parsed_data["skipped_scenarios"],
                "duration": parsed_data["duration"],
                "uploaded_by": uploaded_by,
            }
            
            report = await self.repository.create_report(report_data)
            
            # Update progress: 70%
            await task_status_service.update_progress(task_id, 70)
            
            # Create scenarios in batch
            scenarios_data = [
                {
                    "id": str(uuid.uuid4()),
                    "report_id": report.id,
                    **scenario
                }
                for scenario in parsed_data["scenarios"]
            ]
            
            await self.repository.create_scenarios(scenarios_data)
            
            # Update progress: 90%
            await task_status_service.update_progress(task_id, 90)
            
            # Invalidate related caches
            await cache_service.invalidate_pattern(f"reports:project:{project_id}:*")
            await cache_service.invalidate_pattern(f"reports:module:{module_id}:*")
            logger.debug(f"Invalidated caches for project {project_id} and module {module_id}")
            
            # Invalidate execution caches (reports are executions)
            from app.executions.service import ExecutionService
            await ExecutionService.invalidate_execution_caches(
                project_id=project_id,
                module_id=module_id
            )
            logger.debug(f"Invalidated execution caches for project {project_id} and module {module_id}")
            
            # Mark task as completed
            result = {
                "report_id": str(report.id),
                "scenarios_processed": len(scenarios_data),
                "total_scenarios": report.total_scenarios,
                "passed_scenarios": report.passed_scenarios,
                "failed_scenarios": report.failed_scenarios,
                "skipped_scenarios": report.skipped_scenarios,
            }
            
            await task_status_service.mark_completed(task_id, result)
            logger.info(f"Task {task_id} completed successfully: report_id={report.id}")
            
        except ValueError as e:
            # Validation or parsing error
            error_msg = f"Validation error: {str(e)}"
            logger.error(f"Task {task_id} failed: {error_msg}")
            await task_status_service.mark_failed(task_id, error_msg)
            
        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(f"Task {task_id} failed with exception")
            await task_status_service.mark_failed(task_id, error_msg)
    
    async def get_task_status(self, task_id: str) -> Optional[UploadTaskStatus]:
        """Get task status from Redis.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status or None if not found
        """
        status_data = await task_status_service.get_status(task_id)
        
        if not status_data:
            return None
        
        return UploadTaskStatus(
            task_id=status_data.task_id,
            status=status_data.status.value,
            progress=status_data.progress,
            result=status_data.result,
            error=status_data.error
        )
