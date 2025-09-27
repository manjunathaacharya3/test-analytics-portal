from datetime import datetime

from pydantic import BaseModel


class ProjectInfo(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class ModuleInfo(BaseModel):
    id: str
    name: str
    project: ProjectInfo  # Nested project info

    class Config:
        orm_mode = True


class ExecutionSummaryResponse(BaseModel):
    id: str
    module_id: str
    module_name: str
    passed: int
    failed: int
    total: int
    duration: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


from pydantic import BaseModel
from typing import List, Optional


class ScenarioResponse(BaseModel):
    id: str  # Unique ID of the scenario
    scenario: str  # Scenario name/title
    tags: List[str] = []  # List of tags associated with the scenario
    duration: Optional[str] = None  # Duration as a string, e.g., "5m"
    status: str  # Status: "Passed", "❌ Failed", etc.
    failed_step: Optional[str] = None  # Name of failed step (if any)
    error: Optional[str] = None  # Error/stack trace for failed step
    attachments: Optional[List[str]] = []  # List of attachment filenames or URLs
