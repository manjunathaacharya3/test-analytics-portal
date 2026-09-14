"""Data access layer for executions and scenarios."""
import uuid
import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.reports.models import Report, Scenario
from app.projects.models import Module, Project

logger = logging.getLogger(__name__)


class ExecutionRepository:
    """Repository for execution (report) data access."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def get_by_id(self, execution_id: str) -> Optional[Report]:
        """Get execution by ID.
        
        Args:
            execution_id: Execution (Report) ID
            
        Returns:
            Report instance or None if not found
        """
        result = await self.db.execute(
            select(Report)
            .where(Report.id == execution_id)
            .options(selectinload(Report.scenarios))
        )
        return result.scalar_one_or_none()
    
    async def get_by_project(
        self,
        project_id: str,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None
    ) -> List[Report]:
        """Get all executions for a project with pagination and filtering.
        
        Args:
            project_id: Project ID
            page: Page number (1-indexed)
            size: Number of items per page
            status: Optional status filter
            
        Returns:
            List of executions (reports) with module relationship loaded
        """
        offset = (page - 1) * size
        stmt = (
            select(Report)
            .where(Report.project_id == project_id)
            .options(selectinload(Report.module))
            .order_by(desc(Report.created_at))
        )
        
        # Apply status filter if provided
        # Note: Status is derived from passed/failed/skipped counts
        # We'll filter in the service layer for now
        
        stmt = stmt.offset(offset).limit(size)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_by_module(
        self,
        module_id: str,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None
    ) -> List[Report]:
        """Get all executions for a module with pagination and filtering.
        
        Args:
            module_id: Module ID
            page: Page number (1-indexed)
            size: Number of items per page
            status: Optional status filter
            
        Returns:
            List of executions (reports) with module relationship loaded
        """
        offset = (page - 1) * size
        stmt = (
            select(Report)
            .where(Report.module_id == module_id)
            .options(selectinload(Report.module))
            .order_by(desc(Report.created_at))
            .offset(offset)
            .limit(size)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_scenarios_by_execution(
        self,
        execution_id: str,
        page: int = 1,
        size: int = 50,
        status: Optional[str] = None
    ) -> List[Scenario]:
        """Get scenarios for an execution with pagination and filtering.
        
        Args:
            execution_id: Execution (Report) ID
            page: Page number (1-indexed)
            size: Number of items per page
            status: Optional status filter (passed, failed, skipped)
            
        Returns:
            List of scenarios
        """
        offset = (page - 1) * size
        stmt = select(Scenario).where(Scenario.report_id == execution_id)
        
        if status:
            stmt = stmt.where(Scenario.status == status)
        
        stmt = stmt.order_by(desc(Scenario.created_at)).offset(offset).limit(size)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def count_by_project(self, project_id: str) -> int:
        """Count total executions for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Total count of executions
        """
        result = await self.db.execute(
            select(func.count(Report.id))
            .where(Report.project_id == project_id)
        )
        return result.scalar() or 0
    
    async def count_by_module(self, module_id: str) -> int:
        """Count total executions for a module.
        
        Args:
            module_id: Module ID
            
        Returns:
            Total count of executions
        """
        result = await self.db.execute(
            select(func.count(Report.id))
            .where(Report.module_id == module_id)
        )
        return result.scalar() or 0
    
    async def count_scenarios_by_execution(
        self,
        execution_id: str,
        status: Optional[str] = None
    ) -> int:
        """Count scenarios for an execution with optional status filter.
        
        Args:
            execution_id: Execution (Report) ID
            status: Optional status filter
            
        Returns:
            Total count of scenarios
        """
        stmt = select(func.count(Scenario.id)).where(Scenario.report_id == execution_id)
        
        if status:
            stmt = stmt.where(Scenario.status == status)
        
        result = await self.db.execute(stmt)
        return result.scalar() or 0
