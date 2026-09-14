"""API endpoints for execution operations."""
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
# from app.core.security import get_current_user  # Temporarily disabled for testing
# from app.modules.auth.models import User  # Temporarily disabled for testing
from app.executions.service import ExecutionService
from app.executions.schemas import (
    ExecutionResponse,
    ExecutionListResponse,
    ScenarioListResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get(
    "/{execution_id}",
    response_model=ExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get execution by ID",
    description="Retrieve a single execution by its ID with caching support."
)
async def get_execution(
    execution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user)  # Temporarily disabled for testing
) -> ExecutionResponse:
    """Get execution by ID.
    
    Args:
        execution_id: Execution ID
        db: Database session
        
    Returns:
        ExecutionResponse
    """
    logger.info(f"Fetching execution {execution_id}")
    return await ExecutionService.get_execution_by_id(db, str(execution_id))


@router.get(
    "/{execution_id}/scenarios",
    response_model=ScenarioListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get scenarios for an execution",
    description="Retrieve paginated scenarios for a specific execution with optional status filtering."
)
async def get_execution_scenarios(
    execution_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(50, ge=1, le=100, description="Page size (max 100)"),
    status: Optional[str] = Query(
        None,
        description="Filter by status (passed, failed, skipped)"
    ),
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user)  # Temporarily disabled for testing
) -> ScenarioListResponse:
    """Get scenarios for an execution.
    
    Args:
        execution_id: Execution ID
        page: Page number (1-indexed)
        size: Page size
        status: Optional status filter
        db: Database session
        
    Returns:
        ScenarioListResponse
    """
    logger.info(
        f"Fetching scenarios for execution {execution_id} "
        f"(page={page}, size={size}, status={status})"
    )
    return await ExecutionService.get_scenarios_by_execution(
        db, str(execution_id), page, size, status
    )


# Additional router for project-level executions
project_router = APIRouter(prefix="/projects", tags=["executions"])


@project_router.get(
    "/{project_id}/executions",
    response_model=ExecutionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get executions for a project",
    description="Retrieve paginated executions for a specific project with optional status filtering."
)
async def get_project_executions(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    status: Optional[str] = Query(
        None,
        description="Filter by status (passed, failed, mixed)"
    ),
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user)  # Temporarily disabled for testing
) -> ExecutionListResponse:
    """Get executions for a project.
    
    Args:
        project_id: Project ID
        page: Page number (1-indexed)
        size: Page size
        status: Optional status filter
        db: Database session
        
    Returns:
        ExecutionListResponse
    """
    logger.info(
        f"Fetching executions for project {project_id} "
        f"(page={page}, size={size}, status={status})"
    )
    return await ExecutionService.get_executions_by_project(
        db, str(project_id), page, size, status
    )


# Additional router for module-level executions
module_router = APIRouter(prefix="/modules", tags=["executions"])


@module_router.get(
    "/{module_id}/executions",
    response_model=ExecutionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get executions for a module",
    description="Retrieve paginated executions for a specific module with optional status filtering."
)
async def get_module_executions(
    module_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    status: Optional[str] = Query(
        None,
        description="Filter by status (passed, failed, mixed)"
    ),
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user)  # Temporarily disabled for testing
) -> ExecutionListResponse:
    """Get executions for a module.
    
    Args:
        module_id: Module ID
        page: Page number (1-indexed)
        size: Page size
        status: Optional status filter
        db: Database session
        
    Returns:
        ExecutionListResponse
    """
    logger.info(
        f"Fetching executions for module {module_id} "
        f"(page={page}, size={size}, status={status})"
    )
    return await ExecutionService.get_executions_by_module(
        db, str(module_id), page, size, status
    )
