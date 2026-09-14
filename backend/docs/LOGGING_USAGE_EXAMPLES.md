# Structured Logging Usage Guide

## Overview

This guide provides practical examples for using the structured logging system implemented in the Test Analytics Portal backend.

## Quick Start

### Basic Logging

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# Simple info log
logger.info("User logged in successfully")

# Log with structured fields
logger.info(
    "Project created",
    project_id="proj-123",
    project_name="My Test Project",
    owner="user@example.com"
)
```

### Error Logging with Stack Traces

```python
try:
    result = perform_database_operation()
except Exception as e:
    logger.error(
        "Database operation failed",
        operation="create_execution",
        error=str(e),
        exc_info=True  # This includes the full stack trace
    )
    raise
```

### Warning Logs

```python
logger.warning(
    "Deprecated API endpoint used",
    endpoint="/api/v1/old-endpoint",
    client_ip=request.client.host,
    migration_guide="https://docs.example.com/migration"
)
```

### Debug Logs

```python
logger.debug(
    "Cache lookup",
    cache_key="project:123",
    cache_hit=True,
    ttl_remaining=120
)
```

## Correlation IDs

### Automatic Correlation ID (in Request Context)

When using the RequestLoggingMiddleware, correlation IDs are automatically generated and bound to the logging context:

```python
from fastapi import APIRouter, Request
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/projects/{project_id}")
async def get_project(project_id: str, request: Request):
    # Correlation ID is automatically available
    correlation_id = request.state.correlation_id
    
    # All logs automatically include the correlation ID
    logger.info("Fetching project", project_id=project_id)
    
    # ... your logic here
    
    logger.info("Project fetched successfully", project_id=project_id)
    
    return {"project_id": project_id}
```

### Manual Correlation ID Binding (for Background Tasks)

```python
from app.core.logging import get_logger, bind_correlation_id, unbind_context
import uuid

logger = get_logger(__name__)

async def background_task():
    # Generate and bind correlation ID for background task
    correlation_id = str(uuid.uuid4())
    bind_correlation_id(correlation_id)
    
    try:
        logger.info("Background task started")
        # ... task logic
        logger.info("Background task completed")
    finally:
        # Always clear context when done
        unbind_context()
```

## User Context

### Binding User Information

```python
from app.core.logging import bind_user_context
from app.core.dependencies import get_current_user

@router.post("/projects")
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user)
):
    # Bind user context to all subsequent logs
    bind_user_context(
        user_id=str(current_user.id),
        user_email=current_user.email
    )
    
    logger.info(
        "Creating project",
        project_name=project_data.name
    )
    # This log will automatically include user_id and user_email
    
    # ... create project logic
    
    return {"status": "created"}
```

## Log Levels

### When to Use Each Level

**DEBUG** - Detailed diagnostic information
```python
logger.debug(
    "SQL query executed",
    query="SELECT * FROM projects WHERE id = ?",
    params=["123"],
    execution_time_ms=45
)
```

**INFO** - General informational messages
```python
logger.info(
    "Report uploaded successfully",
    report_type="cucumber",
    file_size_bytes=1024000,
    scenarios_count=150
)
```

**WARNING** - Warning messages for potentially harmful situations
```python
logger.warning(
    "Cache miss - falling back to database",
    cache_key="executions:module:456",
    fallback_duration_ms=250
)
```

**ERROR** - Error events that might still allow the application to continue
```python
logger.error(
    "Failed to send notification email",
    recipient="user@example.com",
    error_code="SMTP_TIMEOUT",
    exc_info=True
)
```

## Sensitive Data Redaction

Sensitive fields are automatically redacted from logs:

```python
# This will automatically redact the password
logger.info(
    "User registration attempt",
    email="user@example.com",
    password="secret123",  # Will be logged as "***REDACTED***"
    full_name="John Doe"
)

