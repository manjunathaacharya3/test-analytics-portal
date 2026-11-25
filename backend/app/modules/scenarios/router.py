"""Scenario API endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
# from app.core.security import get_current_user  # Temporarily disabled for testing
# from app.modules.auth.models import User  # Temporarily disabled for testing
from app.modules.reports.models import Report, Scenario
from app.modules.scenarios.schemas import (
    FailedScenarioListResponse,
    FailedScenarioResponse,
    ScenarioListResponse,
    ScenarioResponse,
)
from app.projects.models import Module, Project

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get(
    "/",
    response_model=ScenarioListResponse,
    summary="List scenarios",
    description="Get paginated list of scenarios with filtering"
)
async def list_scenarios(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by status"),
    feature: Optional[str] = Query(None, description="Filter by feature"),
    tags: Optional[str] = Query(None, description="Filter by tags"),
    search: Optional[str] = Query(None, description="Search in name or error"),
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user)  # Temporarily disabled for testing
) -> ScenarioListResponse:
    """List scenarios with filtering and pagination.
    
    Args:
        page: Page number
        size: Page size
        status: Filter by status
        feature: Filter by feature
        tags: Filter by tags
        search: Search query
        db: Database session
        
    Returns:
        Paginated list of scenarios
    """
    # Build query
    query = select(Scenario)
    
    # Apply filters
    if status:
        query = query.where(Scenario.status == status)
    if feature:
        query = query.where(Scenario.feature.ilike(f"%{feature}%"))
    if tags:
        query = query.where(Scenario.tags.ilike(f"%{tags}%"))
    if search:
        query = query.where(
            or_(
                Scenario.name.ilike(f"%{search}%"),
                Scenario.error_message.ilike(f"%{search}%")
            )
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    query = query.order_by(Scenario.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    scenarios = result.scalars().all()
    
    # Calculate pages
    pages = (total + size - 1) // size
    
    return ScenarioListResponse(
        scenarios=[ScenarioResponse.from_orm(s) for s in scenarios],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get(
    "/failures",
    response_model=FailedScenarioListResponse,
    summary="List failed scenarios",
    description=(
        "Get paginated list of failed scenarios enriched with project and "
        "module context, for use in failure analysis views. Public endpoint "
        "(no auth required)."
    )
)
async def list_failed_scenarios(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    project_id: Optional[uuid.UUID] = Query(None, description="Filter by project ID"),
    module_id: Optional[uuid.UUID] = Query(None, description="Filter by module ID"),
    search: Optional[str] = Query(None, description="Search in name or error message"),
    db: AsyncSession = Depends(get_db)
) -> FailedScenarioListResponse:
    """List failed scenarios with project/module context.

    Args:
        page: Page number
        size: Page size
        project_id: Optional project ID filter
        module_id: Optional module ID filter
        search: Search query
        db: Database session

    Returns:
        Paginated list of failed scenarios with project/module names
    """
    base_query = (
        select(Scenario, Report, Module, Project)
        .join(Report, Scenario.report_id == Report.id)
        .join(Module, Report.module_id == Module.id)
        .join(Project, Report.project_id == Project.id)
        .where(Scenario.status == "failed")
    )

    if project_id:
        base_query = base_query.where(Report.project_id == project_id)
    if module_id:
        base_query = base_query.where(Report.module_id == module_id)
    if search:
        base_query = base_query.where(
            or_(
                Scenario.name.ilike(f"%{search}%"),
                Scenario.error_message.ilike(f"%{search}%")
            )
        )

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination and ordering (most recent failures first)
    offset = (page - 1) * size
    base_query = base_query.order_by(Scenario.created_at.desc()).offset(offset).limit(size)

    result = await db.execute(base_query)
    rows = result.all()

    scenarios = [
        FailedScenarioResponse(
            id=scenario.id,
            name=scenario.name,
            status=scenario.status,
            duration=scenario.duration,
            error_message=scenario.error_message,
            stack_trace=scenario.stack_trace,
            tags=[t.strip() for t in scenario.tags.split(",") if t.strip()] if scenario.tags else [],
            feature=scenario.feature,
            created_at=scenario.created_at,
            project_id=project.id,
            project_name=project.name,
            module_id=module.id,
            module_name=module.name,
        )
        for scenario, report, module, project in rows
    ]

    pages = (total + size - 1) // size if total else 0

    return FailedScenarioListResponse(
        scenarios=scenarios,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get(
    "/{scenario_id}",
    response_model=ScenarioResponse,
    summary="Get scenario by ID",
    description="Get a specific scenario by its ID"
)
async def get_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user)  # Temporarily disabled for testing
) -> ScenarioResponse:
    """Get scenario by ID.
    
    Args:
        scenario_id: Scenario UUID
        db: Database session
        
    Returns:
        Scenario information
    """
    from app.core.exceptions import NotFoundError
    
    result = await db.execute(
        select(Scenario).where(Scenario.id == scenario_id)
    )
    scenario = result.scalar_one_or_none()
    
    if not scenario:
        raise NotFoundError(message=f"Scenario with ID {scenario_id} not found")
    
    return ScenarioResponse.from_orm(scenario)


@router.post(
    "/{scenario_id}/rerun",
    summary="Rerun scenario",
    description="Trigger a rerun of a specific scenario"
)
async def rerun_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user)  # Temporarily disabled for testing
):
    """Rerun a scenario.
    
    Args:
        scenario_id: Scenario UUID
        db: Database session
        
    Returns:
        Rerun status
    """
    # TODO: Implement scenario rerun logic
    # This would typically trigger a test execution in the CI/CD pipeline
    return {
        "message": "Scenario rerun triggered",
        "scenario_id": scenario_id,
        "status": "pending"
    }
