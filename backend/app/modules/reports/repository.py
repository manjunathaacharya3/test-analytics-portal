"""Data access layer for reports and scenarios."""
import uuid
import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.reports.models import Report, Scenario

logger = logging.getLogger(__name__)


class ReportRepository:
    """Repository for report and scenario data access."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def create_report(self, report_data: dict) -> Report:
        """Create a new report.
        
        Args:
            report_data: Dictionary containing report fields
            
        Returns:
            Created report instance
        """
        report = Report(**report_data)
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        logger.info(f"Created report {report.id} for project {report.project_id}")
        return report
    
    async def get_report_by_id(self, report_id: str) -> Optional[Report]:
        """Get report by ID.
        
        Args:
            report_id: Report ID
            
        Returns:
            Report instance or None if not found
        """
        result = await self.db.execute(
            select(Report)
            .where(Report.id == report_id)
            .options(selectinload(Report.scenarios))
        )
        return result.scalar_one_or_none()
    
    async def get_reports_by_project(
        self,
        project_id: str,
        page: int = 1,
        size: int = 20
    ) -> List[Report]:
        """Get all reports for a project with pagination.
        
        Args:
            project_id: Project ID
            page: Page number (1-indexed)
            size: Number of items per page
            
        Returns:
            List of reports
        """
        offset = (page - 1) * size
        result = await self.db.execute(
            select(Report)
            .where(Report.project_id == project_id)
            .order_by(Report.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        return result.scalars().all()
    
    async def get_reports_by_module(
        self,
        module_id: str,
        page: int = 1,
        size: int = 20
    ) -> List[Report]:
        """Get all reports for a module with pagination.
        
        Args:
            module_id: Module ID
            page: Page number (1-indexed)
            size: Number of items per page
            
        Returns:
            List of reports
        """
        offset = (page - 1) * size
        result = await self.db.execute(
            select(Report)
            .where(Report.module_id == module_id)
            .order_by(Report.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        return result.scalars().all()
    
    async def create_scenarios(self, scenarios_data: List[dict]) -> List[Scenario]:
        """Create multiple scenarios in batch.
        
        Args:
            scenarios_data: List of dictionaries containing scenario fields
            
        Returns:
            List of created scenario instances
        """
        scenarios = [Scenario(**data) for data in scenarios_data]
        self.db.add_all(scenarios)
        await self.db.commit()
        
        # Refresh all scenarios
        for scenario in scenarios:
            await self.db.refresh(scenario)
        
        logger.info(f"Created {len(scenarios)} scenarios")
        return scenarios
    
    async def get_scenarios_by_report(
        self,
        report_id: str,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 50
    ) -> List[Scenario]:
        """Get scenarios for a report with optional filtering.
        
        Args:
            report_id: Report ID
            status: Optional status filter (passed, failed, skipped)
            page: Page number (1-indexed)
            size: Number of items per page
            
        Returns:
            List of scenarios
        """
        offset = (page - 1) * size
        stmt = select(Scenario).where(Scenario.report_id == report_id)
        
        if status:
            stmt = stmt.where(Scenario.status == status)
        
        stmt = stmt.order_by(Scenario.created_at.desc()).offset(offset).limit(size)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