# Token fields are also redacted
logger.debug(
    "API request headers",
    headers={
        "authorization": "Bearer token123",  # Will be redacted
        "content-type": "application/json"   # Will be logged normally
    }
)
```

### Automatically Redacted Fields

- `password`, `hashed_password`
- `token`, `access_token`, `refresh_token`
- `authorization`, `bearer`
- `api_key`, `secret`, `jwt`

## Service-Specific Patterns

### Repository Layer

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

class ProjectRepository:
    async def get_by_id(self, project_id: str) -> Project:
        logger.debug(
            "Fetching project from database",
            project_id=project_id
        )
        
        project = await self.db.get(Project, project_id)
        
        if not project:
            logger.warning(
                "Project not found",
                project_id=project_id
            )
            return None
        
        logger.debug(
            "Project fetched successfully",
            project_id=project_id,
            project_name=project.name
        )
        
        return project
```

### Service Layer

```python
class ReportService:
    async def process_report(self, file_data: bytes, module_id: str):
        logger.info(
            "Processing report upload",
            module_id=module_id,
            file_size_bytes=len(file_data)
        )
        
        try:
            # Parse report
            parsed_data = self.parser.parse(file_data)
            
            logger.info(
                "Report parsed successfully",
                scenarios_count=len(parsed_data.scenarios),
                passed=parsed_data.passed,
                failed=parsed_data.failed
            )
            
            # Save to database
            execution = await self.repository.create_execution(parsed_data)
            
            logger.info(
                "Report processing completed",
                execution_id=str(execution.id),
                processing_time_ms=100
            )
            
            return execution
            
        except ParseError as e:
            logger.error(
                "Failed to parse report",
                module_id=module_id,
                error=str(e),
                exc_info=True
            )
            raise
        except DatabaseError as e:
            logger.error(
                "Failed to save execution to database",
                module_id=module_id,
                error=str(e),
                exc_info=True
            )
            raise
```

### Router/Controller Layer

```python
from fastapi import APIRouter, HTTPException, status
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/reports/upload")
async def upload_report(
    file: UploadFile,
    module_id: str,
    current_user: User = Depends(get_current_user)
):
    bind_user_context(
        user_id=str(current_user.id),
        user_email=current_user.email
    )
    
    logger.info(
        "Report upload initiated",
        module_id=module_id,
        filename=file.filename,
        content_type=file.content_type
    )
    
    try:
        file_data = await file.read()
        execution = await report_service.process_report(file_data, module_id)
        
        logger.info(
            "Report upload successful",
            execution_id=str(execution.id)
        )
        
        return {"execution_id": str(execution.id)}
        
    except ValueError as e:
        logger.warning(
            "Invalid report format",
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report format"
        )
```

## Log Output Examples

### Development Environment (Console)

```
2024-01-15T10:30:45.123Z [INFO    ] Request started
  correlation_id=abc123-def456-ghi789
  method=GET
  endpoint=/api/v1/projects
  client_host=192.168.1.100
  user_agent=Mozilla/5.0...

2024-01-15T10:30:45.168Z [INFO    ] Request completed
  correlation_id=abc123-def456-ghi789
  method=GET
  endpoint=/api/v1/projects
  status_code=200
  duration_ms=45
```

### Production Environment (JSON)

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "correlation_id": "abc123-def456-ghi789",
  "service": "taps-backend",
  "environment": "production",
  "logger_name": "app.projects.router",
  "module": "router",
  "function": "get_projects",
  "line_number": 45,
  "method": "GET",
  "endpoint": "/api/v1/projects",
  "status_code": 200,
  "duration_ms": 45,
  "user_id": "user-uuid-123",
  "user_email": "user@example.com",
  "message": "Request completed"
}
```

## Configuration

### Environment Variables

```bash
# Set log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Set environment (affects output format)
ENVIRONMENT=production  # JSON output
ENVIRONMENT=development # Console output

# Enable debug mode (colored console output)
DEBUG=true
```

### Runtime Configuration

```python
from app.core.logging import configure_logging
from app.core.config import settings

# Logging is automatically configured on application startup
# in app/main.py, but you can reconfigure if needed:

