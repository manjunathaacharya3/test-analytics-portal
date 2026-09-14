"""Custom exception classes for the application."""

from typing import Any, Optional


class TAPSException(Exception):
    """Base exception class for TAPS application."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(TAPSException):
    """Exception raised for validation errors.
    
    Used when input data fails validation checks.
    """
    pass


class AuthenticationError(TAPSException):
    """Exception raised for authentication failures.
    
    Used when user credentials are invalid or missing.
    """
    pass


class AuthorizationError(TAPSException):
    """Exception raised for authorization failures.
    
    Used when user lacks permissions for an action.
    """
    pass


class NotFoundError(TAPSException):
    """Exception raised when a resource is not found.
    
    Used when querying for non-existent database records.
    """
    pass


class ConflictError(TAPSException):
    """Exception raised for resource conflicts.
    
    Used when attempting to create duplicate resources.
    """
    pass


class DatabaseError(TAPSException):
    """Exception raised for database operation failures.
    
    Used when database queries or transactions fail.
    """
    pass


class ExternalServiceError(TAPSException):
    """Exception raised for external service failures.
    
    Used when third-party API calls fail.
    """
    pass
