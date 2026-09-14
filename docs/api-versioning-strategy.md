# API Versioning Strategy

## Overview

The Test Analytics Portal API implements a comprehensive versioning strategy to ensure backward compatibility, smooth migrations, and clear communication of API changes to consumers.

## Versioning Approach

### URL-Based Versioning

All API endpoints follow the `/api/{version}` prefix pattern:

```
/api/v1/auth/login
/api/v1/projects
/api/v1/reports/upload
/api/v1/executions/{execution_id}
```

**Rationale:**
- Clear and explicit version in URL
- Easy to cache at CDN/proxy level
- Simple to test different versions
- Browser-friendly (can be tested directly in address bar)

### Header-Based Version Negotiation

Clients can optionally specify the API version using the `API-Version` header:

```http
GET /api/v1/projects HTTP/1.1
Host: api.example.com
API-Version: v1
```

The API will:
1. Validate the requested version against supported versions
2. Return `404 Not Found` for unsupported versions
3. Include the current API version in response headers

### Version Format

- **Format:** `v{major}`
- **Current Version:** `v1`
- **Supported Versions:** `["v1"]`

**Examples:**
- `v1` - Current stable version
- `v2` - Future major version (breaking changes)

## Configuration

### Centralized Version Management

All version configuration is centralized in `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    # API Versioning
    api_version: str = "v1"
    api_prefix: str = "/api"
    supported_api_versions: list[str] = ["v1"]
    
    @property
    def api_v1_prefix(self) -> str:
        """Get the full API v1 prefix path."""
        return f"{self.api_prefix}/{self.api_version}"
```

### Environment Variables

Version configuration can be overridden via environment variables:

```bash
API_VERSION=v1
API_PREFIX=/api
```

## Router Registration Pattern

### Standard Pattern

All routers follow this registration pattern in `backend/app/main.py`:

```python
from fastapi import APIRouter
from app.core.config import settings

# Individual router with module-specific prefix
router = APIRouter(prefix="/auth", tags=["authentication"])

# Register with /api/v1 prefix in main.py
app.include_router(auth_router, prefix="/api/v1")
```

### Current Router Registration

```python
# Authentication
app.include_router(auth_router, prefix="/api/v1")
# Results in: /api/v1/auth/login, /api/v1/auth/register, etc.

# Projects
app.include_router(projects_router, prefix="/api/v1")
# Results in: /api/v1/projects, /api/v1/projects/{id}, etc.

# Reports
app.include_router(reports_router, prefix="/api/v1")
# Results in: /api/v1/reports/upload, /api/v1/reports/status/{task_id}, etc.

# Executions
app.include_router(executions_router, prefix="/api/v1")
# Results in: /api/v1/executions, /api/v1/executions/{id}, etc.

# Scenarios
app.include_router(scenarios_router, prefix="/api/v1")
# Results in: /api/v1/scenarios, /api/v1/scenarios/{id}, etc.

# Analytics
app.include_router(analytics_router, prefix="/api/v1")
# Results in: /api/v1/analytics/trends, etc.

# Defects
app.include_router(defects_router, prefix="/api/v1")
# Results in: /api/v1/defects, /api/v1/defects/{id}, etc.
```

## Version Negotiation Middleware

### APIVersionMiddleware

The `APIVersionMiddleware` in `backend/app/core/middleware.py` handles:

1. **Version Validation:**
   - Checks `API-Version` header if provided
   - Validates version from URL path
   - Returns `404 Not Found` for unsupported versions

2. **Response Headers:**
   - Adds `API-Version` header to all responses
   - Includes supported versions in error responses

3. **Exception Handling:**
   - Skips version check for health endpoints (`/health`, `/api/v1/health`)
   - Skips version check for documentation (`/docs`, `/redoc`, `/openapi.json`)
   - Logs warnings for unsupported version requests

### Middleware Flow

