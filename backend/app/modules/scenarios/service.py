"""Scenario service for filtering and rerun logic."""

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.reports.models import Scenario
from app.modules.scenarios.schemas import ScenarioResponse


class ScenarioService:
    """Service for scenario operations."""
    
    @staticmethod
    async def get_scenario_by_id(
        db: AsyncSession,
        scenario_id: str
    ) -> ScenarioResponse:
        """Get scenario by ID.
        
        Args:
            db: Database session
            scenario_id: Scenario UUID
            
        Returns:
            Scenario response
            
        Raises:
            NotFoundError: If scenario not found
        """
        result = await db.execute(
            select(Scenario).where(Scenario.id == scenario_id)
        )
        scenario = result.scalar_one_or_none()
        
        if not scenario:
            raise NotFoundError(message=f"Scenario with ID {scenario_id} not found")
        
        return ScenarioResponse.from_orm(scenario)
    
    @staticmethod
    async def filter_scenarios(
        db: AsyncSession,
        status: Optional[str] = None,
        feature: Optional[str] = None,
        tags: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 50
    ) -> tuple[list[ScenarioResponse], int]:
        """Filter scenarios with pagination.
        
        Args:
            db: Database session
            status: Filter by status
            feature: Filter by feature
            tags: Filter by tags
            search: Search query
            page: Page number
            size: Page size
            
        Returns:
            Tuple of (scenarios list, total count)
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
        
        return [
            ScenarioResponse.from_orm(s) for s in scenarios
        ], total
