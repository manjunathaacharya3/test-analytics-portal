from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProjectOverviewResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    repository_url: Optional[str] = None
    owner: str

    # 🔹 Extra fields
    total_tests: int
    pass_rate: float
    last_status: Optional[str] = None
    last_run: Optional[datetime] = None
    modules: int

    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        orm_mode = True
