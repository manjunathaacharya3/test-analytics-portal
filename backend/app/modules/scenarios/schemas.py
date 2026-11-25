"""Pydantic schemas for scenario filtering and responses."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ScenarioFilter(BaseModel):
    """Schema for scenario filtering."""
    
    status: Optional[str] = None
    feature: Optional[str] = None
    tags: Optional[str] = None
    search: Optional[str] = Field(None, description="Search in scenario name or error message")


class ScenarioResponse(BaseModel):
    """Schema for scenario response."""
    
    id: uuid.UUID
    report_id: uuid.UUID
    name: str
    status: str
    duration: Optional[float] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    tags: Optional[str] = None
    feature: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ScenarioListResponse(BaseModel):
    """Schema for paginated scenario list response."""
    
    scenarios: list[ScenarioResponse]
    total: int
    page: int
    size: int
    pages: int


class FailedScenarioResponse(BaseModel):
    """Schema for a failed scenario enriched with project/module context.

    Used by the AI Insights / Failure Analysis page to display real failed
    scenarios instead of mock data. No AI-generated fields (confidence,
    root cause, similar failures, suggested fix) are included since there
    is no AI/ML backend producing that data.
    """

    id: uuid.UUID
    name: str
    status: str
    duration: Optional[float] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    feature: Optional[str] = None
    created_at: datetime
    project_id: uuid.UUID
    project_name: str
    module_id: uuid.UUID
    module_name: str

    class Config:
        from_attributes = True


class FailedScenarioListResponse(BaseModel):
    """Schema for paginated failed scenario list response."""

    scenarios: list[FailedScenarioResponse]
    total: int
    page: int
    size: int
    pages: int
