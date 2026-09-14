"""Defect model for defect management."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Defect(Base):
    """Defect model for tracking bugs and issues."""
    
    __tablename__ = "defects"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Open",
        index=True
    )
    assigned_to: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )
    reported_by: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    module_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    scenario_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Defect(id={self.id}, title={self.title}, status={self.status}, severity={self.severity})>"


class DefectSeverity:
    """Defect severity constants."""
    
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    
    @classmethod
    def all(cls) -> list[str]:
        """Get all available severity levels."""
        return [cls.CRITICAL, cls.HIGH, cls.MEDIUM, cls.LOW]
    
    @classmethod
    def is_valid(cls, severity: str) -> bool:
        """Check if a severity is valid."""
        return severity in cls.all()


class DefectPriority:
    """Defect priority constants."""
    
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    
    @classmethod
    def all(cls) -> list[str]:
        """Get all available priority levels."""
        return [cls.P0, cls.P1, cls.P2, cls.P3]
    
    @classmethod
    def is_valid(cls, priority: str) -> bool:
        """Check if a priority is valid."""
        return priority in cls.all()


class DefectStatus:
    """Defect status constants."""
    
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    FIXED = "Fixed"
    CLOSED = "Closed"
    WONT_FIX = "Won't Fix"
    
    @classmethod
    def all(cls) -> list[str]:
        """Get all available status values."""
        return [cls.OPEN, cls.IN_PROGRESS, cls.FIXED, cls.CLOSED, cls.WONT_FIX]
    
    @classmethod
    def is_valid(cls, status: str) -> bool:
        """Check if a status is valid."""
        return status in cls.all()
    
    @classmethod
    def valid_transitions(cls) -> dict[str, list[str]]:
        """Get valid status transitions."""
        return {
            cls.OPEN: [cls.IN_PROGRESS, cls.WONT_FIX, cls.CLOSED],
            cls.IN_PROGRESS: [cls.FIXED, cls.OPEN, cls.WONT_FIX],
            cls.FIXED: [cls.CLOSED, cls.OPEN],
            cls.CLOSED: [cls.OPEN],
            cls.WONT_FIX: [cls.OPEN],
        }
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """Check if a status transition is valid."""
        if from_status not in cls.valid_transitions():
            return False
        return to_status in cls.valid_transitions()[from_status]
