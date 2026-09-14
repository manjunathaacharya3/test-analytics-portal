"""Pydantic schemas for authentication requests and responses."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.modules.auth.models import Role


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Schema for user registration."""
    
    password: str = Field(..., min_length=8, max_length=100)
    role: str = Field(default=Role.VIEWER)
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate that role is one of the allowed values."""
        if not Role.is_valid(v):
            raise ValueError(f"Role must be one of: {', '.join(Role.all())}")
        return v


class UserUpdate(BaseModel):
    """Schema for user updates."""
    
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        """Validate that role is one of the allowed values."""
        if v is not None and not Role.is_valid(v):
            raise ValueError(f"Role must be one of: {', '.join(Role.all())}")
        return v


class UserResponse(UserBase):
    """Schema for user response."""
    
    id: uuid.UUID
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for JWT token response."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds


class TokenData(BaseModel):
    """Schema for JWT token payload data."""
    
    user_id: Optional[str] = None
    email: Optional[str] = None


class LoginRequest(BaseModel):
    """Schema for login request."""
    
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    
    refresh_token: str
