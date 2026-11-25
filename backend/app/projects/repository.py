"""Data access layer for projects and modules."""
from typing import Optional, List
from datetime import datetime

from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.projects.models import Project, Module


class ProjectRepository:
    """Repository for project data access."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def create(self, project_data: dict) -> Project:
        """Create a new project.
        
        Args:
            project_data: Dictionary containing project fields
            
        Returns:
            Created project instance
        """
        project = Project(**project_data)
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project
    
    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project instance or None if not found
        """
        result = await self.db.execute(
            select(Project)
            .where(Project.id == project_id)
            .options(selectinload(Project.modules))
        )
        return result.scalar_one_or_none()
    
    async def get_all(self) -> List[Project]:
        """Get all projects.
        
        Returns:
            List of all projects
        """
        result = await self.db.execute(
            select(Project).order_by(Project.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_all_with_metrics(
        self,
        page: int = 1,
        size: int = 20,
        is_active: Optional[bool] = None,
        owner: Optional[str] = None
    ) -> List[dict]:
        """Get all projects with aggregated metrics, pagination, and filtering.
        
        This method fixes the N+1 query problem by using a single optimized query
        with JOINs and aggregations instead of 301 queries for 100 projects.
        
        IMPORTANT: Counts UNIQUE scenarios by name, not total execution counts.
        If a module has 4 scenarios and is executed twice, it shows 4, not 8.
        
        Args:
            page: Page number (1-indexed)
            size: Number of items per page
            is_active: Filter by active status
            owner: Filter by owner email
        
        Returns:
            List of dictionaries containing project data and metrics
        """
        from app.modules.reports.models import Report, Scenario  # Import here to avoid circular dependency
        
        # Create a subquery to count modules per project
        # This counts all modules regardless of whether they have reports
        modules_subquery = (
            select(
                Module.project_id,
                func.count(Module.id).label("module_count")
            )
            .group_by(Module.project_id)
        ).subquery()
        
        # Subquery to get the latest report per module (for status determination)
        latest_report_subquery = (
            select(
                Report.module_id,
                func.max(Report.created_at).label("latest_created_at")
            )
            .group_by(Report.module_id)
        ).subquery()
        
        # Single optimized query with JOINs and aggregations
        # This replaces N+1 queries with a single query using database-level aggregations
        # COUNT DISTINCT scenarios by name to avoid counting duplicates across executions
        stmt = (
            select(
                Project,
                func.coalesce(modules_subquery.c.module_count, 0).label("modules_count"),
                # Count unique scenarios by name (not SUM of execution counts)
                func.count(func.distinct(Scenario.name)).label("total_tests"),
                # Count scenarios with status='passed' from latest execution
                func.sum(
                    case(
                        (
                            (Scenario.status == 'passed') & 
                            (Report.created_at == latest_report_subquery.c.latest_created_at),
                            1
                        ),
                        else_=0
                    )
                ).label("passed_tests"),
                # Count scenarios with status='failed' from latest execution
                func.sum(
                    case(
                        (
                            (Scenario.status == 'failed') & 
                            (Report.created_at == latest_report_subquery.c.latest_created_at),
                            1
                        ),
                        else_=0
                    )
                ).label("failed_tests"),
                func.max(Report.created_at).label("last_run"),
            )
            .outerjoin(modules_subquery, modules_subquery.c.project_id == Project.id)
            .outerjoin(Module, Module.project_id == Project.id)
            .outerjoin(Report, Report.module_id == Module.id)
            .outerjoin(latest_report_subquery, latest_report_subquery.c.module_id == Module.id)
            .outerjoin(Scenario, Scenario.report_id == Report.id)
        )
        
        # Apply filters
        if is_active is not None:
            stmt = stmt.where(Project.is_active == is_active)
        if owner is not None:
            stmt = stmt.where(Project.owner == owner)
        
        # Group by Project.id and module_count from subquery
        # The module_count must be in GROUP BY because it's selected but not aggregated in the main query
        stmt = stmt.group_by(Project.id, modules_subquery.c.module_count).order_by(Project.created_at.desc())
        
        # Apply pagination
        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size)
        
        # Add eager loading for modules relationship
        stmt = stmt.options(selectinload(Project.modules))
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        enriched_projects = []
        for row in rows:
            project = row[0]
            modules_count = int(row[1]) if row[1] is not None else 0
            total_tests = int(row[2]) if row[2] is not None else 0
            passed_tests = int(row[3]) if row[3] is not None else 0
            failed_tests = int(row[4]) if row[4] is not None else 0
            last_run = row[5]
            
            pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0
            
            # Determine status based on test results from latest execution
            if total_tests == 0:
                last_status = None
            elif failed_tests == 0:
                last_status = "passed"
            elif passed_tests == 0:
                last_status = "failed"
            else:
                last_status = "mixed"
            
            enriched_projects.append({
                "project": project,
                "modules": modules_count,
                "total_tests": total_tests,
                "pass_rate": round(pass_rate, 2),
                "last_status": last_status,
                "last_run": last_run,
            })
        
        return enriched_projects
    
    async def update(self, project_id: str, update_data: dict) -> Optional[Project]:
        """Update a project.
        
        Args:
            project_id: Project ID
            update_data: Dictionary containing fields to update
            
        Returns:
            Updated project instance or None if not found
        """
        project = await self.get_by_id(project_id)
        if not project:
            return None
        
        for key, value in update_data.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)
        
        await self.db.commit()
        await self.db.refresh(project)
        return project
    
    async def delete(self, project_id: str) -> bool:
        """Delete a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            True if deleted, False if not found
        """
        project = await self.get_by_id(project_id)
        if not project:
            return False
        
        await self.db.delete(project)
        await self.db.commit()
        return True
    
    async def get_modules(self, project_id: str) -> List[Module]:
        """Get all modules for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of modules
        """
        result = await self.db.execute(
            select(Module)
            .where(Module.project_id == project_id)
            .order_by(Module.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_module_by_name(self, project_id: str, module_name: str) -> Optional[Module]:
        """Get module by name with case-insensitive search.
        
        Args:
            project_id: Project ID
            module_name: Module name (case-insensitive)
            
        Returns:
            Module instance or None if not found
        """
        result = await self.db.execute(
            select(Module)
            .where(Module.project_id == project_id)
            .where(func.lower(Module.name) == func.lower(module_name))
        )
        return result.scalar_one_or_none()
    
    async def create_module(self, module_data: dict) -> Module:
        """Create a new module.
        
        Args:
            module_data: Dictionary containing module fields
            
        Returns:
            Created module instance
        """
        module = Module(**module_data)
        self.db.add(module)
        await self.db.commit()
        await self.db.refresh(module)
        return module
    
    async def get_module_by_id(self, module_id: str) -> Optional[Module]:
        """Get module by ID.
        
        Args:
            module_id: Module ID
            
        Returns:
            Module instance or None if not found
        """
        result = await self.db.execute(
            select(Module)
            .where(Module.id == module_id)
        )
        return result.scalar_one_or_none()
    
    async def update_module(self, module_id: str, update_data: dict) -> Optional[Module]:
        """Update a module.
        
        Args:
            module_id: Module ID
            update_data: Dictionary containing fields to update
            
        Returns:
            Updated module instance or None if not found
        """
        module = await self.get_module_by_id(module_id)
        if not module:
            return None
        
        for key, value in update_data.items():
            if hasattr(module, key) and value is not None:
                setattr(module, key, value)
        
        await self.db.commit()
        await self.db.refresh(module)
        return module
    
    async def delete_module(self, module_id: str) -> bool:
        """Delete a module.
        
        Args:
            module_id: Module ID
            
        Returns:
            True if deleted, False if not found
        """
        module = await self.get_module_by_id(module_id)
        if not module:
            return False
        
        await self.db.delete(module)
        await self.db.commit()
        return True
