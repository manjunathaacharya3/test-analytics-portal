"""Pydantic schemas for execution endpoints."""
import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ExecutionBase(BaseModel):
    """Base execution schema."""
    
    file_name: str
    file_size: int
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    skipped_scenarios: int
    duration: Optional[float] = None
    uploaded_by: str


class ExecutionResponse(ExecutionBase):
    """Schema for execution response."""
    
    id: uuid.UUID
    project_id: uuid.UUID
    module_id: uuid.UUID
    module_name: Optional[str] = Field(None, description="Module name (if module exists)")
    created_at: datetime
    pass_rate: float = Field(description="Pass rate percentage (0-100)")
    status: str = Field(description="Execution status: passed, failed, or mixed")
    
    class Config:
        from_attributes = True


class ExecutionListResponse(BaseModel):
    """Schema for paginated execution list response."""
    
    executions: List[ExecutionResponse]
    total: int
    page: int
    size: int
    total_pages: int


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


class ScenarioListResponse(BaseModel):
    """Schema for paginated scenario list response."""
    
    scenarios: List[ScenarioResponse]
    total: int
    page: int
    size: int
    total_pages: int


class ExecutionDetailResponse(ExecutionResponse):
    """Schema for detailed execution response with scenarios."""
    
    scenarios: List[ScenarioResponse] = []
