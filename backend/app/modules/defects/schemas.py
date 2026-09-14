"""Pydantic schemas for defect management."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.modules.defects.models import DefectSeverity, DefectPriority, DefectStatus


class DefectBase(BaseModel):
    """Base defect schema."""
    
    title: str = Field(..., min_length=1, max_length=500, description="Defect title")
    description: str = Field(..., min_length=1, description="Detailed defect description")
    severity: str = Field(..., description="Defect severity: Critical, High, Medium, Low")
    priority: str = Field(..., description="Defect priority: P0, P1, P2, P3")
    assigned_to: Optional[str] = Field(None, max_length=255, description="User assigned to fix the defect")
    module_id: Optional[uuid.UUID] = Field(None, description="Module ID where defect was found")
    scenario_id: Optional[uuid.UUID] = Field(None, description="Scenario ID where defect was found")
    resolution: Optional[str] = Field(None, description="Resolution details")
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity value."""
        if not DefectSeverity.is_valid(v):
            raise ValueError(
                f"Invalid severity '{v}'. Must be one of: {', '.join(DefectSeverity.all())}"
            )
        return v
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority value."""
        if not DefectPriority.is_valid(v):
            raise ValueError(
                f"Invalid priority '{v}'. Must be one of: {', '.join(DefectPriority.all())}"
            )
        return v


class DefectCreate(DefectBase):
    """Schema for creating a defect."""
    
    project_id: uuid.UUID = Field(..., description="Project ID")
    reported_by: str = Field(..., max_length=255, description="User who reported the defect")
    status: str = Field(default="Open", description="Initial defect status")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        if not DefectStatus.is_valid(v):
            raise ValueError(
                f"Invalid status '{v}'. Must be one of: {', '.join(DefectStatus.all())}"
            )
        return v


class DefectUpdate(BaseModel):
    """Schema for updating a defect."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, min_length=1)
    severity: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = Field(None, max_length=255)
    module_id: Optional[uuid.UUID] = None
    scenario_id: Optional[uuid.UUID] = None
    resolution: Optional[str] = None
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v: Optional[str]) -> Optional[str]:
        """Validate severity value if provided."""
        if v is not None and not DefectSeverity.is_valid(v):
            raise ValueError(
                f"Invalid severity '{v}'. Must be one of: {', '.join(DefectSeverity.all())}"
            )
        return v
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority value if provided."""
        if v is not None and not DefectPriority.is_valid(v):
            raise ValueError(
                f"Invalid priority '{v}'. Must be one of: {', '.join(DefectPriority.all())}"
            )
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status value if provided."""
        if v is not None and not DefectStatus.is_valid(v):
            raise ValueError(
                f"Invalid status '{v}'. Must be one of: {', '.join(DefectStatus.all())}"
            )
        return v


class DefectResponse(DefectBase):
    """Schema for defect response."""
    
    id: uuid.UUID
    project_id: uuid.UUID
    reported_by: str
    status: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DefectStatusUpdate(BaseModel):
    """Schema for updating defect status."""
    
    status: str = Field(..., description="New status")
    resolution: Optional[str] = Field(None, description="Resolution details (required for Fixed/Closed/Won't Fix)")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        if not DefectStatus.is_valid(v):
            raise ValueError(
                f"Invalid status '{v}'. Must be one of: {', '.join(DefectStatus.all())}"
            )
        return v


class DefectAssignment(BaseModel):
    """Schema for assigning a defect."""
    
    assigned_to: str = Field(..., max_length=255, description="User to assign the defect to")


class DefectListResponse(BaseModel):
    """Schema for paginated defect list response."""
    
    defects: list[DefectResponse]
    total: int
    page: int
    size: int
    total_pages: int
