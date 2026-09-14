"""Authentication service for user management and JWT operations."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    LoginRequest,
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
)


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    async def register_user(
        db: AsyncSession,
        user_data: UserCreate
    ) -> UserResponse:
        """Register a new user.
        
        Args:
            db: Database session
            user_data: User registration data
            
        Returns:
            Created user response
            
        Raises:
            ConflictError: If user with email already exists
        """
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise ConflictError(
                message=f"User with email {user_data.email} already exists"
            )
        
        # Create new user
        hashed_pwd = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_pwd,
            full_name=user_data.full_name,
            role=user_data.role,
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        return UserResponse.model_validate(new_user)
    
    @staticmethod
    async def login(
        db: AsyncSession,
        login_data: LoginRequest
    ) -> Token:
        """Authenticate user and generate JWT token.
        
        Args:
            db: Database session
            login_data: Login credentials
            
        Returns:
            JWT access token
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == login_data.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationError(message="Invalid email or password")
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise AuthenticationError(message="Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise AuthenticationError(message="User account is inactive")
        
        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()
        
        # Generate JWT token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        
        return Token(access_token=access_token)
    
    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: str
    ) -> UserResponse:
        """Get user by ID.
        
        Args:
            db: Database session
            user_id: User UUID
            
        Returns:
            User response
            
        Raises:
            NotFoundError: If user not found
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError(message=f"User with ID {user_id} not found")
        
        return UserResponse.model_validate(user)
    
    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: str,
        user_data: UserUpdate
    ) -> UserResponse:
        """Update user information.
        
        Args:
            db: Database session
            user_id: User UUID
            user_data: User update data
            
        Returns:
            Updated user response
            
        Raises:
            NotFoundError: If user not found
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError(message=f"User with ID {user_id} not found")
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        
        return UserResponse.model_validate(user)
