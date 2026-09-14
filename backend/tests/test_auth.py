"""Unit tests for authentication module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.modules.auth.models import User, Role
from app.modules.auth.schemas import (
    UserCreate,
    LoginRequest,
    UserResponse,
    Token,
)
from app.modules.auth.service import AuthService


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test that password hashing works correctly."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password_456"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False


class TestJWTTokens:
    """Test JWT token generation and validation."""
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "user123", "email": "test@example.com", "role": "viewer"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_access_token(self):
        """Test JWT token decoding."""
        data = {"sub": "user123", "email": "test@example.com", "role": "viewer"}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "test@example.com"
        assert decoded["role"] == "viewer"
        assert "exp" in decoded
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token raises exception."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("invalid_token")
        
        assert exc_info.value.status_code == 401
    
    def test_token_expiration(self):
        """Test that token includes expiration time."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        # Check that expiration is present and is a valid timestamp
        assert "exp" in decoded
        exp_timestamp = decoded["exp"]
        
        # Verify expiration is a number (timestamp)
        assert isinstance(exp_timestamp, (int, float))
        
        # Convert both to UTC datetime for proper comparison
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        current_time = datetime.utcnow()
        
        # Token should expire in the future
        assert exp_datetime > current_time
        
        # Token should expire within a reasonable timeframe (between 25-35 minutes)
        # This accounts for test execution time
        time_diff = exp_datetime - current_time
        assert timedelta(minutes=25) <= time_diff <= timedelta(minutes=35)


class TestRoleModel:
    """Test Role model constants."""
    
    def test_role_constants(self):
        """Test that role constants are defined correctly."""
        assert Role.ADMIN == "admin"
        assert Role.MANAGER == "manager"
        assert Role.VIEWER == "viewer"
    
    def test_role_all(self):
        """Test that all() returns all roles."""
        roles = Role.all()
        
        assert len(roles) == 3
        assert "admin" in roles
        assert "manager" in roles
        assert "viewer" in roles
    
    def test_role_is_valid(self):
        """Test role validation."""
        assert Role.is_valid("admin") is True
        assert Role.is_valid("manager") is True
        assert Role.is_valid("viewer") is True
        assert Role.is_valid("invalid_role") is False


class TestUserSchemas:
    """Test user Pydantic schemas."""
    
    def test_user_create_schema(self):
        """Test UserCreate schema validation."""
        user_data = UserCreate(
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role="viewer"
        )
        
        assert user_data.email == "test@example.com"
        assert user_data.password == "password123"
        assert user_data.full_name == "Test User"
        assert user_data.role == "viewer"
    
    def test_user_create_invalid_role(self):
        """Test UserCreate schema rejects invalid role."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="password123",
                full_name="Test User",
                role="invalid_role"
            )
    
    def test_user_create_short_password(self):
        """Test UserCreate schema rejects short password."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="short",  # Less than 8 characters
                full_name="Test User"
            )
    
    def test_login_request_schema(self):
        """Test LoginRequest schema."""
        login_data = LoginRequest(
            email="test@example.com",
            password="password123"
        )
        
        assert login_data.email == "test@example.com"
        assert login_data.password == "password123"
    
    def test_token_schema(self):
        """Test Token schema."""
        token = Token(access_token="test_token_123")
        
        assert token.access_token == "test_token_123"
        assert token.token_type == "bearer"
        assert token.expires_in == 1800  # 30 minutes