```
Request → APIVersionMiddleware → Validation → Route Handler → Response
                ↓                                                  ↓
        Check API-Version header                    Add API-Version header
        Check URL path version                      Return response
        Return 404 if unsupported
```

## OpenAPI Documentation

### Documentation URLs

- **Swagger UI:** `/api/v1/docs`
- **ReDoc:** `/api/v1/redoc`
- **OpenAPI Schema:** `/api/v1/openapi.json`

### Configuration

```python
app = FastAPI(
    title="Test Analytics Portal API",
    version="1.0.0",
    description="Test Analytics Portal - Modular Monolith Backend API",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)
```

## Health Endpoints

### Unversioned Health Check

The health endpoint is available at both versioned and unversioned paths:

- **Unversioned:** `/health` (for Docker healthcheck and load balancers)
- **Versioned:** `/api/v1/health` (for API consumers)

**Rationale:**
- Load balancers and orchestrators expect simple `/health` endpoint
- API consumers can use versioned endpoint for consistency
- Both endpoints return identical health status

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123Z",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "database": "connected",
    "cache": "connected"
  }
}
```

## Version Migration Strategy

### Adding a New Version

1. **Update Configuration:**
   ```python
   # backend/app/core/config.py
   api_version: str = "v2"  # Update default version
   supported_api_versions: list[str] = ["v1", "v2"]  # Add new version
   ```

2. **Create Version-Specific Routers:**
   ```python
   # backend/app/api/v2/router.py
   from fastapi import APIRouter
   
   router_v2 = APIRouter(prefix="/api/v2")
   ```

3. **Register Both Versions:**
   ```python
   # backend/app/main.py
   app.include_router(auth_router_v1, prefix="/api/v1")
   app.include_router(auth_router_v2, prefix="/api/v2")
   ```

4. **Update Documentation:**
   - Document breaking changes
   - Provide migration guide
   - Set deprecation timeline for old version

### Deprecation Process

1. **Announce Deprecation:**
   - Add deprecation notice to documentation
   - Include `Deprecation` header in responses
   - Set sunset date (minimum 6 months)

2. **Deprecation Headers:**
   ```http
   Deprecation: true
   Sunset: Sat, 31 Dec 2024 23:59:59 GMT
   Link: </api/v2/docs>; rel="successor-version"
   ```

3. **Monitor Usage:**
   - Track requests to deprecated version
   - Contact high-volume consumers
   - Provide migration support

4. **Remove Old Version:**
   - Remove from `supported_api_versions`
   - Remove router registration
   - Return `410 Gone` for old version requests

## Breaking vs Non-Breaking Changes

### Non-Breaking Changes (Patch/Minor)

**Can be deployed without version bump:**
- Adding new optional fields to request/response
- Adding new endpoints
- Adding new query parameters (optional)
- Fixing bugs that don't change behavior
- Performance improvements
- Adding new enum values (if clients handle unknown values)

**Example:**
```python
# Adding optional field - Non-breaking
class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []  # New optional field
```

### Breaking Changes (Major)

**Require new major version:**
- Removing or renaming fields
- Changing field types
- Making optional fields required
- Changing URL structure
- Changing authentication mechanism
- Removing endpoints
- Changing error response format

**Example:**
```python
# Changing field type - Breaking
# v1
class ProjectResponse(BaseModel):
    created_at: str  # ISO string

# v2
class ProjectResponse(BaseModel):
    created_at: datetime  # datetime object
