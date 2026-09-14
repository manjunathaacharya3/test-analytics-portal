"""API routes for projects and modules."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.modules.auth.models import User
from app.projects.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectOverviewResponse,
    ModuleCreate,
    ModuleUpdate,
    ModuleResponse,
)
from app.projects.service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new test analytics project with the provided details. Public endpoint (no auth required).",
)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> ProjectResponse:
    """Create a new project.
    
    Args:
        project: Project creation data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Created project
    """
    service = ProjectService(db)
    return await service.create_project(project)


@router.get(
    "",
    response_model=List[ProjectOverviewResponse],
    summary="List all projects",
    description="Get a list of all projects with aggregated metrics, pagination, sorting, and filtering. Public endpoint (no auth required).",
)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    owner: Optional[str] = Query(None, description="Filter by owner email"),
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> List[ProjectOverviewResponse]:
    """List all projects with metrics, pagination, and filtering.
    
    Args:
        page: Page number (1-indexed)
        size: Number of items per page
        is_active: Filter by active status
        owner: Filter by owner email
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of projects with aggregated metrics
    """
    service = ProjectService(db)
    return await service.list_projects(
        page=page,
        size=size,
        is_active=is_active,
        owner=owner
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project by ID",
    description="Retrieve a single project by its ID. Public endpoint (no auth required).",
)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> ProjectResponse:
    """Get project by ID.
    
    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Project details
        
    Raises:
        HTTPException: If project not found
    """
    service = ProjectService(db)
    project = await service.get_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    return project


@router.get(
    "/{project_id}/modules",
    response_model=List[ModuleResponse],
    summary="List project modules",
    description="Get all modules belonging to a specific project. Public endpoint (no auth required).",
)
async def list_project_modules(
    project_id: str,
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> List[ModuleResponse]:
    """List all modules for a project.
    
    Args:
        project_id: Project ID
        db: Database session
        
    Returns:
        List of modules
        
    Raises:
        HTTPException: If project not found
    """
    service = ProjectService(db)
    
    # Verify project exists
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    return await service.get_project_modules(project_id)


@router.post(
    "/{project_id}/modules",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new module",
    description="Create a new module for a specific project. Public endpoint (no auth required).",
)
async def create_module(
    project_id: str,
    module: ModuleCreate,
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> ModuleResponse:
    """Create a new module for a project.
    
    Args:
        project_id: Project ID
        module: Module creation data
        db: Database session
        
    Returns:
        Created module
        
    Raises:
        HTTPException: If project not found or validation fails
    """
    service = ProjectService(db)
    
    try:
        return await service.create_module(project_id, module)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put(
    "/{project_id}/modules/{module_id}",
    response_model=ModuleResponse,
    summary="Update a module",
    description="Update an existing module. Public endpoint (no auth required).",
)
async def update_module(
    project_id: str,
    module_id: str,
    module_update: ModuleUpdate,
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> ModuleResponse:
    """Update a module.
    
    Args:
        project_id: Project ID
        module_id: Module ID
        module_update: Module update data
        db: Database session
        
    Returns:
        Updated module
        
    Raises:
        HTTPException: If module not found or validation fails
    """
    service = ProjectService(db)
    
    try:
        module = await service.update_module(project_id, module_id, module_update)
        
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module with ID {module_id} not found"
            )
        
        return module
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{project_id}/modules/{module_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a module",
    description="Delete a module. Public endpoint (no auth required).",
)
async def delete_module(
    project_id: str,
    module_id: str,
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> None:
    """Delete a module.
    
    Args:
        project_id: Project ID
        module_id: Module ID
        db: Database session
        
    Raises:
        HTTPException: If module not found or validation fails
    """
    service = ProjectService(db)
    
    try:
        deleted = await service.delete_module(project_id, module_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module with ID {module_id} not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="Update an existing project's details. Public endpoint (no auth required).",
)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> ProjectResponse:
    """Update a project.
    
    Args:
        project_id: Project ID
        project_update: Project update data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Updated project
        
    Raises:
        HTTPException: If project not found
    """
    service = ProjectService(db)
    project = await service.update_project(project_id, project_update)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Soft delete a project by setting is_active to false. Public endpoint (no auth required).",
)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user),  # Removed for public access
) -> None:
    """Soft delete a project.
    
    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database session
        
    Raises:
        HTTPException: If project not found
    """
    service = ProjectService(db)
    deleted = await service.soft_delete_project(project_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
