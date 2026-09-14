"""Application configuration management."""
import os
from typing import Optional, Union

from dotenv import load_dotenv
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Test Analytics Portal API"
    app_version: str = "1.0.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:password@localhost:5432/test_portal"
    )
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "20"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_max_connections: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    
    # JWT Authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS - Will be parsed from comma-separated string
    CORS_ORIGINS: Union[str, list[str]] = Field(
        default="http://localhost:3000,http://localhost:8000"
    )
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string to list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    # Rate Limiting
    rate_limit_anonymous_per_minute: int = int(os.getenv("RATE_LIMIT_ANONYMOUS_PER_MINUTE", "100"))
    rate_limit_authenticated_per_minute: int = int(os.getenv("RATE_LIMIT_AUTHENTICATED_PER_MINUTE", "1000"))
    rate_limit_upload_per_hour: int = int(os.getenv("RATE_LIMIT_UPLOAD_PER_HOUR", "10"))
    rate_limit_bypass_admin: bool = os.getenv("RATE_LIMIT_BYPASS_ADMIN", "true").lower() == "true"
    
    # Request Validation
    max_request_size: int = int(os.getenv("MAX_REQUEST_SIZE", str(10 * 1024 * 1024)))  # 10MB default
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API Versioning
    api_version: str = "v1"
    api_prefix: str = "/api"
    supported_api_versions: list[str] = ["v1"]
    
    @property
    def api_v1_prefix(self) -> str:
        """Get the full API v1 prefix path."""
        return f"{self.api_prefix}/{self.api_version}"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