@pytest.mark.asyncio
class TestAuthService:
    """Test AuthService methods."""
    
    async def test_register_user_success(self):
        """Test successful user registration."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        
        # Mock that user doesn't exist
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result
        
        # Create a mock user with all required fields that will be returned after refresh
        from uuid import uuid4
        mock_user = User(
            email="newuser@example.com",
            hashed_password="hashed_password",
            full_name="New User",
            role="viewer"
        )
        mock_user.id = uuid4()
        mock_user.is_active = True
        mock_user.created_at = datetime.utcnow()
        mock_user.updated_at = datetime.utcnow()
        mock_user.last_login = None
        
        # Mock refresh to populate the user object
        async def mock_refresh(user):
            user.id = mock_user.id
            user.is_active = mock_user.is_active
            user.created_at = mock_user.created_at
            user.updated_at = mock_user.updated_at
        
        db.refresh = AsyncMock(side_effect=mock_refresh)
        
        # Create user data
        user_data = UserCreate(
            email="newuser@example.com",
            password="password123",
            full_name="New User",
            role="viewer"
        )
        
        # Register user
        result = await AuthService.register_user(db, user_data)
        
        # Verify database operations were called
        assert db.add.called
        assert db.commit.called
        assert db.refresh.called
        
        # Verify returned user has correct data
        assert result.email == "newuser@example.com"
        assert result.full_name == "New User"
        assert result.role == "viewer"
        assert result.is_active is True
    
    async def test_register_user_duplicate_email(self):
        """Test user registration with duplicate email."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        
        # Mock that user already exists
        existing_user = User(
            email="existing@example.com",
            hashed_password="hashed",
            full_name="Existing User",
            role="viewer"
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        db.execute.return_value = mock_result
        
        # Create user data with same email
        user_data = UserCreate(
            email="existing@example.com",
            password="password123",
            full_name="New User",
            role="viewer"
        )
        
        # Attempt to register user
        with pytest.raises(ConflictError) as exc_info:
            await AuthService.register_user(db, user_data)
        
        assert "already exists" in str(exc_info.value.message)
    
    async def test_login_success(self):
        """Test successful login."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        
        # Create mock user with hashed password
        password = "password123"
        hashed_pwd = hash_password(password)
        mock_user = User(
            email="test@example.com",
            hashed_password=hashed_pwd,
            full_name="Test User",
            role="viewer",
            is_active=True
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        db.execute.return_value = mock_result
        
        # Login data
        login_data = LoginRequest(
            email="test@example.com",
            password=password
        )
        
        # Login
        result = await AuthService.login(db, login_data)
        
        # Verify token is returned
        assert isinstance(result, Token)
        assert result.access_token is not None
        assert result.token_type == "bearer"
        
        # Verify last_login was updated
        assert db.commit.called
    
    async def test_login_invalid_email(self):
        """Test login with non-existent email."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        
        # Mock that user doesn't exist
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result
        
        # Login data
        login_data = LoginRequest(
            email="nonexistent@example.com",
            password="password123"
        )
        
        # Attempt login
        with pytest.raises(AuthenticationError) as exc_info:
            await AuthService.login(db, login_data)
        
        assert "Invalid email or password" in str(exc_info.value.message)
    
    async def test_login_invalid_password(self):
        """Test login with incorrect password."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        
        # Create mock user
        correct_password = "correct_password"
        hashed_pwd = hash_password(correct_password)
        mock_user = User(
            email="test@example.com",
            hashed_password=hashed_pwd,
            full_name="Test User",
            role="viewer",
            is_active=True
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        db.execute.return_value = mock_result
        
        # Login data with wrong password
        login_data = LoginRequest(
            email="test@example.com",
            password="wrong_password"
        )
        
        # Attempt login
        with pytest.raises(AuthenticationError) as exc_info:
            await AuthService.login(db, login_data)
        
        assert "Invalid email or password" in str(exc_info.value.message)
    
    async def test_login_inactive_user(self):
        """Test login with inactive user account."""
        # Mock database session
        db = AsyncMock(spec=AsyncSession)
        
        # Create mock inactive user
        password = "password123"
        hashed_pwd = hash_password(password)
        mock_user = User(
            email="test@example.com",
            hashed_password=hashed_pwd,
            full_name="Test User",
            role="viewer",
            is_active=False  # Inactive user
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        db.execute.return_value = mock_result
        
        # Login data
        login_data = LoginRequest(
            email="test@example.com",
            password=password
        )
        
        # Attempt login
        with pytest.raises(AuthenticationError) as exc_info:
            await AuthService.login(db, login_data)
        
        assert "inactive" in str(exc_info.value.message).lower()
