"""API routes for defect management."""
import logging
import uuid
from typing import Optional
import math

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundError, ConflictError
from app.modules.auth.models import User
from app.modules.defects.schemas import (
    DefectCreate,
    DefectUpdate,
    DefectResponse,
    DefectStatusUpdate,
    DefectAssignment,
    DefectListResponse,
)
from app.modules.defects.service import DefectService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/defects", tags=["Defects"])


@router.post(
    "",
    response_model=DefectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new defect",
    description="""
    Create a new defect in the system.
    
    **Required Fields:**
    - title: Defect title (max 500 chars)
    - description: Detailed description
    - severity: Critical, High, Medium, or Low
    - priority: P0, P1, P2, or P3
    - project_id: Project ID
    - reported_by: User who reported the defect
    
    **Optional Fields:**
    - assigned_to: User assigned to fix
    - module_id: Module where defect was found
    - scenario_id: Scenario where defect was found
    - status: Initial status (default: Open)
    
    **Authentication:**
    - Public endpoint (no auth required)
    """,
)
async def create_defect(
    defect_data: DefectCreate,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> DefectResponse:
    """Create a new defect.
    
    Args:
        defect_data: Defect creation data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Created defect
    """
    try:
        service = DefectService(db)
        defect = await service.create_defect(defect_data)
        
        logger.info(
            f"Defect created: id={defect.id}, user=system"
        )
        return defect
        
    except ValueError as e:
        logger.warning(f"Defect creation validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Defect creation failed with unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create defect",
        )


@router.get(
    "/{defect_id}",
    response_model=DefectResponse,
    summary="Get defect by ID",
    description="""
    Retrieve a single defect by its ID.
    
    **Authentication:**
    - Public endpoint (no auth required)
    """,
)
async def get_defect(
    defect_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> DefectResponse:
    """Get defect by ID.
    
    Args:
        defect_id: Defect ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Defect data
    """
    try:
        service = DefectService(db)
        defect = await service.get_defect(defect_id)
        return defect
        
    except NotFoundError as e:
        logger.warning(f"Defect not found: {defect_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Failed to get defect {defect_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve defect",
        )


@router.get(
    "",
    response_model=DefectListResponse,
    summary="List defects with filtering",
    description="""
    Retrieve a paginated list of defects with optional filtering.
    
    **Filters:**
    - project_id: Filter by project
    - module_id: Filter by module
    - status: Filter by status (Open, In Progress, Fixed, Closed, Won't Fix)
    - severity: Filter by severity (Critical, High, Medium, Low)
    - priority: Filter by priority (P0, P1, P2, P3)
    - assigned_to: Filter by assigned user
    
    **Pagination:**
    - page: Page number (default: 1)
    - size: Items per page (default: 20, max: 100)
    
    **Authentication:**
    - Public endpoint (no auth required)
    """,
)
async def list_defects(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    module_id: Optional[str] = Query(None, description="Filter by module ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned user"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> DefectListResponse:
    """List defects with filtering and pagination.
    
    Args:
        project_id: Filter by project ID
        module_id: Filter by module ID
        status: Filter by status
        severity: Filter by severity
        priority: Filter by priority
        assigned_to: Filter by assigned user
        page: Page number
        size: Page size
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Paginated list of defects
    """
    try:
        service = DefectService(db)
        defects, total = await service.get_defects(
            project_id=project_id,
            module_id=module_id,
            status=status,
            severity=severity,
            priority=priority,
            assigned_to=assigned_to,
            page=page,
            size=size,
        )
        
        total_pages = math.ceil(total / size) if total > 0 else 0
        
        return DefectListResponse(
            defects=defects,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
        )
        
    except Exception as e:
        logger.exception(f"Failed to list defects")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve defects",
        )


@router.put(
    "/{defect_id}",
    response_model=DefectResponse,
    summary="Update defect",
    description="""
    Update defect fields.
    
    **Updatable Fields:**
    - title, description, severity, priority
    - status (with validation)
    - assigned_to, module_id, scenario_id
    - resolution
    
    **Note:** Status transitions are validated. Use PUT /defects/{id}/status for better status update handling.
    
    **Authentication:**
    - Public endpoint (no auth required)
    """,
)
async def update_defect(
    defect_id: uuid.UUID,
    update_data: DefectUpdate,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> DefectResponse:
    """Update a defect.
    
    Args:
        defect_id: Defect ID
        update_data: Update data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Updated defect
    """
    try:
        service = DefectService(db)
        defect = await service.update_defect(defect_id, update_data)
        
        logger.info(
            f"Defect updated: id={defect_id}, user=system"
        )
        return defect
        
    except NotFoundError as e:
        logger.warning(f"Defect not found: {defect_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ConflictError as e:
        logger.warning(f"Invalid defect update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValueError as e:
        logger.warning(f"Defect update validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Failed to update defect {defect_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update defect",
        )


@router.delete(
    "/{defect_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete defect",
    description="""
    Delete a defect from the system.
    
    **Authentication:**
    - Public endpoint (no auth required)
    """,
)
async def delete_defect(
    defect_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> None:
    """Delete a defect.
    
    Args:
        defect_id: Defect ID
        current_user: Authenticated user
        db: Database session
    """
    try:
        service = DefectService(db)
        await service.delete_defect(defect_id)
        
        logger.info(
            f"Defect deleted: id={defect_id}, user=system"
        )
        
    except NotFoundError as e:
        logger.warning(f"Defect not found: {defect_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Failed to delete defect {defect_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete defect",
        )


@router.get(
    "/scenarios/{scenario_id}/defects",
    response_model=list[DefectResponse],
    summary="Get defects by scenario",
    description="""
    Retrieve all defects linked to a specific scenario.
    
    **Authentication:**
    - Public endpoint (no auth required)
    """,
)
async def get_scenario_defects(
    scenario_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> list[DefectResponse]:
    """Get defects linked to a scenario.
    
    Args:
        scenario_id: Scenario ID
        page: Page number
        size: Page size
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of defects
    """
    try:
        service = DefectService(db)
        defects = await service.get_defects_by_scenario(
            scenario_id=scenario_id,
            page=page,
            size=size,
        )
        return defects
        
    except Exception as e:
        logger.exception(f"Failed to get defects for scenario {scenario_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scenario defects",
        )


@router.post(
    "/{defect_id}/assign",
    response_model=DefectResponse,
    summary="Assign defect to user",
    description="""
    Assign a defect to a user for resolution.
    
    **Authentication:**
    - Public endpoint (no auth required)
    """,
)
async def assign_defect(
    defect_id: uuid.UUID,
    assignment: DefectAssignment,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> DefectResponse:
    """Assign a defect to a user.
    
    Args:
        defect_id: Defect ID
        assignment: Assignment data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Updated defect
    """
    try:
        service = DefectService(db)
        defect = await service.assign_defect(defect_id, assignment)
        
        logger.info(
            f"Defect assigned: id={defect_id}, assigned_to={assignment.assigned_to}, user=system"
        )
        return defect
        
    except NotFoundError as e:
        logger.warning(f"Defect not found: {defect_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Failed to assign defect {defect_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign defect",
        )


@router.put(
    "/{defect_id}/status",
    response_model=DefectResponse,
    summary="Update defect status",
    description="""
    Update defect status with validation of status transitions.
    
    **Valid Status Transitions:**
    - Open → In Progress, Won't Fix, Closed
    - In Progress → Fixed, Open, Won't Fix
    - Fixed → Closed, Open
    - Closed → Open
    - Won't Fix → Open
    
    **Note:** Resolution is required when transitioning to Fixed, Closed, or Won't Fix.
    
    **Authentication:**
    - Public endpoint (no auth required)
    """,
)
async def update_defect_status(
    defect_id: uuid.UUID,
    status_update: DefectStatusUpdate,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> DefectResponse:
    """Update defect status.
    
    Args:
        defect_id: Defect ID
        status_update: Status update data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Updated defect
    """
    try:
        service = DefectService(db)
        defect = await service.update_defect_status(defect_id, status_update)
        
        logger.info(
            f"Defect status updated: id={defect_id}, status={status_update.status}, user=system"
        )
        return defect
        
    except NotFoundError as e:
        logger.warning(f"Defect not found: {defect_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ConflictError as e:
        logger.warning(f"Invalid status transition: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValueError as e:
        logger.warning(f"Status update validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Failed to update defect status {defect_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update defect status",
        )
