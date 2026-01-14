from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from database.database import get_db
from database.tables.execution import Execution
from database.tables.module import Module
from database.tables.project import Project
from database.tables.scenario import Scenario  # assuming you have a Scenario table
from service.schema.execution import ExecutionSummaryResponse, ScenarioResponse

router = APIRouter(prefix="/api/executions", tags=["Executions"])


def seconds_to_minutes_str(seconds: Optional[float]) -> Optional[str]:
    """Convert seconds (float) to rounded minutes string 'Nm'. Return None if input None."""
    if seconds is None:
        return None
    try:
        minutes = int(round(seconds / 60.0))
        return f"{minutes}m"
    except Exception:
        # fallback: return the raw value as string
        return str(seconds)


@router.get("/project/{project_id}", response_model=List[ExecutionSummaryResponse])
async def get_executions_by_project(project_id: str, db: AsyncSession = Depends(get_db)):
    # Ensure project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Fetch executions with module loaded
    result = await db.execute(
        select(Execution)
        .options(
            selectinload(Execution.module).selectinload(Module.project)
        )
        .join(Module, Module.id == Execution.module_id)
        .where(Module.project_id == project_id)
        .order_by(Execution.created_at.desc())
    )
    executions = result.scalars().all()

    # Build list of dicts matching ExecutionSummaryResponse (convert durations)
    out = []
    for e in executions:
        out.append({
            "id": e.id,
            "module_id": e.module_id,
            "module_name": getattr(e, "module").name if getattr(e, "module", None) else "Unknown",
            "passed": int(e.passed or 0),
            "failed": int(e.failed or 0),
            "total": int(e.total or 0),
            "duration": seconds_to_minutes_str(e.duration),
            "status": e.status,
            "created_at": e.created_at,
        })
    return out


@router.get("/module/{module_id}", response_model=List[ExecutionSummaryResponse])
async def get_executions_by_module(module_id: str, db: AsyncSession = Depends(get_db)):
    # Ensure module exists
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    # Fetch executions with module + project eagerly loaded
    result = await db.execute(
        select(Execution)
        .options(
            selectinload(Execution.module).selectinload(Module.project)
        )
        .where(Execution.module_id == module_id)
        .order_by(Execution.created_at.desc())
    )
    executions = result.scalars().all()

    out = []
    for e in executions:
        out.append({
            "id": e.id,
            "module_id": e.module_id,
            "module_name": getattr(e, "module").name if getattr(e, "module", None) else "Unknown",
            "passed": int(e.passed or 0),
            "failed": int(e.failed or 0),
            "total": int(e.total or 0),
            "duration": seconds_to_minutes_str(e.duration),
            "status": e.status,
            "created_at": e.created_at,
        })
    return out


@router.get("/{execution_id}/scenarios", response_model=List[ScenarioResponse])
async def get_execution_scenarios(execution_id: str, db: AsyncSession = Depends(get_db)):
    # Validate execution exists
    result = await db.execute(select(Execution).where(Execution.id == execution_id))
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Fetch scenarios related to this execution
    result = await db.execute(
        select(Scenario)
        .where(Scenario.execution_id == execution_id)
        .order_by(Scenario.created_at)
    )
    scenarios = result.scalars().all()

    # Convert duration to string with "m"
    response = []
    for sc in scenarios:
        duration_str = f"{round(sc.duration)}m" if sc.duration is not None else None
        response.append({
            "id": sc.id,
            "scenario": sc.scenario,
            "tags": sc.tags or [],
            "duration": duration_str,
            "status": sc.status,
            "failed_step": sc.failed_step,
            "error": sc.error,
            "attachments": sc.attachments or [],
        })
    return response


@router.get("/{project_id}/executions", response_model=List[ExecutionSummaryResponse])
async def list_executions(
        project_id: str,
        db: AsyncSession = Depends(get_db),
        limit: int = Query(100, ge=1, le=500),  # default 100, max 500
        offset: int = Query(0, ge=0),
        status: Optional[str] = None,  # filter by status if needed
):
    # Get modules for this project
    modules_result = await db.execute(
        select(Module.id, Module.name).where(Module.project_id == project_id)
    )
    modules = {m.id: m.name for m in modules_result.all()}

    if not modules:
        return []

    # Build query
    query = (
        select(Execution)
        .where(Execution.module_id.in_(modules.keys()))
        .order_by(desc(Execution.created_at))
        .limit(limit)
        .offset(offset)
    )

    if status:
        query = query.where(Execution.status == status)

    result = await db.execute(query)
    executions = result.scalars().all()

    out = []
    for e in executions:
        out.append({
            "id": e.id,
            "module_id": e.module_id,
            "module_name": modules.get(e.module_id, "Unknown"),
            "passed": int(e.passed or 0),
            "failed": int(e.failed or 0),
            "total": int(e.total or 0),
            "duration": seconds_to_minutes_str(e.duration),
            "status": e.status,
            "created_at": e.created_at,
        })
    return [
        ExecutionSummaryResponse(
            id=e.id,
            module_id=e.module_id,
            module_name=modules.get(e.module_id, "Unknown"),
            passed=e.passed,
            failed=e.failed,
            total=e.total,
            duration=f"{round(e.duration, 2)}m" if e.duration is not None else None,  # 🔹 convert float → string
            status=e.status,
            created_at=e.created_at,
        )
        for e in executions
    ]
