"""Pydantic schemas for report upload and processing."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ScenarioBase(BaseModel):
    """Base scenario schema."""
    
    name: str
    status: str
    duration: Optional[float] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    tags: Optional[str] = None
    feature: Optional[str] = None


class ScenarioResponse(ScenarioBase):
    """Schema for scenario response."""
    
    id: uuid.UUID
    report_id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReportBase(BaseModel):
    """Base report schema."""
    
    file_name: str
    file_size: int
    total_scenarios: int = 0
    passed_scenarios: int = 0
    failed_scenarios: int = 0
    skipped_scenarios: int = 0
    duration: Optional[float] = None


class ReportCreate(ReportBase):
    """Schema for report creation."""
    
    project_id: uuid.UUID
    module_id: uuid.UUID
    uploaded_by: str


class ReportResponse(ReportBase):
    """Schema for report response."""
    
    id: uuid.UUID
    project_id: uuid.UUID
    module_id: uuid.UUID
    uploaded_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReportWithScenarios(ReportResponse):
    """Schema for report with scenarios."""
    
    scenarios: list[ScenarioResponse] = []


class UploadTaskStatus(BaseModel):
    """Schema for upload task status."""
    
    task_id: str
    status: str = Field(..., description="Status: processing, completed, failed")
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    result: Optional[dict] = None
    error: Optional[str] = None


class UploadResponse(BaseModel):
    """Schema for upload response."""
    
    task_id: str
    status: str = "processing"
    message: str = "Report upload started"
