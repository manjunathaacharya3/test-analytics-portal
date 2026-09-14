"""Unit tests for defects module."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.modules.defects.models import (
    Defect,
    DefectSeverity,
    DefectPriority,
    DefectStatus,
)
from app.modules.defects.schemas import (
    DefectCreate,
    DefectUpdate,
    DefectResponse,
    DefectStatusUpdate,
    DefectAssignment,
)
from app.modules.defects.service import DefectService
from app.modules.defects.repository import DefectRepository


class TestDefectConstants:
    """Test defect constant classes."""
    
    def test_severity_constants(self):
        """Test DefectSeverity constants."""
        assert DefectSeverity.CRITICAL == "Critical"
        assert DefectSeverity.HIGH == "High"
        assert DefectSeverity.MEDIUM == "Medium"
        assert DefectSeverity.LOW == "Low"
    
    def test_severity_all(self):
        """Test DefectSeverity.all() returns all severities."""
        severities = DefectSeverity.all()
        assert len(severities) == 4
        assert "Critical" in severities
        assert "High" in severities
        assert "Medium" in severities
        assert "Low" in severities
    
    def test_severity_is_valid(self):
        """Test DefectSeverity.is_valid() validation."""
        assert DefectSeverity.is_valid("Critical") is True
        assert DefectSeverity.is_valid("High") is True
        assert DefectSeverity.is_valid("Invalid") is False
    
    def test_priority_constants(self):
        """Test DefectPriority constants."""
        assert DefectPriority.P0 == "P0"
        assert DefectPriority.P1 == "P1"
        assert DefectPriority.P2 == "P2"
        assert DefectPriority.P3 == "P3"
    
    def test_priority_all(self):
        """Test DefectPriority.all() returns all priorities."""
        priorities = DefectPriority.all()
        assert len(priorities) == 4
        assert "P0" in priorities
        assert "P1" in priorities
        assert "P2" in priorities
        assert "P3" in priorities
    
    def test_priority_is_valid(self):
        """Test DefectPriority.is_valid() validation."""
        assert DefectPriority.is_valid("P0") is True
        assert DefectPriority.is_valid("P3") is True
        assert DefectPriority.is_valid("P5") is False
    
    def test_status_constants(self):
        """Test DefectStatus constants."""
        assert DefectStatus.OPEN == "Open"
        assert DefectStatus.IN_PROGRESS == "In Progress"
        assert DefectStatus.FIXED == "Fixed"
        assert DefectStatus.CLOSED == "Closed"
        assert DefectStatus.WONT_FIX == "Won't Fix"
    
    def test_status_all(self):
        """Test DefectStatus.all() returns all statuses."""
        statuses = DefectStatus.all()
        assert len(statuses) == 5
        assert "Open" in statuses
        assert "In Progress" in statuses
        assert "Fixed" in statuses
        assert "Closed" in statuses
        assert "Won't Fix" in statuses
    
    def test_status_is_valid(self):
        """Test DefectStatus.is_valid() validation."""
        assert DefectStatus.is_valid("Open") is True
        assert DefectStatus.is_valid("Closed") is True
        assert DefectStatus.is_valid("Invalid") is False
    
    def test_status_valid_transitions(self):
        """Test DefectStatus.valid_transitions() returns correct transitions."""
        transitions = DefectStatus.valid_transitions()
        
        # Test Open transitions
        assert "In Progress" in transitions["Open"]
        assert "Won't Fix" in transitions["Open"]
        assert "Closed" in transitions["Open"]
        
        # Test In Progress transitions
        assert "Fixed" in transitions["In Progress"]
        assert "Open" in transitions["In Progress"]
        assert "Won't Fix" in transitions["In Progress"]
        
        # Test Fixed transitions
        assert "Closed" in transitions["Fixed"]
        assert "Open" in transitions["Fixed"]
    
    def test_status_can_transition(self):
        """Test DefectStatus.can_transition() validation."""
        # Valid transitions
        assert DefectStatus.can_transition("Open", "In Progress") is True
        assert DefectStatus.can_transition("In Progress", "Fixed") is True
        assert DefectStatus.can_transition("Fixed", "Closed") is True
        
        # Invalid transitions
        assert DefectStatus.can_transition("Open", "Fixed") is False
        assert DefectStatus.can_transition("Closed", "Fixed") is False
        assert DefectStatus.can_transition("Won't Fix", "Fixed") is False


class TestDefectSchemas:
    """Test defect Pydantic schemas."""
    
    def test_defect_create_schema(self):
        """Test DefectCreate schema validation."""
        defect_data = DefectCreate(
            title="Test defect",
            description="Test description",
            severity="High",
            priority="P1",
            project_id="project-123",
            reported_by="test@example.com",
            status="Open"
        )
        
        assert defect_data.title == "Test defect"
        assert defect_data.severity == "High"
        assert defect_data.priority == "P1"
        assert defect_data.status == "Open"
    
    def test_defect_create_invalid_severity(self):
        """Test DefectCreate schema rejects invalid severity."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError) as exc_info:
            DefectCreate(
                title="Test defect",
                description="Test description",
                severity="Invalid",
                priority="P1",
                project_id="project-123",
                reported_by="test@example.com"
            )
        
        assert "Invalid severity" in str(exc_info.value)
    
    def test_defect_create_invalid_priority(self):
        """Test DefectCreate schema rejects invalid priority."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError) as exc_info:
            DefectCreate(
                title="Test defect",
                description="Test description",
                severity="High",
                priority="P5",
                project_id="project-123",
                reported_by="test@example.com"
            )
        
        assert "Invalid priority" in str(exc_info.value)
    
    def test_defect_create_invalid_status(self):
        """Test DefectCreate schema rejects invalid status."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError) as exc_info:
            DefectCreate(
                title="Test defect",
                description="Test description",
                severity="High",
                priority="P1",
                project_id="project-123",
                reported_by="test@example.com",
                status="Invalid"
            )
        
        assert "Invalid status" in str(exc_info.value)
    
    def test_defect_update_schema(self):
        """Test DefectUpdate schema."""
        update_data = DefectUpdate(
            title="Updated title",
            severity="Critical",
            status="In Progress"
        )
        
        assert update_data.title == "Updated title"
        assert update_data.severity == "Critical"
        assert update_data.status == "In Progress"
    
    def test_defect_status_update_schema(self):
        """Test DefectStatusUpdate schema."""
        status_update = DefectStatusUpdate(
            status="Fixed",
            resolution="Fixed by updating the code"
        )
        
        assert status_update.status == "Fixed"
        assert status_update.resolution == "Fixed by updating the code"
    
    def test_defect_assignment_schema(self):
        """Test DefectAssignment schema."""
        assignment = DefectAssignment(assigned_to="developer@example.com")
        
        assert assignment.assigned_to == "developer@example.com"


