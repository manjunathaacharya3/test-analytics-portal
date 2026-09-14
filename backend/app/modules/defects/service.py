"""Business logic for defect management."""
import uuid
import logging
from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.defects.repository import DefectRepository
from app.modules.defects.models import Defect, DefectStatus
from app.modules.defects.schemas import (
    DefectCreate,
    DefectUpdate,
    DefectResponse,
    DefectStatusUpdate,
    DefectAssignment,
)
from app.core.exceptions import NotFoundError, ConflictError

logger = logging.getLogger(__name__)


class DefectService:
    """Service layer for defect management."""
    
    def __init__(self, db: AsyncSession):
        """Initialize service with database session.
        
        Args:
            db: Async database session
        """
        self.repository = DefectRepository(db)
        self.db = db
    
    async def create_defect(self, defect_data: DefectCreate) -> DefectResponse:
        """Create a new defect.
        
        Args:
            defect_data: Defect creation data
            
        Returns:
            Created defect
        """
        # Convert to dict and create
        defect_dict = defect_data.model_dump()
        defect = await self.repository.create_defect(defect_dict)
        
        logger.info(
            f"Created defect {defect.id}: {defect.title} "
            f"(severity={defect.severity}, status={defect.status})"
        )
        
        return DefectResponse.model_validate(defect)
    
    async def get_defect(self, defect_id: uuid.UUID) -> DefectResponse:
        """Get defect by ID.
        
        Args:
            defect_id: Defect ID
            
        Returns:
            Defect data
            
        Raises:
            NotFoundError: If defect not found
        """
        defect = await self.repository.get_defect_by_id(defect_id)
        if not defect:
            raise NotFoundError(f"Defect with ID {defect_id} not found")
        
        return DefectResponse.model_validate(defect)
    
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
    ) -> tuple[List[DefectResponse], int]:
        """Get defects with filtering.
        
        Args:
            project_id: Filter by project ID
            module_id: Filter by module ID
            status: Filter by status
            severity: Filter by severity
            priority: Filter by priority
            assigned_to: Filter by assigned user
            page: Page number
            size: Page size
            
        Returns:
            Tuple of (list of defects, total count)
        """
        defects, total = await self.repository.get_defects(
            project_id=project_id,
            module_id=module_id,
            status=status,
            severity=severity,
            priority=priority,
            assigned_to=assigned_to,
            page=page,
            size=size
        )
        
        return [
            DefectResponse.model_validate(defect) for defect in defects
        ], total
    
    async def get_defects_by_scenario(
        self,
        scenario_id: uuid.UUID,
        page: int = 1,
        size: int = 20
    ) -> List[DefectResponse]:
        """Get defects linked to a scenario.
        
        Args:
            scenario_id: Scenario ID
            page: Page number
            size: Page size
            
        Returns:
            List of defects
        """
        defects = await self.repository.get_defects_by_scenario(
            scenario_id=scenario_id,
            page=page,
            size=size
        )
        
        return [DefectResponse.model_validate(defect) for defect in defects]
    
    async def update_defect(
        self,
        defect_id: uuid.UUID,
        update_data: DefectUpdate
    ) -> DefectResponse:
        """Update a defect.
        
        Args:
            defect_id: Defect ID
            update_data: Update data
            
        Returns:
            Updated defect
            
        Raises:
            NotFoundError: If defect not found
            ConflictError: If status transition is invalid
        """
        # Check if defect exists
        existing_defect = await self.repository.get_defect_by_id(defect_id)
        if not existing_defect:
            raise NotFoundError(f"Defect with ID {defect_id} not found")
        
        # Validate status transition if status is being updated
        update_dict = update_data.model_dump(exclude_unset=True)
        if 'status' in update_dict:
            new_status = update_dict['status']
            current_status = existing_defect.status
            
            if not DefectStatus.can_transition(current_status, new_status):
                raise ConflictError(
                    f"Invalid status transition from '{current_status}' to '{new_status}'"
                )
        
        # Update defect
        updated_defect = await self.repository.update_defect(defect_id, update_dict)
        
        logger.info(f"Updated defect {defect_id}")
        return DefectResponse.model_validate(updated_defect)
    
    async def update_defect_status(
        self,
        defect_id: uuid.UUID,
        status_update: DefectStatusUpdate
    ) -> DefectResponse:
        """Update defect status with validation.
        
        Args:
            defect_id: Defect ID
            status_update: Status update data
            
        Returns:
            Updated defect
            
        Raises:
            NotFoundError: If defect not found
            ConflictError: If status transition is invalid
        """
        # Check if defect exists
        existing_defect = await self.repository.get_defect_by_id(defect_id)
        if not existing_defect:
            raise NotFoundError(f"Defect with ID {defect_id} not found")
        
        # Validate status transition
        current_status = existing_defect.status
        new_status = status_update.status
        
        if not DefectStatus.can_transition(current_status, new_status):
            raise ConflictError(
                f"Invalid status transition from '{current_status}' to '{new_status}'. "
                f"Valid transitions: {', '.join(DefectStatus.valid_transitions().get(current_status, []))}"
            )
        
        # Prepare update data
        update_dict = {'status': new_status}
        if status_update.resolution:
            update_dict['resolution'] = status_update.resolution
        
        # Update defect
        updated_defect = await self.repository.update_defect(defect_id, update_dict)
        
        logger.info(
            f"Updated defect {defect_id} status: {current_status} -> {new_status}"
        )
        return DefectResponse.model_validate(updated_defect)
    
    async def assign_defect(
        self,
        defect_id: uuid.UUID,
        assignment: DefectAssignment
    ) -> DefectResponse:
        """Assign a defect to a user.
        
        Args:
            defect_id: Defect ID
            assignment: Assignment data
            
        Returns:
            Updated defect
            
        Raises:
            NotFoundError: If defect not found
        """
        # Check if defect exists
        existing_defect = await self.repository.get_defect_by_id(defect_id)
        if not existing_defect:
            raise NotFoundError(f"Defect with ID {defect_id} not found")
        
        # Update assignment
        update_dict = {'assigned_to': assignment.assigned_to}
        updated_defect = await self.repository.update_defect(defect_id, update_dict)
        
        logger.info(
            f"Assigned defect {defect_id} to {assignment.assigned_to}"
        )
        return DefectResponse.model_validate(updated_defect)
    
    async def delete_defect(self, defect_id: uuid.UUID) -> None:
        """Delete a defect.
        
        Args:
            defect_id: Defect ID
            
        Raises:
            NotFoundError: If defect not found
        """
        deleted = await self.repository.delete_defect(defect_id)
        if not deleted:
            raise NotFoundError(f"Defect with ID {defect_id} not found")
        
        logger.info(f"Deleted defect {defect_id}")
