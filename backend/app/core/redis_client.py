"""Redis client configuration and connection management."""
import logging
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[Redis] = None
_connection_pool: Optional[ConnectionPool] = None


async def get_redis_client() -> Redis:
    """Get or create Redis client instance with proper connection pooling.
    
    Returns:
        Redis: Async Redis client with health-checked connection pool
    """
    global _redis_client, _connection_pool
    
    if _redis_client is None:
        try:
            # Create connection pool with health check and keepalive settings
            # Note: socket_keepalive_options removed to fix Error 22 (EINVAL)
            # The numeric keys (1,2,3) are platform-specific and cause issues in Docker
            _connection_pool = ConnectionPool.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.redis_max_connections,
                # Socket settings for connection stability
                socket_keepalive=True,
                # Removed socket_keepalive_options - causes EINVAL on some platforms
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                retry_on_error=[ConnectionError, TimeoutError],
                # Health check interval for pool connections (in seconds)
                health_check_interval=30
            )
            
            _redis_client = Redis(connection_pool=_connection_pool)
            logger.info(f"Redis client created with connection pool: {settings.redis_url}")
            
            # Verify initial connection
            await _redis_client.ping()
            logger.info("Redis initial connection verified successfully")
            
        except Exception as e:
            logger.error(f"Failed to create Redis client: {e}")
            # Clean up on failure
            if _connection_pool:
                await _connection_pool.disconnect()
                _connection_pool = None
            _redis_client = None
            raise
    
    return _redis_client


async def close_redis_client() -> None:
    """Close Redis client connection and connection pool."""
    global _redis_client, _connection_pool
    
    if _redis_client is not None:
        try:
            await _redis_client.close()
            logger.info("Redis client closed successfully")
        except Exception as e:
            logger.error(f"Error closing Redis client: {e}")
        finally:
            _redis_client = None
    
    if _connection_pool is not None:
        try:
            await _connection_pool.disconnect()
            logger.info("Redis connection pool disconnected successfully")
        except Exception as e:
            logger.error(f"Error disconnecting Redis connection pool: {e}")
        finally:
            _connection_pool = None


async def check_redis_health() -> bool:
    """Check Redis connectivity with proper error handling.
    
    Returns:
        bool: True if Redis is healthy, False otherwise
    """
    try:
        client = await get_redis_client()
        # Use ping with timeout to avoid hanging
        await client.ping()
        logger.debug("Redis health check: PASSED")
        return True
    except ConnectionError as e:
        logger.warning(f"Redis health check failed: Connection error - {e}")
        # Reset client on connection errors to force reconnection
        global _redis_client
        _redis_client = None
        return False
    except TimeoutError as e:
        logger.warning(f"Redis health check failed: Timeout - {e}")
        return False
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return False


async def get_redis_value(key: str) -> Optional[str]:
    """Get value from Redis with error handling.
    
    Args:
        key: Redis key to retrieve
        
    Returns:
        Optional[str]: Value if found, None otherwise
    """
    try:
        client = await get_redis_client()
        value = await client.get(key)
        return value
    except Exception as e:
        logger.error(f"Failed to get Redis key '{key}': {e}")
        return None


async def set_redis_value(key: str, value: str, expire: Optional[int] = None) -> bool:
    """Set value in Redis with optional expiration.
    
    Args:
        key: Redis key to set
        value: Value to store
        expire: Optional expiration time in seconds
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        client = await get_redis_client()
        if expire:
            await client.setex(key, expire, value)
        else:
            await client.set(key, value)
        return True
    except Exception as e:
        logger.error(f"Failed to set Redis key '{key}': {e}")
        return False
