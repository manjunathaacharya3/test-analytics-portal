"""Business logic for execution operations with Redis caching."""
import logging
import math
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.executions.repository import ExecutionRepository
from app.executions.schemas import (
    ExecutionResponse,
    ExecutionListResponse,
    ScenarioResponse,
    ScenarioListResponse,
    ExecutionDetailResponse
)
from app.executions.cache_config import (
    CACHE_TTL_CONFIG,
    get_execution_cache_key,
    get_execution_detail_cache_key,
    get_scenarios_cache_key
)
from app.core.cache import cache_service
from app.core.exceptions import NotFoundError
from app.modules.reports.models import Report, Scenario

logger = logging.getLogger(__name__)


class ExecutionService:
    """Service for execution operations with caching."""
    
    @staticmethod
    def _calculate_pass_rate(report: Report) -> float:
        """Calculate pass rate percentage.
        
        Args:
            report: Report instance
            
        Returns:
            Pass rate percentage (0-100)
        """
        if report.total_scenarios == 0:
            return 0.0
        return round((report.passed_scenarios / report.total_scenarios) * 100, 2)
    
    @staticmethod
    def _determine_status(report: Report) -> str:
        """Determine execution status based on scenario results.
        
        Args:
            report: Report instance
            
        Returns:
            Status string: 'passed', 'failed', or 'mixed'
        """
        if report.failed_scenarios > 0:
            return "failed"
        elif report.passed_scenarios == report.total_scenarios:
            return "passed"
        else:
            return "mixed"
    
    @staticmethod
    def _enrich_execution(report: Report) -> dict:
        """Enrich execution with calculated fields.
        
        Args:
            report: Report instance
            
        Returns:
            Dictionary with enriched execution data including module_name
        """
        enriched = {
            **report.__dict__,
            "pass_rate": ExecutionService._calculate_pass_rate(report),
            "status": ExecutionService._determine_status(report)
        }
        
        # Add module_name - use module name if available, otherwise None
        enriched["module_name"] = (
            report.module.name 
            if hasattr(report, 'module') and report.module 
            else None
        )
        
        return enriched
    
    @staticmethod
    async def get_execution_by_id(
        db: AsyncSession,
        execution_id: str,
        use_cache: bool = True
    ) -> ExecutionResponse:
        """Get execution by ID with caching.
        
        Args:
            db: Database session
            execution_id: Execution ID
            use_cache: Whether to use cache (default: True)
            
        Returns:
            ExecutionResponse
            
        Raises:
            NotFoundError: If execution not found
        """
        # Try cache first
        if use_cache:
            cache_key = get_execution_detail_cache_key(execution_id)
            cached_data = await cache_service.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for execution {execution_id}")
                return ExecutionResponse(**cached_data)
        
        # Cache miss - query database
        logger.debug(f"Cache miss for execution {execution_id}")
        repo = ExecutionRepository(db)
        report = await repo.get_by_id(execution_id)
        
        if not report:
            raise NotFoundError(f"Execution {execution_id} not found")
        
        enriched_data = ExecutionService._enrich_execution(report)
        response = ExecutionResponse(**enriched_data)
        
        # Store in cache
        if use_cache:
            await cache_service.set(
                cache_key,
                response.model_dump(),
                ttl=CACHE_TTL_CONFIG["execution:detail"]
            )
        
        return response
    
    @staticmethod
    async def get_executions_by_project(
        db: AsyncSession,
        project_id: str,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
        use_cache: bool = True
    ) -> ExecutionListResponse:
        """Get executions for a project with pagination and caching.
        
        Args:
            db: Database session
            project_id: Project ID
            page: Page number (1-indexed)
            size: Page size
            status: Optional status filter
            use_cache: Whether to use cache (default: True)
            
        Returns:
            ExecutionListResponse
        """
        # Try cache first
        if use_cache:
            cache_key = get_execution_cache_key(
                "executions:project",
                project_id,
                page,
                size,
                status
            )
            cached_data = await cache_service.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for project {project_id} executions")
                return ExecutionListResponse(**cached_data)
        
        # Cache miss - query database
        logger.debug(f"Cache miss for project {project_id} executions")
        repo = ExecutionRepository(db)
        reports = await repo.get_by_project(project_id, page, size, status)
        total = await repo.count_by_project(project_id)
        
        # Enrich executions
        enriched_executions = [
            ExecutionResponse(**ExecutionService._enrich_execution(report))
            for report in reports
        ]
        
        # Filter by status if provided (post-query filtering)
        if status:
            enriched_executions = [
                exec for exec in enriched_executions if exec.status == status
            ]
        
        total_pages = math.ceil(total / size) if total > 0 else 0
        
        response = ExecutionListResponse(
            executions=enriched_executions,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
        
        # Store in cache
        if use_cache:
            await cache_service.set(
                cache_key,
                response.model_dump(),
                ttl=CACHE_TTL_CONFIG["executions:project"]
            )
        
        return response
    
    @staticmethod
    async def get_executions_by_module(
        db: AsyncSession,
        module_id: str,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
        use_cache: bool = True
    ) -> ExecutionListResponse:
        """Get executions for a module with pagination and caching.
        
        Args:
            db: Database session
            module_id: Module ID
            page: Page number (1-indexed)
            size: Page size
            status: Optional status filter
            use_cache: Whether to use cache (default: True)
            
        Returns:
            ExecutionListResponse
        """
        # Try cache first
        if use_cache:
            cache_key = get_execution_cache_key(
                "executions:module",
                module_id,
                page,
                size,
                status
            )
            cached_data = await cache_service.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for module {module_id} executions")
                return ExecutionListResponse(**cached_data)
        
        # Cache miss - query database
        logger.debug(f"Cache miss for module {module_id} executions")
        repo = ExecutionRepository(db)
        reports = await repo.get_by_module(module_id, page, size, status)
        total = await repo.count_by_module(module_id)
        
        # Enrich executions
        enriched_executions = [
            ExecutionResponse(**ExecutionService._enrich_execution(report))
            for report in reports
        ]
        
        # Filter by status if provided (post-query filtering)
        if status:
            enriched_executions = [
                exec for exec in enriched_executions if exec.status == status
            ]
        
        total_pages = math.ceil(total / size) if total > 0 else 0
        
        response = ExecutionListResponse(
            executions=enriched_executions,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
        
        # Store in cache
        if use_cache:
            await cache_service.set(
                cache_key,
                response.model_dump(),
                ttl=CACHE_TTL_CONFIG["executions:module"]
            )
        
        return response
    
    @staticmethod
    async def get_scenarios_by_execution(
        db: AsyncSession,
        execution_id: str,
        page: int = 1,
        size: int = 50,
        status: Optional[str] = None,
        use_cache: bool = True
    ) -> ScenarioListResponse:
        """Get scenarios for an execution with pagination and caching.
        
        Args:
            db: Database session
            execution_id: Execution ID
            page: Page number (1-indexed)
            size: Page size
            status: Optional status filter
            use_cache: Whether to use cache (default: True)
            
        Returns:
            ScenarioListResponse
        """
        # Try cache first
        if use_cache:
            cache_key = get_scenarios_cache_key(execution_id, page, size, status)
            cached_data = await cache_service.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for execution {execution_id} scenarios")
                return ScenarioListResponse(**cached_data)
        
        # Cache miss - query database
        logger.debug(f"Cache miss for execution {execution_id} scenarios")
        repo = ExecutionRepository(db)
        scenarios = await repo.get_scenarios_by_execution(
            execution_id, page, size, status
        )
        total = await repo.count_scenarios_by_execution(execution_id, status)
        
        scenario_responses = [
            ScenarioResponse.model_validate(scenario)
            for scenario in scenarios
        ]
        
        total_pages = math.ceil(total / size) if total > 0 else 0
        
        response = ScenarioListResponse(
            scenarios=scenario_responses,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
        
        # Store in cache
        if use_cache:
            await cache_service.set(
                cache_key,
                response.model_dump(),
                ttl=CACHE_TTL_CONFIG["scenarios:execution"]
            )
        
        return response
    
    @staticmethod
    async def invalidate_execution_caches(
        project_id: Optional[str] = None,
        module_id: Optional[str] = None,
        execution_id: Optional[str] = None
    ) -> None:
        """Invalidate execution-related caches.
        
        Args:
            project_id: Optional project ID to invalidate project executions cache
            module_id: Optional module ID to invalidate module executions cache
            execution_id: Optional execution ID to invalidate execution detail cache
        """
        if project_id:
            pattern = f"executions:project:{project_id}:*"
            await cache_service.invalidate_pattern(pattern)
            logger.info(f"Invalidated cache for project {project_id} executions")
        
        if module_id:
            pattern = f"executions:module:{module_id}:*"
            await cache_service.invalidate_pattern(pattern)
            logger.info(f"Invalidated cache for module {module_id} executions")
        
        if execution_id:
            # Invalidate execution detail
            detail_key = get_execution_detail_cache_key(execution_id)
            await cache_service.delete(detail_key)
            
            # Invalidate scenarios
            pattern = f"scenarios:execution:{execution_id}:*"
            await cache_service.invalidate_pattern(pattern)
            logger.info(f"Invalidated cache for execution {execution_id}")
