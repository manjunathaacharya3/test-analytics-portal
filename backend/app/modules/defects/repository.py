"""Data access layer for defects."""
import uuid
import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.defects.models import Defect

logger = logging.getLogger(__name__)


class DefectRepository:
    """Repository for defect data access."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def create_defect(self, defect_data: dict) -> Defect:
        """Create a new defect.
        
        Args:
            defect_data: Dictionary containing defect fields
            
        Returns:
            Created defect instance
        """
        defect = Defect(**defect_data)
        self.db.add(defect)
        await self.db.commit()
        await self.db.refresh(defect)
        logger.info(f"Created defect {defect.id} for project {defect.project_id}")
        return defect
    
    async def get_defect_by_id(self, defect_id: uuid.UUID) -> Optional[Defect]:
        """Get defect by ID.
        
        Args:
            defect_id: Defect ID
            
        Returns:
            Defect instance or None if not found
        """
        result = await self.db.execute(
            select(Defect).where(Defect.id == defect_id)
        )
        return result.scalar_one_or_none()
    
    async def get_defects(
        self,
        project_id: Optional[str] = None,
        module_id: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> tuple[List[Defect], int]:
        """Get defects with filtering and pagination.
        
        Args:
            project_id: Filter by project ID
            module_id: Filter by module ID
            status: Filter by status
            severity: Filter by severity
            priority: Filter by priority
            assigned_to: Filter by assigned user
            page: Page number (1-indexed)
            size: Number of items per page
            
        Returns:
            Tuple of (list of defects, total count)
        """
        # Build filter conditions
        conditions = []
        if project_id:
            conditions.append(Defect.project_id == project_id)
        if module_id:
            conditions.append(Defect.module_id == module_id)
        if status:
            conditions.append(Defect.status == status)
        if severity:
            conditions.append(Defect.severity == severity)
        if priority:
            conditions.append(Defect.priority == priority)
        if assigned_to:
            conditions.append(Defect.assigned_to == assigned_to)
        
        # Build query
        stmt = select(Defect)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Get total count
        count_stmt = select(func.count()).select_from(Defect)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()
        
        # Apply pagination and ordering
        offset = (page - 1) * size
        stmt = stmt.order_by(Defect.created_at.desc()).offset(offset).limit(size)
        
        # Execute query
        result = await self.db.execute(stmt)
        defects = result.scalars().all()
        
        logger.debug(f"Retrieved {len(defects)} defects (total: {total})")
        return list(defects), total
    
    async def get_defects_by_scenario(
        self,
        scenario_id: uuid.UUID,
        page: int = 1,
        size: int = 20
    ) -> List[Defect]:
        """Get defects linked to a specific scenario.
        
        Args:
            scenario_id: Scenario ID
            page: Page number (1-indexed)
            size: Number of items per page
            
        Returns:
            List of defects
        """
        offset = (page - 1) * size
        stmt = (
            select(Defect)
            .where(Defect.scenario_id == scenario_id)
            .order_by(Defect.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        
        result = await self.db.execute(stmt)
        defects = result.scalars().all()
        logger.debug(f"Retrieved {len(defects)} defects for scenario {scenario_id}")
        return list(defects)
    
    async def update_defect(
        self,
        defect_id: uuid.UUID,
        update_data: dict
    ) -> Optional[Defect]:
        """Update a defect.
        
        Args:
            defect_id: Defect ID
            update_data: Dictionary of fields to update
            
        Returns:
            Updated defect instance or None if not found
        """
        defect = await self.get_defect_by_id(defect_id)
        if not defect:
            return None
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(defect, key):
                setattr(defect, key, value)
        
        # Update timestamp
        defect.updated_at = datetime.utcnow()
        
        # Handle closed_at for status changes
        if 'status' in update_data:
            if update_data['status'] in ['Closed', 'Fixed', "Won't Fix"]:
                if not defect.closed_at:
                    defect.closed_at = datetime.utcnow()
            elif defect.closed_at:
                # Reopening defect
                defect.closed_at = None
        
        await self.db.commit()
        await self.db.refresh(defect)
        logger.info(f"Updated defect {defect_id}")
        return defect
    
    async def delete_defect(self, defect_id: uuid.UUID) -> bool:
        """Delete a defect.
        
        Args:
            defect_id: Defect ID
            
        Returns:
            True if deleted, False if not found
        """
        defect = await self.get_defect_by_id(defect_id)
        if not defect:
            return False
        
        await self.db.delete(defect)
        await self.db.commit()
        logger.info(f"Deleted defect {defect_id}")
        return True
