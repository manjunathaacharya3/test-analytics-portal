from typing import Any, Dict

from pydantic import BaseModel


class ReportRequest(BaseModel):
    project_name: str
    module_name: str
    cucumber_json: Dict[str, Any]  # raw cucumber JSON report


class ReportResponse(BaseModel):
    execution_id: str
    status: str
    pass_rate: float

    class Config:
        orm_mode = True
