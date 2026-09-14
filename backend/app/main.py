"""FastAPI application entry point with modular monolith architecture."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.core.middleware import setup_middleware
from app.core.redis_client import close_redis_client
from app.core.logging import configure_logging, get_logger

# Import routers from all modules
from app.modules.auth.router import router as auth_router
from app.modules.reports.router import router as reports_router
from app.modules.scenarios.router import router as scenarios_router
from app.modules.analytics.router import router as analytics_router
from app.modules.defects.router import router as defects_router
from app.projects.router import router as projects_router
from app.executions.router import router as executions_router
from app.executions.router import project_router as executions_project_router
from app.executions.router import module_router as executions_module_router

# Configure structured logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting Test Analytics Portal API")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Test database connection (non-blocking)
    try:
        async with engine.begin() as conn:
            logger.info("✅ Database connection established successfully")
    except Exception as e:
        logger.warning(f"⚠️  Database connection failed during startup: {e}")
        logger.warning("Application will start anyway. Database operations may fail until connection is established.")
        # Do not raise - allow the application to start
    
    yield
    
    # Shutdown
    logger.info("Shutting down Test Analytics Portal API")
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during database shutdown: {e}")
    
    try:
        await close_redis_client()
        logger.info("Redis connections closed")
    except Exception as e:
        logger.error(f"Error during Redis shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Test Analytics Portal - Modular Monolith Backend API",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# Setup middleware (CORS, logging, error handling)
setup_middleware(app)

# Include routers with /api/v1 prefix
app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(scenarios_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(defects_router, prefix="/api/v1")
app.include_router(executions_router, prefix="/api/v1")
app.include_router(executions_project_router, prefix="/api/v1")
app.include_router(executions_module_router, prefix="/api/v1")


@app.get("/", tags=["health"])
async def root():
    """Root endpoint."""
    return {
        "message": "Test Analytics Portal API",
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/health", tags=["health"])
@app.get("/api/v1/health", tags=["health"])
async def health_check():
    """Health check endpoint with database and cache connectivity checks.
    
    Available at both /health (for Docker healthcheck) and /api/v1/health (for API consumers).
    
    Returns:
        dict: Health status including service connectivity information
    """
    from datetime import datetime
    from app.core.redis_client import check_redis_health
    
    # Initialize services status
    services = {
        "database": "unknown",
        "cache": "unknown"
    }
    
    overall_status = "healthy"
    
    # Check database connectivity
    try:
        async with engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
            services["database"] = "connected"
            logger.debug("Database health check: OK")
    except Exception as e:
        services["database"] = "disconnected"
        overall_status = "unhealthy"
        logger.error(f"Database health check failed: {e}")
    
    # Check Redis connectivity
    try:
        redis_healthy = await check_redis_health()
        services["cache"] = "connected" if redis_healthy else "disconnected"
        if not redis_healthy:
            overall_status = "degraded"  # Redis failure is not critical
        logger.debug(f"Redis health check: {'OK' if redis_healthy else 'FAILED'}")
    except Exception as e:
        services["cache"] = "disconnected"
        overall_status = "degraded"  # Redis failure is not critical
        logger.warning(f"Redis health check failed: {e}")
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.app_version,
        "environment": settings.environment,
        "services": services
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