configure_logging()
```

## Best Practices

### 1. Always Use Structured Fields

❌ **Bad:**
```python
logger.info(f"User {user_id} created project {project_name}")
```

✅ **Good:**
```python
logger.info(
    "User created project",
    user_id=user_id,
    project_name=project_name
)
```

### 2. Include Context in Error Logs

❌ **Bad:**
```python
logger.error("Failed to save")
```

✅ **Good:**
```python
logger.error(
    "Failed to save execution to database",
    execution_id=execution_id,
    module_id=module_id,
    error=str(e),
    exc_info=True
)
```

### 3. Always Clear Context in Background Tasks

❌ **Bad:**
```python
async def background_task():
    bind_correlation_id(str(uuid.uuid4()))
    # ... task logic
    # Context not cleared - will leak to next task!
```

✅ **Good:**
```python
async def background_task():
    bind_correlation_id(str(uuid.uuid4()))
    try:
        # ... task logic
    finally:
        unbind_context()  # Always clear!
```

### 4. Use Appropriate Log Levels

- **DEBUG**: Detailed diagnostic info (SQL queries, cache operations)
- **INFO**: Normal application flow (requests, business operations)
- **WARNING**: Unexpected but handled situations (cache misses, deprecated usage)
- **ERROR**: Errors that need attention (exceptions, failures)

### 5. Include Performance Metrics

```python
import time

start_time = time.time()
# ... operation
duration_ms = (time.time() - start_time) * 1000

logger.info(
    "Operation completed",
    operation="complex_calculation",
    duration_ms=round(duration_ms, 2),
    items_processed=1000
)
```

## Troubleshooting

### Correlation IDs Not Appearing

**Problem**: Logs don't include correlation_id

**Solution**: Ensure RequestLoggingMiddleware is properly configured in middleware stack:

```python
# In app/main.py
from app.core.middleware import setup_middleware

setup_middleware(app)  # This sets up all middleware including logging
```

### Sensitive Data Not Redacted

**Problem**: Passwords or tokens appearing in logs

**Solution**: Check field names match redaction patterns (case-insensitive):

```python
# These will be redacted:
password, Password, PASSWORD
access_token, accessToken, ACCESS_TOKEN
api_key, apiKey, API_KEY

# If using custom field names, add them to SENSITIVE_FIELDS in logging.py
```

### Logs Not in JSON Format

**Problem**: Logs showing console format in production

**Solution**: Check ENVIRONMENT variable:

```bash
ENVIRONMENT=production  # Must be set for JSON output
```

## Integration with Monitoring Tools

### Elasticsearch/Kibana

JSON logs can be directly ingested into Elasticsearch:

```bash
# Example Filebeat configuration
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/taps-backend/*.log
  json.keys_under_root: true
  json.add_error_key: true
```

### Grafana Loki

```yaml
# Example Promtail configuration
clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: taps-backend
    static_configs:
      - targets:
          - localhost
        labels:
          job: taps-backend
          __path__: /var/log/taps-backend/*.log
    pipeline_stages:
      - json:
          expressions:
            correlation_id: correlation_id
            level: level
            user_id: user_id
```

### CloudWatch

```python
# Example CloudWatch integration (add to logging.py if needed)
import watchtower

cloudwatch_handler = watchtower.CloudWatchLogHandler(
    log_group="/aws/taps-backend",
    stream_name="{instance_id}"
)
logging.getLogger().addHandler(cloudwatch_handler)
```

## Summary

Structured logging with correlation IDs provides:

✅ **Request Tracing**: Track requests across the entire application
✅ **Structured Data**: Easy querying and filtering in log aggregation tools
✅ **Security**: Automatic sensitive data redaction
✅ **Context Propagation**: User and request context in all logs
✅ **Production Ready**: JSON format for machine parsing
✅ **Developer Friendly**: Colored console output for local development

For more information, see:
- `backend/app/core/logging.py` - Implementation
- `backend/tests/test_logging.py` - Test examples
- `.slingshot/context/LOGGING_IMPLEMENTATION.md` - Full implementation report