@pytest.mark.asyncio
class TestDefectRepository:
    """Test DefectRepository methods."""
    
    async def test_create_defect(self):
        """Test creating a defect."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        repository = DefectRepository(db)
        
        # Mock defect data
        defect_data = {
            "title": "Test defect",
            "description": "Test description",
            "severity": "High",
            "priority": "P1",
            "status": "Open",
            "project_id": "project-123",
            "reported_by": "test@example.com"
        }
        
        # Create defect
        defect = await repository.create_defect(defect_data)
        
        # Verify database operations
        assert db.add.called
        assert db.commit.called
        assert db.refresh.called
        assert defect.title == "Test defect"
    
    async def test_get_defect_by_id(self):
        """Test getting defect by ID."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        repository = DefectRepository(db)
        
        # Mock defect
        defect_id = uuid.uuid4()
        mock_defect = Defect(
            id=defect_id,
            title="Test defect",
            description="Test description",
            severity="High",
            priority="P1",
            status="Open",
            project_id="project-123",
            reported_by="test@example.com"
        )
        
        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_defect
        db.execute.return_value = mock_result
        
        # Get defect
        result = await repository.get_defect_by_id(defect_id)
        
        # Verify
        assert result == mock_defect
        assert db.execute.called


@pytest.mark.asyncio
class TestDefectService:
    """Test DefectService methods."""
    
    async def test_create_defect_success(self):
        """Test successful defect creation."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        service = DefectService(db)
        
        # Mock repository
        mock_defect = Defect(
            id=uuid.uuid4(),
            title="Test defect",
            description="Test description",
            severity="High",
            priority="P1",
            status="Open",
            project_id="project-123",
            reported_by="test@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        service.repository.create_defect = AsyncMock(return_value=mock_defect)
        
        # Create defect
        defect_data = DefectCreate(
            title="Test defect",
            description="Test description",
            severity="High",
            priority="P1",
            project_id="project-123",
            reported_by="test@example.com"
        )
        
        result = await service.create_defect(defect_data)
        
        # Verify
        assert result.title == "Test defect"
        assert result.severity == "High"
        assert service.repository.create_defect.called
    
    async def test_get_defect_not_found(self):
        """Test getting non-existent defect raises NotFoundError."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        service = DefectService(db)
        
        # Mock repository to return None
        service.repository.get_defect_by_id = AsyncMock(return_value=None)
        
        # Attempt to get defect
        with pytest.raises(NotFoundError):
            await service.get_defect(uuid.uuid4())
    
    async def test_update_defect_status_invalid_transition(self):
        """Test updating defect status with invalid transition raises ConflictError."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        service = DefectService(db)
        
        # Mock existing defect with status "Open"
        mock_defect = Defect(
            id=uuid.uuid4(),
            title="Test defect",
            description="Test description",
            severity="High",
            priority="P1",
            status="Open",
            project_id="project-123",
            reported_by="test@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        service.repository.get_defect_by_id = AsyncMock(return_value=mock_defect)
        
        # Attempt invalid transition from "Open" to "Fixed" (should go through "In Progress" first)
        status_update = DefectStatusUpdate(status="Fixed", resolution="Test resolution")
        
        with pytest.raises(ConflictError) as exc_info:
            await service.update_defect_status(mock_defect.id, status_update)
        
        assert "Invalid status transition" in str(exc_info.value.message)
    
    async def test_update_defect_status_valid_transition(self):
        """Test updating defect status with valid transition."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        service = DefectService(db)
        
        # Mock existing defect
        defect_id = uuid.uuid4()
        mock_defect = Defect(
            id=defect_id,
            title="Test defect",
            description="Test description",
            severity="High",
            priority="P1",
            status="Open",
            project_id="project-123",
            reported_by="test@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock updated defect
        updated_defect = Defect(
            id=defect_id,
            title="Test defect",
            description="Test description",
            severity="High",
            priority="P1",
            status="In Progress",
            project_id="project-123",
            reported_by="test@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        service.repository.get_defect_by_id = AsyncMock(return_value=mock_defect)
        service.repository.update_defect = AsyncMock(return_value=updated_defect)
        
        # Valid transition from "Open" to "In Progress"
        status_update = DefectStatusUpdate(status="In Progress")
        result = await service.update_defect_status(defect_id, status_update)
        
        # Verify
        assert result.status == "In Progress"
        assert service.repository.update_defect.called
    
    async def test_assign_defect_success(self):
        """Test successful defect assignment."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        service = DefectService(db)
        
        # Mock existing defect
        defect_id = uuid.uuid4()
        mock_defect = Defect(
            id=defect_id,
            title="Test defect",
            description="Test description",
            severity="High",
            priority="P1",
            status="Open",
            project_id="project-123",
            reported_by="test@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock updated defect with assignment
        updated_defect = Defect(
            id=defect_id,
            title="Test defect",
            description="Test description",
            severity="High",
            priority="P1",
            status="Open",
            assigned_to="developer@example.com",
            project_id="project-123",
            reported_by="test@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        service.repository.get_defect_by_id = AsyncMock(return_value=mock_defect)
        service.repository.update_defect = AsyncMock(return_value=updated_defect)
        
        # Assign defect
        assignment = DefectAssignment(assigned_to="developer@example.com")
        result = await service.assign_defect(defect_id, assignment)
        
        # Verify
        assert result.assigned_to == "developer@example.com"
        assert service.repository.update_defect.called
    
    async def test_delete_defect_not_found(self):
        """Test deleting non-existent defect raises NotFoundError."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        service = DefectService(db)
        
        # Mock repository to return False (not found)
        service.repository.delete_defect = AsyncMock(return_value=False)
        
        # Attempt to delete defect
        with pytest.raises(NotFoundError):
            await service.delete_defect(uuid.uuid4())
