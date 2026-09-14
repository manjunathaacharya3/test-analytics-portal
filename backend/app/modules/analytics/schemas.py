"""Pydantic schemas for analytics responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    """Schema for dashboard metrics."""
    
    total_projects: int
    total_executions: int
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    skipped_scenarios: int
    pass_rate: float
    avg_duration: Optional[float] = None


class TrendDataPoint(BaseModel):
    """Schema for a single trend data point."""
    
    date: datetime
    pass_rate: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    duration: Optional[float] = None


class TrendResponse(BaseModel):
    """Schema for trend analysis response."""
    
    data_points: list[TrendDataPoint]
    period: str  # daily, weekly, monthly


class AnalyticsResponse(BaseModel):
    """Schema for analytics response."""
    
    metrics: DashboardMetrics
    trends: Optional[TrendResponse] = None