```

## Error Responses

### Unsupported Version

**Request:**
```http
GET /api/v3/projects HTTP/1.1
Host: api.example.com
```

**Response:**
```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": "Unsupported API Version",
  "message": "API version 'v3' is not supported",
  "supported_versions": ["v1"]
}
```

### Version Header Mismatch

**Request:**
```http
GET /api/v1/projects HTTP/1.1
Host: api.example.com
API-Version: v2
```

**Response:**
```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": "Unsupported API Version",
  "message": "API version 'v2' is not supported",
  "supported_versions": ["v1"]
}
```

## Client Implementation Guidelines

### Recommended Approach

1. **Always specify version in URL:**
   ```javascript
   const API_BASE_URL = 'https://api.example.com/api/v1';
   
   fetch(`${API_BASE_URL}/projects`);
   ```

2. **Handle version errors gracefully:**
   ```javascript
   try {
     const response = await fetch(`${API_BASE_URL}/projects`);
     if (response.status === 404) {
       const error = await response.json();
       if (error.supported_versions) {
         // Version not supported - upgrade client
         console.error('API version not supported:', error);
       }
     }
   } catch (error) {
     // Handle error
   }
   ```

3. **Check API-Version response header:**
   ```javascript
   const response = await fetch(`${API_BASE_URL}/projects`);
   const apiVersion = response.headers.get('API-Version');
   console.log('Using API version:', apiVersion);
   ```

### Testing Different Versions

```bash
# Test v1 endpoint
curl -X GET https://api.example.com/api/v1/projects

# Test with version header
curl -X GET https://api.example.com/api/v1/projects \
  -H "API-Version: v1"

# Test unsupported version
curl -X GET https://api.example.com/api/v2/projects
# Returns: 404 Not Found
```

## Monitoring and Analytics

### Metrics to Track

1. **Version Usage:**
   - Requests per version
   - Unique clients per version
   - Geographic distribution per version

2. **Migration Progress:**
   - Percentage of traffic on old vs new version
   - Time to migrate (from announcement to deprecation)
   - Number of clients still on deprecated version

3. **Error Rates:**
   - 404 errors for unsupported versions
   - Version mismatch errors
   - Client upgrade failures

### Logging

```python
logger.warning(
    f"Unsupported API version requested: {api_version_header}",
    extra={
        "path": request.url.path,
        "requested_version": api_version_header,
        "supported_versions": settings.supported_api_versions,
        "client_ip": request.client.host,
        "user_agent": request.headers.get("User-Agent"),
    }
)
```

## Best Practices

### DO

✅ Always version your API from the start
✅ Use semantic versioning for API versions
✅ Document all breaking changes clearly
✅ Provide migration guides for major versions
✅ Support at least 2 major versions simultaneously
✅ Give clients 6+ months to migrate
✅ Monitor version usage and deprecation metrics
✅ Test version negotiation middleware thoroughly
✅ Include version in response headers
✅ Keep health endpoints unversioned for infrastructure

### DON'T

❌ Don't make breaking changes without version bump
❌ Don't remove versions without deprecation period
❌ Don't version health/monitoring endpoints
❌ Don't use date-based versioning (2024-01-15)
❌ Don't support more than 3 major versions
❌ Don't change version format mid-lifecycle
❌ Don't forget to update documentation URLs
❌ Don't ignore client feedback during migration
❌ Don't version internal/admin endpoints separately
❌ Don't make version negotiation complex

## Future Considerations

### GraphQL Migration

If migrating to GraphQL in the future:
- GraphQL doesn't require URL versioning
- Use schema evolution instead
- Deprecate fields with `@deprecated` directive
- Maintain REST API alongside GraphQL during transition

### API Gateway Integration

When adding API Gateway:
- Version routing at gateway level
- A/B testing between versions
- Gradual rollout of new versions
- Automatic fallback to stable version

### Multi-Tenant Versioning

For multi-tenant scenarios:
- Allow per-tenant version pinning
- Gradual tenant migration
- Tenant-specific deprecation timelines
- Version override for enterprise clients

## References

- [REST API Versioning Best Practices](https://restfulapi.net/versioning/)
- [Semantic Versioning 2.0.0](https://semver.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAPI Specification](https://swagger.io/specification/)

## Changelog

### v1.0.0 (2024-01-15)
- Initial API versioning implementation
- `/api/v1` prefix for all endpoints
- API version negotiation middleware
- Header-based version support
- Centralized version configuration
- Documentation at `/api/v1/docs`
- Health endpoints at `/health` and `/api/v1/health`