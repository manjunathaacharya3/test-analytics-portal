"""Redis cache service for caching API responses."""
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional

from app.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class CacheService:
    """Service for Redis caching operations."""
    
    def __init__(self):
        """Initialize cache service."""
        self.redis_client = None
    
    async def _get_client(self):
        """Get Redis client instance."""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get cache key '{key}': {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ) -> bool:
        """Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: 5 minutes)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            serialized = json.dumps(value, default=str)
            await client.setex(key, ttl, serialized)
            logger.debug(f"Cached key '{key}' with TTL {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Failed to set cache key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            client = await self._get_client()
            await client.delete(key)
            logger.debug(f"Deleted cache key '{key}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache key '{key}': {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> bool:
        """Invalidate all keys matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., 'projects:*')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await client.delete(*keys)
                logger.debug(f"Invalidated {len(keys)} keys matching '{pattern}'")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate pattern '{pattern}': {e}")
            return False


# Global cache service instance
cache_service = CacheService()


def cached(
    key_prefix: str,
    ttl: int = 300,
    key_builder: Optional[Callable] = None
):
    """Decorator for caching function results.
    
    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live in seconds (default: 5 minutes)
        key_builder: Optional function to build cache key from args/kwargs
    
    Example:
        @cached(key_prefix="projects", ttl=300)
        async def get_projects(page: int, size: int):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key builder: prefix:func_name:args:kwargs
                args_str = ":".join(str(arg) for arg in args)
                kwargs_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{func.__name__}:{args_str}:{kwargs_str}"
            
            # Try to get from cache
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key '{cache_key}'")
                return cached_result
            
            # Cache miss - execute function
            logger.debug(f"Cache miss for key '{cache_key}'")
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_service.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
