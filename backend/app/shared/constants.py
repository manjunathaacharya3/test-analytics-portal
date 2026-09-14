"""Shared constants for status enums, file size limits, and allowed extensions."""

from enum import Enum


class ScenarioStatus(str, Enum):
    """Scenario status enumeration."""
    
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"
    UNKNOWN = "unknown"


class ReportFormat(str, Enum):
    """Report format enumeration."""
    
    CUCUMBER_JSON = "cucumber_json"
    JUNIT_XML = "junit_xml"
    TESTNG_XML = "testng_xml"


class UserRole(str, Enum):
    """User role enumeration."""
    
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"


# File upload constants
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_REPORT_EXTENSIONS = [".json", ".xml"]
ALLOWED_REPORT_MIME_TYPES = [
    "application/json",
    "application/xml",
    "text/xml",
]

# Pagination constants
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Cache TTL (in seconds)
CACHE_TTL_SHORT = 60  # 1 minute
CACHE_TTL_MEDIUM = 300  # 5 minutes
CACHE_TTL_LONG = 600  # 10 minutes

# Date format constants
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

# Status codes
HTTP_STATUS_OK = 200
HTTP_STATUS_CREATED = 201
HTTP_STATUS_ACCEPTED = 202
HTTP_STATUS_NO_CONTENT = 204
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_CONFLICT = 409
HTTP_STATUS_UNPROCESSABLE_ENTITY = 422
HTTP_STATUS_INTERNAL_SERVER_ERROR = 500
HTTP_STATUS_SERVICE_UNAVAILABLE = 503
