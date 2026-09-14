"""Analytics API endpoints for dashboard and trends."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.modules.analytics.schemas import (
    AnalyticsResponse,
    DashboardMetrics,
    TrendDataPoint,
    TrendResponse,
)
from app.modules.auth.models import User
from app.modules.reports.models import Report, Scenario

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/dashboard",
    response_model=DashboardMetrics,
    summary="Get dashboard metrics",
    description="Get aggregated metrics for the dashboard. Public endpoint (no auth required)."
)
async def get_dashboard_metrics(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user)  # Removed for public access
) -> DashboardMetrics:
    """Get dashboard metrics.
    
    Args:
        project_id: Optional project ID filter
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dashboard metrics
    """
    from app.projects.models import Project
    
    # Count projects
    project_query = select(func.count(Project.id))
    if project_id:
        project_query = project_query.where(Project.id == project_id)
    project_result = await db.execute(project_query)
    total_projects = project_result.scalar()
    
    # Count reports (executions)
    report_query = select(func.count(Report.id))
    if project_id:
        report_query = report_query.where(Report.project_id == project_id)
    report_result = await db.execute(report_query)
    total_executions = report_result.scalar()
    
    # Aggregate scenario statistics
    from sqlalchemy import case
    scenario_query = select(
        func.count(Scenario.id).label("total"),
        func.sum(case((Scenario.status == "passed", 1), else_=0)).label("passed"),
        func.sum(case((Scenario.status == "failed", 1), else_=0)).label("failed"),
        func.sum(case((Scenario.status == "skipped", 1), else_=0)).label("skipped"),
        func.avg(Scenario.duration).label("avg_duration"),
    )
    
    if project_id:
        scenario_query = scenario_query.join(Report).where(Report.project_id == project_id)
    
    scenario_result = await db.execute(scenario_query)
    stats = scenario_result.one()
    
    total_scenarios = stats.total or 0
    passed_scenarios = stats.passed or 0
    failed_scenarios = stats.failed or 0
    skipped_scenarios = stats.skipped or 0
    avg_duration = stats.avg_duration
    
    # Calculate pass rate
    pass_rate = (passed_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0.0
    
    return DashboardMetrics(
        total_projects=total_projects,
        total_executions=total_executions,
        total_scenarios=total_scenarios,
        passed_scenarios=passed_scenarios,
        failed_scenarios=failed_scenarios,
        skipped_scenarios=skipped_scenarios,
        pass_rate=round(pass_rate, 2),
        avg_duration=round(avg_duration, 2) if avg_duration else None,
    )


@router.get(
    "/trends",
    response_model=TrendResponse,
    summary="Get trend analysis",
    description="Get trend data for pass rate and test counts over time. Public endpoint (no auth required)."
)
async def get_trends(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
    # current_user: User = Depends(get_current_user)  # Removed for public access
) -> TrendResponse:
    """Get trend analysis.
    
    Args:
        project_id: Optional project ID filter
        days: Number of days to analyze
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Trend analysis data
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Query reports grouped by date
    query = select(
        func.date(Report.created_at).label("date"),
        func.sum(Report.total_scenarios).label("total_tests"),
        func.sum(Report.passed_scenarios).label("passed_tests"),
        func.sum(Report.failed_scenarios).label("failed_tests"),
        func.avg(Report.duration).label("avg_duration"),
    ).where(
        Report.created_at >= start_date
    ).group_by(
        func.date(Report.created_at)
    ).order_by(
        func.date(Report.created_at)
    )
    
    if project_id:
        query = query.where(Report.project_id == project_id)
    
    result = await db.execute(query)
    rows = result.all()
    
    # Build data points
    data_points = []
    for row in rows:
        total = row.total_tests or 0
        passed = row.passed_tests or 0
        pass_rate = (passed / total * 100) if total > 0 else 0.0
        
        data_points.append(
            TrendDataPoint(
                date=row.date,
                pass_rate=round(pass_rate, 2),
                total_tests=total,
                passed_tests=passed,
                failed_tests=row.failed_tests or 0,
                duration=round(row.avg_duration, 2) if row.avg_duration else None,
            )
        )
    
    return TrendResponse(
        data_points=data_points,
        period="daily"
    )
