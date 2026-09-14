"""Business logic for projects and modules."""
import uuid
import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.projects.models import Project, Module
from app.projects.repository import ProjectRepository
from app.projects.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectOverviewResponse,
    ModuleCreate,
    ModuleUpdate,
    ModuleResponse,
)
from app.core.cache import cache_service

logger = logging.getLogger(__name__)


class ProjectService:
    """Service layer for project business logic."""
    
    def __init__(self, db: AsyncSession):
        """Initialize service with database session.
        
        Args:
            db: Async database session
        """
        self.repository = ProjectRepository(db)
    
    async def create_project(self, project_data: ProjectCreate) -> ProjectResponse:
        """Create a new project and invalidate cache.
        
        Args:
            project_data: Project creation data
            
        Returns:
            Created project response
        """
        project_dict = project_data.model_dump()
        project_dict["id"] = str(uuid.uuid4())
        
        project = await self.repository.create(project_dict)
        
        # Invalidate projects list cache
        await cache_service.invalidate_pattern("projects:list:*")
        logger.debug("Invalidated projects list cache after creation")
        
        return ProjectResponse.model_validate(project)
    
    async def get_project(self, project_id: str) -> Optional[ProjectResponse]:
        """Get project by ID with Redis caching.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project response or None if not found
        """
        # Try to get from cache
        cache_key = f"project:{project_id}"
        cached_project = await cache_service.get(cache_key)
        if cached_project:
            logger.debug(f"Cache hit for project {project_id}")
            return ProjectResponse(**cached_project)
        
        # Cache miss - fetch from database
        logger.debug(f"Cache miss for project {project_id}")
        project = await self.repository.get_by_id(project_id)
        if not project:
            return None
        
        project_response = ProjectResponse.model_validate(project)
        
        # Store in cache (TTL: 10 minutes)
        await cache_service.set(cache_key, project_response.model_dump(), ttl=600)
        
        return project_response
    
    async def list_projects(
        self,
        page: int = 1,
        size: int = 20,
        is_active: Optional[bool] = None,
        owner: Optional[str] = None
    ) -> List[ProjectOverviewResponse]:
        """List all projects with aggregated metrics, pagination, and filtering with Redis caching.
        
        Args:
            page: Page number (1-indexed)
            size: Number of items per page
            is_active: Filter by active status
            owner: Filter by owner email
        
        Returns:
            List of project overview responses
        """
        # Build cache key based on query parameters
        cache_key = f"projects:list:page={page}:size={size}:active={is_active}:owner={owner}"
        
        # Try to get from cache
        cached_projects = await cache_service.get(cache_key)
        if cached_projects:
            logger.debug(f"Cache hit for projects list (page={page}, size={size})")
            return [ProjectOverviewResponse(**p) for p in cached_projects]
        
        # Cache miss - fetch from database
        logger.debug(f"Cache miss for projects list (page={page}, size={size})")
        enriched_projects = await self.repository.get_all_with_metrics(
            page=page,
            size=size,
            is_active=is_active,
            owner=owner
        )
        
        responses = []
        for item in enriched_projects:
            project = item["project"]
            response = ProjectOverviewResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                repository_url=project.repository_url,
                owner=project.owner,
                created_at=project.created_at,
                updated_at=project.updated_at,
                is_active=project.is_active,
                modules=item["modules"],
                total_tests=item["total_tests"],
                pass_rate=item["pass_rate"],
                last_status=item["last_status"],
                last_run=item["last_run"],
            )
            responses.append(response)
        
        # Store in cache (TTL: 5 minutes)
        await cache_service.set(
            cache_key,
            [r.model_dump() for r in responses],
            ttl=300
        )
        
        return responses
    
    async def update_project(
        self, project_id: str, update_data: ProjectUpdate
    ) -> Optional[ProjectResponse]:
        """Update a project and invalidate cache.
        
        Args:
            project_id: Project ID
            update_data: Project update data
            
        Returns:
            Updated project response or None if not found
        """
        update_dict = update_data.model_dump(exclude_unset=True)
        project = await self.repository.update(project_id, update_dict)
        
        if not project:
            return None
        
        # Invalidate caches
        await cache_service.delete(f"project:{project_id}")
        await cache_service.invalidate_pattern("projects:list:*")
        logger.debug(f"Invalidated cache for project {project_id}")
        
        return ProjectResponse.model_validate(project)
    
    async def delete_project(self, project_id: str) -> bool:
        """Hard delete a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            True if deleted, False if not found
        """
        return await self.repository.delete(project_id)
    
    async def soft_delete_project(self, project_id: str) -> bool:
        """Soft delete a project by setting is_active to False and invalidate cache.
        
        Args:
            project_id: Project ID
            
        Returns:
            True if soft deleted, False if not found
        """
        project = await self.repository.update(project_id, {"is_active": False})
        
        if project:
            # Invalidate caches
            await cache_service.delete(f"project:{project_id}")
            await cache_service.invalidate_pattern("projects:list:*")
            logger.debug(f"Invalidated cache for soft-deleted project {project_id}")
        
        return project is not None
    
    async def get_project_modules(self, project_id: str) -> List[ModuleResponse]:
        """Get all modules for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of module responses
        """
        modules = await self.repository.get_modules(project_id)
        return [ModuleResponse.model_validate(module) for module in modules]
    
    async def get_or_create_module(self, project_id: str, module_name: str) -> str:
        """Get existing module or create new one if not found (case-insensitive).
        
        Args:
            project_id: Project ID
            module_name: Module name
            
        Returns:
            Module ID (UUID as string)
        """
        # Check if module exists (case-insensitive)
        existing_module = await self.repository.get_module_by_name(project_id, module_name)
        
        if existing_module:
            logger.debug(f"Found existing module: {existing_module.name} (ID: {existing_module.id})")
            return str(existing_module.id)
        
        # Create new module
        module_data = {
            "id": str(uuid.uuid4()),
            "name": module_name,
            "project_id": project_id,
            "is_active": True,
        }
        
        new_module = await self.repository.create_module(module_data)
        
        # Invalidate caches
        await cache_service.delete(f"project:{project_id}")
        await cache_service.invalidate_pattern("projects:list:*")
        logger.info(f"Created new module: {new_module.name} (ID: {new_module.id}) for project {project_id}")
        
        return str(new_module.id)
    
    async def create_module(self, project_id: str, module_data: ModuleCreate) -> ModuleResponse:
        """Create a new module for a project and invalidate cache.
        
        Args:
            project_id: Project ID
            module_data: Module creation data
            
        Returns:
            Created module response
            
        Raises:
            ValueError: If project doesn't exist
        """
        # Validate project exists
        project = await self.repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        module_dict = module_data.model_dump()
        module_dict["id"] = str(uuid.uuid4())
        module_dict["project_id"] = project_id
        
        module = await self.repository.create_module(module_dict)
        
        # Invalidate caches
        await cache_service.delete(f"project:{project_id}")
        await cache_service.invalidate_pattern("projects:list:*")
        logger.info(f"Created module: {module.name} (ID: {module.id}) for project {project_id}")
        
        return ModuleResponse.model_validate(module)
    
    async def update_module(
        self, project_id: str, module_id: str, update_data: ModuleUpdate
    ) -> Optional[ModuleResponse]:
        """Update a module and invalidate cache.
        
        Args:
            project_id: Project ID
            module_id: Module ID
            update_data: Module update data
            
        Returns:
            Updated module response or None if not found
            
        Raises:
            ValueError: If project doesn't exist or module doesn't belong to project
        """
        # Validate project exists
        project = await self.repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Validate module exists and belongs to project
        module = await self.repository.get_module_by_id(module_id)
        if not module:
            return None
        
        if str(module.project_id) != project_id:
            raise ValueError(f"Module {module_id} does not belong to project {project_id}")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_module = await self.repository.update_module(module_id, update_dict)
        
        # Invalidate caches
        await cache_service.delete(f"project:{project_id}")
        await cache_service.invalidate_pattern("projects:list:*")
        logger.info(f"Updated module: {module_id} for project {project_id}")
        
        return ModuleResponse.model_validate(updated_module)
    
    async def delete_module(self, project_id: str, module_id: str) -> bool:
        """Delete a module and invalidate cache.
        
        Args:
            project_id: Project ID
            module_id: Module ID
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            ValueError: If project doesn't exist or module doesn't belong to project
        """
        # Validate project exists
        project = await self.repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Validate module exists and belongs to project
        module = await self.repository.get_module_by_id(module_id)
        if not module:
            return False
        
        if str(module.project_id) != project_id:
            raise ValueError(f"Module {module_id} does not belong to project {project_id}")
        
        deleted = await self.repository.delete_module(module_id)
        
        if deleted:
            # Invalidate caches
            await cache_service.delete(f"project:{project_id}")
            await cache_service.invalidate_pattern("projects:list:*")
            logger.info(f"Deleted module: {module_id} from project {project_id}")
        
        return deleted
