# routers/projects.py
import uuid

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.database import get_db
from database.tables.execution import Execution
from database.tables.module import Module
from database.tables.project import Project
from service.schema.ProjectOverviewResponse import ProjectOverviewResponse
from service.schema.project import ProjectResponse, ProjectCreate

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/create_project", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db)):
    db_project = Project(
        id=str(uuid.uuid4()),
        name=project.name,
        description=project.description,
        repository_url=project.repository_url,
        owner=project.owner,
    )
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project


@router.get("/all_projects", response_model=list[ProjectOverviewResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    # 1. Fetch all projects
    result = await db.execute(select(Project))
    projects = result.scalars().all()

    enriched_projects = []

    for project in projects:
        # count modules
        result = await db.execute(
            select(func.count(Module.id)).where(Module.project_id == project.id)
        )
        modules_count = result.scalar()

        # executions for this project
        result = await db.execute(
            select(
                func.sum(Execution.total).label("total_tests"),
                func.sum(Execution.passed).label("passed_tests"),
                func.max(Execution.created_at).label("last_run"),
            )
            .join(Module, Module.id == Execution.module_id)
            .where(Module.project_id == project.id)
        )
        row = result.one()
        total_tests = row.total_tests or 0
        passed_tests = row.passed_tests or 0
        last_run = row.last_run

        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0

        # last execution status
        result = await db.execute(
            select(Execution.status)
            .join(Module, Module.id == Execution.module_id)
            .where(Module.project_id == project.id)
            .order_by(Execution.created_at.desc())
            .limit(1)
        )
        last_status = result.scalar()

        enriched_projects.append(ProjectOverviewResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            repository_url=project.repository_url,
            owner=project.owner,
            total_tests=total_tests,
            pass_rate=round(pass_rate, 2),
            last_status=last_status,
            last_run=last_run,
            modules=modules_count,
            created_at=project.created_at,
            updated_at=project.updated_at,
            is_active=project.is_active,
        ))

    return enriched_projects


# routers/projects.py

@router.get("/{project_id}/modules")
async def list_project_modules(project_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch all modules for a given project"""
    # 1. Validate project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Fetch modules
    result = await db.execute(select(Module).where(Module.project_id == project_id))
    modules = result.scalars().all()

    return [
        {
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        }
        for m in modules
    ]
