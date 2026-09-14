"""API routes for report upload and status tracking."""
import logging
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.modules.auth.models import User
from app.modules.reports.schemas import (
    UploadResponse,
    UploadTaskStatus,
)
from app.modules.reports.service import ReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload test report",
    description="""
    Upload a Cucumber JSON test report for processing.
    
    The upload is processed asynchronously in the background. The endpoint returns immediately
    with a task_id that can be used to track the upload progress.
    
    **File Requirements:**
    - Format: Cucumber JSON (.json extension)
    - Max size: 10MB
    - Encoding: UTF-8
    
    **Returns:**
    - task_id: Unique identifier for tracking upload status
    - status: Initial status ("processing")
    - message: Confirmation message
    
    **Authentication:**
    - Public endpoint (no auth required)
    """,
)
async def upload_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Cucumber JSON report file"),
    project_id: str = Form(..., description="Project ID"),
    module_id: str = Form(..., description="Module ID"),
    uploaded_by: str = Form("system", description="User who uploaded the report"),
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> UploadResponse:
    """Upload a test report for background processing.
    
    Args:
        background_tasks: FastAPI background tasks
        file: Uploaded Cucumber JSON file
        project_id: Project ID
        module_id: Module ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Upload response with task_id
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        service = ReportService(db)
        
        # Read file content into memory before background task
        file_content = await file.read()
        filename = file.filename
        
        # Initiate upload and get task ID (validates file content)
        upload_response = await service.initiate_upload(
            file_content=file_content,
            filename=filename,
            project_id=project_id,
            module_id=module_id,
            uploaded_by=uploaded_by,
        )
        
        # Add background task for processing with file content
        background_tasks.add_task(
            service.process_upload,
            task_id=upload_response.task_id,
            file_content=file_content,
            filename=filename,
            project_id=project_id,
            module_id=module_id,
            uploaded_by=uploaded_by,
        )
        
        logger.info(
            f"Report upload initiated: task_id={upload_response.task_id}, "
            f"user={uploaded_by}, file={filename}"
        )
        
        return upload_response
        
    except ValueError as e:
        # Validation error
        logger.warning(f"Report upload validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Unexpected error
        logger.exception(f"Report upload failed with unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate report upload",
        )


@router.get(
    "/upload/{task_id}/status",
    response_model=UploadTaskStatus,
    summary="Get upload status",
    description="""
    Retrieve the status of a report upload task.
    
    The status is retrieved from Redis and persists across server restarts.
    Task status is stored with a 24-hour TTL.
    
    **Status Values:**
    - `processing`: Upload is being processed
    - `completed`: Upload completed successfully
    - `failed`: Upload failed with error
    
    **Response Fields:**
    - task_id: Task identifier
    - status: Current status
    - progress: Progress percentage (0-100)
    - result: Result data (if completed)
    - error: Error message (if failed)
    
    **Authentication:**
    - Public endpoint (no auth required)
    """,
)
async def get_upload_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> UploadTaskStatus:
    """Get the status of a report upload task.
    
    Args:
        task_id: Task ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Task status
        
    Raises:
        HTTPException: If task not found
    """
    try:
        service = ReportService(db)
        task_status = await service.get_task_status(task_id)
        
        if not task_status:
            logger.warning(f"Task status not found: {task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found or expired",
            )
        
        logger.debug(f"Retrieved task status: {task_id} - {task_status.status}")
        return task_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get task status for {task_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task status",
        )
