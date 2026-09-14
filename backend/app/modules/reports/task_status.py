"""Redis-backed task status tracking service for report uploads."""
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

from app.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatusData(BaseModel):
    """Task status data model."""
    task_id: str
    status: TaskStatus
    progress: int = Field(ge=0, le=100, description="Progress percentage (0-100)")
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskStatusService:
    """Service for managing task status in Redis with persistent storage."""
    
    # Default TTL: 24 hours (86400 seconds)
    DEFAULT_TTL = 86400
    
    def __init__(self):
        """Initialize task status service."""
        self.redis_client = None
    
    async def _get_client(self):
        """Get Redis client instance."""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    def _get_key(self, task_id: str) -> str:
        """Generate Redis key for task status.
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            Redis key string
        """
        return f"task_status:{task_id}"
    
    async def create_task(self) -> str:
        """Create a new task and return its ID.
        
        Returns:
            Unique task ID
        """
        task_id = str(uuid.uuid4())
        
        # Initialize task status
        status_data = TaskStatusData(
            task_id=task_id,
            status=TaskStatus.PROCESSING,
            progress=0
        )
        
        await self.set_status(task_id, status_data)
        logger.info(f"Created new task: {task_id}")
        
        return task_id
    
    async def set_status(
        self,
        task_id: str,
        status_data: TaskStatusData,
        ttl: int = DEFAULT_TTL
    ) -> bool:
        """Store task status in Redis with TTL.
        
        Args:
            task_id: Unique task identifier
            status_data: Task status data to store
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            key = self._get_key(task_id)
            
            # Update timestamp
            status_data.updated_at = datetime.utcnow()
            
            # Serialize and store
            value = status_data.model_dump_json()
            await client.setex(key, ttl, value)
            
            logger.debug(f"Set status for task {task_id}: {status_data.status} ({status_data.progress}%)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set status for task {task_id}: {e}")
            return False
    
    async def get_status(self, task_id: str) -> Optional[TaskStatusData]:
        """Retrieve task status from Redis.
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            Task status data or None if not found
        """
        try:
            client = await self._get_client()
            key = self._get_key(task_id)
            
            value = await client.get(key)
            if not value:
                logger.warning(f"Task status not found: {task_id}")
                return None
            
            # Deserialize
            status_data = TaskStatusData.model_validate_json(value)
            logger.debug(f"Retrieved status for task {task_id}: {status_data.status}")
            
            return status_data
            
        except Exception as e:
            logger.error(f"Failed to get status for task {task_id}: {e}")
            return None
    
    async def update_progress(
        self,
        task_id: str,
        progress: int,
        ttl: int = DEFAULT_TTL
    ) -> bool:
        """Update task progress percentage.
        
        Args:
            task_id: Unique task identifier
            progress: Progress percentage (0-100)
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        status_data = await self.get_status(task_id)
        if not status_data:
            logger.warning(f"Cannot update progress: task {task_id} not found")
            return False
        
        status_data.progress = max(0, min(100, progress))  # Clamp to 0-100
        return await self.set_status(task_id, status_data, ttl)
    
    async def mark_completed(
        self,
        task_id: str,
        result: Dict[str, Any],
        ttl: int = DEFAULT_TTL
    ) -> bool:
        """Mark task as completed with result.
        
        Args:
            task_id: Unique task identifier
            result: Task result data
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        status_data = await self.get_status(task_id)
        if not status_data:
            logger.warning(f"Cannot mark completed: task {task_id} not found")
            return False
        
        status_data.status = TaskStatus.COMPLETED
        status_data.progress = 100
        status_data.result = result
        status_data.error = None
        
        logger.info(f"Task {task_id} marked as completed")
        return await self.set_status(task_id, status_data, ttl)
    
    async def mark_failed(
        self,
        task_id: str,
        error: str,
        ttl: int = DEFAULT_TTL
    ) -> bool:
        """Mark task as failed with error message.
        
        Args:
            task_id: Unique task identifier
            error: Error message
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        status_data = await self.get_status(task_id)
        if not status_data:
            # Create new status data if not found
            status_data = TaskStatusData(
                task_id=task_id,
                status=TaskStatus.FAILED,
                progress=0
            )
        
        status_data.status = TaskStatus.FAILED
        status_data.error = error
        status_data.result = None
        
        logger.error(f"Task {task_id} marked as failed: {error}")
        return await self.set_status(task_id, status_data, ttl)
    
    async def delete_status(self, task_id: str) -> bool:
        """Delete task status from Redis.
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            client = await self._get_client()
            key = self._get_key(task_id)
            await client.delete(key)
            logger.debug(f"Deleted status for task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete status for task {task_id}: {e}")
            return False


# Global task status service instance
task_status_service = TaskStatusService()
