"""Pydantic schemas for Project and Module."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """Base schema for Project."""
    
    name: str = Field(..., min_length=3, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    repository_url: Optional[str] = Field(None, max_length=500, description="Repository URL")
    owner: str = Field(..., description="Project owner email")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    repository_url: Optional[str] = Field(None, max_length=500)
    owner: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True  # Pydantic v2 syntax (replaces orm_mode)


class ProjectOverviewResponse(ProjectResponse):
    """Schema for project overview with aggregated metrics."""
    
    modules: int = Field(0, description="Number of modules")
    total_tests: int = Field(0, description="Total number of tests")
    pass_rate: float = Field(0.0, description="Overall pass rate percentage")
    last_status: Optional[str] = Field(None, description="Status of last execution")
    last_run: Optional[datetime] = Field(None, description="Timestamp of last execution")


class ModuleBase(BaseModel):
    """Base schema for Module."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Module name")
    description: Optional[str] = Field(None, description="Module description")


class ModuleCreate(ModuleBase):
    """Schema for creating a new module."""
    
    is_active: Optional[bool] = Field(True, description="Module active status")


class ModuleUpdate(BaseModel):
    """Schema for updating a module."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ModuleResponse(ModuleBase):
    """Schema for module response."""
    
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
