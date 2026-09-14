"""Cache configuration for execution endpoints."""

# Cache TTL settings (in seconds)
CACHE_TTL_CONFIG = {
    "executions:project": 120,  # 2 minutes - executions list for project
    "executions:module": 120,   # 2 minutes - executions list for module
    "execution:detail": 300,    # 5 minutes - single execution detail
    "scenarios:execution": 300, # 5 minutes - scenarios for execution
}


def get_execution_cache_key(
    prefix: str,
    resource_id: str,
    page: int = 1,
    size: int = 20,
    status: str = None
) -> str:
    """Generate cache key for execution queries.
    
    Args:
        prefix: Cache key prefix (e.g., 'executions:project')
        resource_id: Resource ID (project_id, module_id, or execution_id)
        page: Page number
        size: Page size
        status: Optional status filter
        
    Returns:
        Generated cache key
    """
    key = f"{prefix}:{resource_id}:page:{page}:size:{size}"
    if status:
        key += f":status:{status}"
    return key


def get_execution_detail_cache_key(execution_id: str) -> str:
    """Generate cache key for execution detail.
    
    Args:
        execution_id: Execution ID
        
    Returns:
        Generated cache key
    """
    return f"execution:detail:{execution_id}"


def get_scenarios_cache_key(
    execution_id: str,
    page: int = 1,
    size: int = 50,
    status: str = None
) -> str:
    """Generate cache key for scenarios query.
    
    Args:
        execution_id: Execution ID
        page: Page number
        size: Page size
        status: Optional status filter
        
    Returns:
        Generated cache key
    """
    key = f"scenarios:execution:{execution_id}:page:{page}:size:{size}"
    if status:
        key += f":status:{status}"
    return key
