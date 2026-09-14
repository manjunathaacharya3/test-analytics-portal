"""Shared utility functions for file validation, date parsing, and pagination."""

import mimetypes
from datetime import datetime
from typing import Optional

from app.core.exceptions import ValidationError


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """Validate file extension.
    
    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (e.g., ['.json', '.xml'])
        
    Returns:
        True if extension is allowed
        
    Raises:
        ValidationError: If extension is not allowed
    """
    extension = filename.lower().split('.')[-1]
    if f".{extension}" not in allowed_extensions:
        raise ValidationError(
            message=f"File extension .{extension} is not allowed",
            details={"allowed_extensions": allowed_extensions}
        )
    return True


def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
    """Validate file size.
    
    Args:
        file_size: Size of file in bytes
        max_size_mb: Maximum allowed size in megabytes
        
    Returns:
        True if size is within limit
        
    Raises:
        ValidationError: If file size exceeds limit
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise ValidationError(
            message=f"File size {file_size / 1024 / 1024:.2f}MB exceeds maximum allowed size of {max_size_mb}MB",
            details={"file_size_mb": file_size / 1024 / 1024, "max_size_mb": max_size_mb}
        )
    return True


def validate_mime_type(filename: str, allowed_types: list[str]) -> bool:
    """Validate MIME type.
    
    Args:
        filename: Name of the file
        allowed_types: List of allowed MIME types (e.g., ['application/json'])
        
    Returns:
        True if MIME type is allowed
        
    Raises:
        ValidationError: If MIME type is not allowed
    """
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type not in allowed_types:
        raise ValidationError(
            message=f"MIME type {mime_type} is not allowed",
            details={"allowed_types": allowed_types}
        )
    return True


def parse_date(date_string: str, format: str = "%Y-%m-%d") -> datetime:
    """Parse date string to datetime object.
    
    Args:
        date_string: Date string to parse
        format: Date format (default: YYYY-MM-DD)
        
    Returns:
        Parsed datetime object
        
    Raises:
        ValidationError: If date string is invalid
    """
    try:
        return datetime.strptime(date_string, format)
    except ValueError as e:
        raise ValidationError(
            message=f"Invalid date format: {date_string}",
            details={"expected_format": format, "error": str(e)}
        )


def parse_date_range(
    start_date: Optional[str],
    end_date: Optional[str],
    format: str = "%Y-%m-%d"
) -> tuple[Optional[datetime], Optional[datetime]]:
    """Parse date range strings.
    
    Args:
        start_date: Start date string
        end_date: End date string
        format: Date format (default: YYYY-MM-DD)
        
    Returns:
        Tuple of (start_datetime, end_datetime)
        
    Raises:
        ValidationError: If date strings are invalid or range is invalid
    """
    start = parse_date(start_date, format) if start_date else None
    end = parse_date(end_date, format) if end_date else None
    
    if start and end and start > end:
        raise ValidationError(
            message="Start date must be before end date",
            details={"start_date": start_date, "end_date": end_date}
        )
    
    return start, end


def calculate_pagination(
    total: int,
    page: int = 1,
    size: int = 20
) -> dict:
    """Calculate pagination metadata.
    
    Args:
        total: Total number of items
        page: Current page number (1-indexed)
        size: Page size
        
    Returns:
        Dictionary with pagination metadata
    """
    pages = (total + size - 1) // size if total > 0 else 0
    offset = (page - 1) * size
    
    return {
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
        "offset": offset,
        "has_next": page < pages,
        "has_prev": page > 1,
    }


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators and parent directory references
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")
    
    # Remove any non-alphanumeric characters except dots, dashes, and underscores
    sanitized = "".join(
        c for c in filename
        if c.isalnum() or c in ".-_"
    )
    
    return sanitized
