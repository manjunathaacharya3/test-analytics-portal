# TAPS Migration: Low-Level Executable Tasks

## Document Purpose
This document breaks down the TAPS Migration Plan into granular, independently executable tasks suitable for AI model execution. Each task has clear objectives, scope, deliverables, dependencies, and acceptance criteria.

---

## Task Index

### Phase 1: Foundation (Tasks 1.1 - 1.8)
### Phase 2: Backend API Migration (Tasks 2.1 - 2.10)
### Phase 3: Frontend Migration (Tasks 3.1 - 3.12)
### Phase 4: Advanced Features (Tasks 4.1 - 4.6)
### Phase 5: Performance Optimization (Tasks 5.1 - 5.8)
### Phase 6: Testing & Deployment (Tasks 6.1 - 6.9)

---

# PHASE 1: FOUNDATION

## Task 1.1: Initialize Next.js 14 Frontend Project

**Objective:** Create a new Next.js 14 project with TypeScript, TailwindCSS, and shadcn/ui configured.

**Scope:**
- Initialize Next.js 14 with App Router
- Configure TypeScript with strict mode
- Set up TailwindCSS with custom design tokens
- Install and configure shadcn/ui components

**Prerequisites:**
- Node.js 18+ installed
- Package manager (npm/yarn/pnpm) available

**Deliverables:**
1. `frontend/` directory with Next.js project structure
2. `tsconfig.json` with strict TypeScript configuration
3. `tailwind.config.ts` with custom theme tokens
4. `components.json` for shadcn/ui configuration
5. `package.json` with all required dependencies
6. `.env.example` file with environment variable templates

**Acceptance Criteria:**
- [ ] `npm run dev` starts development server successfully
- [ ] TypeScript compilation passes with no errors
- [ ] TailwindCSS classes work in components
- [ ] At least one shadcn/ui component (Button) installed and functional
- [ ] Project follows Next.js 14 App Router structure

**Commands to Execute:**
```bash
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --import-alias "@/*"
cd frontend
npx shadcn-ui@latest init
```

**Files to Create/Modify:**
- `frontend/src/app/layout.tsx`
- `frontend/src/app/page.tsx`
- `frontend/tailwind.config.ts`
- `frontend/tsconfig.json`
- `frontend/.env.example`

---

## Task 1.2: Restructure FastAPI Backend into Modular Monolith

**Objective:** Reorganize existing FastAPI backend from flat structure to modular monolith architecture.

**Scope:**
- Create module-based directory structure (projects, executions, reports, auth, core)
- Move existing code from `service/` to new structure
- Separate routers, services, models, schemas, and repositories
- Implement app factory pattern in `main.py`

**Prerequisites:**
- Existing POC backend code in `service/` directory
- Understanding of current API endpoints

**Deliverables:**
1. New `backend/app/` directory structure with modules:
   - `app/projects/` (router.py, service.py, models.py, schemas.py, repository.py)
   - `app/executions/` (router.py, service.py, models.py, schemas.py, repository.py)
   - `app/reports/` (router.py, service.py, schemas.py, parsers/)
   - `app/core/` (database.py, config.py, dependencies.py)
2. Migrated code from POC to new structure
3. Updated import paths
4. App factory pattern in `app/main.py`

**Acceptance Criteria:**
- [ ] All existing API endpoints accessible under new structure
- [ ] No circular import errors
- [ ] Each module follows repository pattern (router → service → repository → models)
- [ ] `uvicorn app.main:app --reload` starts server successfully
- [ ] All existing endpoints return same responses as POC

**Migration Mapping:**
- `service/main.py` → `app/main.py`
- `service/apis/projects.py` → `app/projects/router.py` + `service.py` + `repository.py`
- `service/apis/execution.py` → `app/executions/router.py` + `service.py` + `repository.py`
- `service/apis/report.py` → `app/reports/router.py` + `service.py`
- `service/cucumber_parser.py` → `app/reports/parsers/cucumber.py`
- `database/` → `app/core/database.py` + `app/{module}/models.py`

**Files to Create:**
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/dependencies.py`
- `backend/app/projects/{router,service,models,schemas,repository}.py`
- `backend/app/executions/{router,service,models,schemas,repository}.py`
- `backend/app/reports/{router,service,schemas}.py`
- `backend/app/reports/parsers/{base,cucumber}.py`
- `backend/app/core/{database,config,dependencies}.py`

---

## Task 1.3: Set Up PostgreSQL 16 and Redis 7 with Docker Compose

**Objective:** Create production-ready Docker Compose configuration for PostgreSQL and Redis.

**Scope:**
- Configure PostgreSQL 16 with proper health checks
- Configure Redis 7 with memory limits and eviction policy
- Set up persistent volumes for data
- Configure environment variables
- Add pgAdmin for database management (optional)

**Prerequisites:**
- Docker and Docker Compose installed
- Understanding of database connection strings

**Deliverables:**
1. `docker-compose.yml` with postgres, redis, and backend services
2. PostgreSQL initialization scripts (if needed)
3. Redis configuration file
4. Environment variable templates
5. Volume mounts for data persistence

**Acceptance Criteria:**
- [ ] `docker-compose up -d postgres redis` starts both services
- [ ] PostgreSQL accessible on port 5432 with credentials
- [ ] Redis accessible on port 6379
- [ ] Health checks pass for both services
- [ ] Data persists after container restart
- [ ] Backend can connect to both PostgreSQL and Redis

**Docker Compose Configuration:**
```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: taps
      POSTGRES_USER: taps_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U taps_user -d taps"]
      interval: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

volumes:
  postgres_data:
  redis_data:
```

**Files to Create:**
- `docker-compose.yml`
- `.env.example` (with DB_PASSWORD, DATABASE_URL, REDIS_URL)
- `docker-compose.override.yml` (for local development)

---












**Objective:** Set up Alembic for database migrations and create initial migration from existing SQLAlchemy models.

**Scope:**
- Install and configure Alembic
- Create initial migration from existing models (Project, Module, Execution, Scenario)
- Add indexes for performance optimization
- Add full-text search index on scenarios.error (as per Plan Section 5.3 and 6.1)
- Configure async database connection for migrations

**Prerequisites:**
- PostgreSQL running (Task 1.3 completed)
- SQLAlchemy models defined in new structure (Task 1.2 completed)

**Deliverables:**
1. `backend/app/migrations/` directory with Alembic setup
2. `alembic.ini` configuration file
3. `env.py` configured for async migrations
4. Initial migration file with all tables and indexes (including full-text search index)
5. Migration scripts executable

**Acceptance Criteria:**
- [ ] `alembic init migrations` completes successfully
- [ ] `alembic revision --autogenerate -m "Initial migration"` creates migration
- [ ] `alembic upgrade head` applies migration to PostgreSQL
- [ ] All 4 tables created (projects, modules, executions, scenarios)
- [ ] All 8 standard indexes created as per migration plan
- [ ] Full-text search index created on scenarios.error column
- [ ] `alembic downgrade base` successfully rolls back

**Indexes to Create:**
```sql
-- Standard indexes (8 total)
CREATE INDEX idx_projects_name ON projects(name);
CREATE INDEX idx_projects_owner ON projects(owner);
CREATE INDEX idx_modules_project_id ON modules(project_id);
CREATE UNIQUE INDEX idx_modules_project_name ON modules(project_id, name);
CREATE INDEX idx_executions_module_id ON executions(module_id);
CREATE INDEX idx_executions_created_at ON executions(created_at DESC);
CREATE INDEX idx_scenarios_execution_id ON scenarios(execution_id);
CREATE INDEX idx_scenarios_status ON scenarios(status);

-- Full-text search index on scenarios.error (as per Plan Section 5.3 and 6.1)
CREATE INDEX idx_scenarios_error_fulltext ON scenarios USING gin(to_tsvector('english', error));
```

**Files to Create:**
- `backend/alembic.ini`
- `backend/app/migrations/env.py`
- `backend/app/migrations/versions/001_initial_migration.py` (includes full-text search index)
- `backend/app/migrations/README.md`

---

## Task 1.5: Set Up GitHub Actions CI/CD Pipeline

**Objective:** Create automated CI/CD pipeline for linting, testing, building, and deployment.

**Scope:**
- Configure GitHub Actions workflows for frontend and backend
- Set up linting (ESLint, Prettier, Ruff)
- Configure test execution (Jest, Pytest)
- Set up Docker image building
- Configure deployment to staging environment

**Prerequisites:**
- GitHub repository initialized
- Frontend and backend projects set up

**Deliverables:**
1. `.github/workflows/frontend-ci.yml` - Frontend CI workflow
2. `.github/workflows/backend-ci.yml` - Backend CI workflow
3. `.github/workflows/deploy-staging.yml` - Staging deployment workflow
4. GitHub Actions secrets configured
5. Status badges in README.md

**Acceptance Criteria:**
- [ ] Push to `main` branch triggers CI workflows
- [ ] Frontend workflow runs ESLint, Prettier, TypeScript check, Jest tests
- [ ] Backend workflow runs Ruff, Pytest, security scan
- [ ] Failed checks block PR merging
- [ ] Docker images built and pushed to registry on successful merge
- [ ] Deployment workflow triggers on tag creation

**Workflow Steps:**
1. Checkout code
2. Set up Node.js/Python
3. Install dependencies
4. Run linters
5. Run tests
6. Build Docker images
7. Push to container registry
8. Deploy to staging (on main branch)

**Files to Create:**
- `.github/workflows/frontend-ci.yml`
- `.github/workflows/backend-ci.yml`
- `.github/workflows/deploy-staging.yml`
- `.github/dependabot.yml`

---

## Task 1.6: Configure Code Quality Tools (ESLint, Prettier, Ruff)

**Objective:** Set up and configure linting and formatting tools for both frontend and backend.

**Scope:**
- Configure ESLint for Next.js/React/TypeScript
- Configure Prettier for consistent code formatting
- Configure Ruff for Python linting
- Set up pre-commit hooks with Husky
- Add VS Code workspace settings

**Prerequisites:**
- Frontend project initialized (Task 1.1)
- Backend project structured (Task 1.2)

**Deliverables:**
1. `frontend/.eslintrc.json` with Next.js + TypeScript rules
2. `frontend/.prettierrc` with formatting rules
3. `backend/pyproject.toml` with Ruff configuration
4. `.husky/` directory with pre-commit hooks
5. `.vscode/settings.json` with editor configuration
6. `package.json` scripts for linting

**Acceptance Criteria:**
- [ ] `npm run lint` in frontend runs ESLint successfully
- [ ] `npm run format` in frontend runs Prettier
- [ ] `ruff check .` in backend runs without errors
- [ ] Pre-commit hook prevents commits with linting errors
- [ ] VS Code auto-formats on save
- [ ] All existing code passes linting rules

**ESLint Configuration:**
```json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended",
    "prettier"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "warn"
  }
}
```

**Ruff Configuration (pyproject.toml):**
```toml
[tool.ruff]
line-length = 100
target-version = "py312"
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]
```

**Files to Create:**
- `frontend/.eslintrc.json`
- `frontend/.prettierrc`
- `frontend/.prettierignore`
- `backend/pyproject.toml`
- `backend/.ruff.toml`
- `.husky/pre-commit`
- `.vscode/settings.json`

---

## Task 1.7: Set Up Environment Management

**Objective:** Configure environment variable management for all environments (dev, staging, production).

**Scope:**
- Create `.env.example` templates for frontend and backend
- Configure pydantic-settings for backend configuration
- Set up Next.js environment variables
- Document all required environment variables
- Create environment-specific configuration files

**Prerequisites:**
- Frontend and backend projects initialized

**Deliverables:**
1. `frontend/.env.example` with all frontend environment variables
2. `backend/.env.example` with all backend environment variables
3. `backend/app/config.py` using pydantic-settings
4. `docs/environment-variables.md` documentation
5. `.gitignore` updated to exclude `.env` files

**Acceptance Criteria:**
- [ ] All environment variables documented
- [ ] Backend config loaded via pydantic-settings
- [ ] Frontend environment variables prefixed with `NEXT_PUBLIC_`
- [ ] Default values provided for development
- [ ] Validation errors raised for missing required variables
- [ ] No secrets committed to repository

**Backend Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://taps_user:password@localhost:5432/taps
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# Authentication
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# CORS
ALLOWED_ORIGINS=http://localhost:3000
```

**Frontend Environment Variables:**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1/ws
NEXT_PUBLIC_ENVIRONMENT=development
```

**Files to Create:**
- `frontend/.env.example`
- `frontend/.env.local` (gitignored)
- `backend/.env.example`
- `backend/.env` (gitignored)
- `backend/app/config.py`
- `docs/environment-variables.md`

---

## Task 1.8: Migrate SQLite Data to PostgreSQL

**Objective:** Export data from existing SQLite database and import into PostgreSQL.

**Scope:**
- Create data export script from SQLite
- Transform data to match PostgreSQL schema
- Create data import script for PostgreSQL
- Validate data integrity after migration
- Create rollback plan

**Prerequisites:**
- PostgreSQL running with schema applied (Task 1.3, 1.4 completed)
- Existing SQLite database (`test_portal.db`)

**Deliverables:**
1. `scripts/export_sqlite_data.py` - Export script
2. `scripts/import_postgres_data.py` - Import script
3. `data/migration/` directory with exported data (CSV/JSON)
4. `scripts/validate_migration.py` - Validation script
5. Migration execution log
6. Rollback instructions

**Acceptance Criteria:**
- [ ] All data exported from SQLite to intermediate format
- [ ] Row counts match between SQLite and PostgreSQL
- [ ] Foreign key relationships preserved
- [ ] Timestamps converted correctly
- [ ] No data loss or corruption
- [ ] Validation script confirms 100% data integrity
- [ ] SQLite backup created before migration

**Migration Steps:**
1. Backup SQLite database
2. Export tables to CSV/JSON:
   - projects
   - modules
   - executions
   - scenarios
3. Transform data (UUID generation, timestamp conversion)
4. Import into PostgreSQL tables
5. Validate row counts and relationships
6. Run consistency checks

**Validation Checks:**
- Row count comparison
- Foreign key integrity
- Data type correctness
- Null value handling
- Unique constraint validation

**Files to Create:**
- `scripts/export_sqlite_data.py`
- `scripts/import_postgres_data.py`
- `scripts/validate_migration.py`
- `scripts/rollback_migration.sh`
- `data/migration/projects.csv`
- `data/migration/modules.csv`
- `data/migration/executions.csv`
- `data/migration/scenarios.csv`
- `docs/migration-log.md`

---

# PHASE 2: BACKEND API MIGRATION

## Task 2.2: Implement JWT Authentication and User Management (RENUMBERED FROM 2.1)

**Objective:** Add secure authentication system with JWT tokens and user management under /api/v1/auth.

**Scope:**
- Create User model and database table
- Implement JWT token generation and validation
- Create authentication endpoints (register, login, refresh token)
- Add password hashing with bcrypt
- Implement authentication middleware
- Create user CRUD operations

**Prerequisites:**
- Backend modular structure in place (Task 1.2)
- PostgreSQL running (Task 1.3)
- Alembic configured (Task 1.4)
- API versioning structure set up (Task 2.1)

**Deliverables:**
1. `app/auth/models.py` - User model
2. `app/auth/schemas.py` - Auth request/response schemas
3. `app/auth/service.py` - JWT service, password hashing
4. `app/auth/router.py` - Auth endpoints
5. `app/auth/middleware.py` - Authentication middleware
6. `app/auth/dependencies.py` - get_current_user dependency
7. Alembic migration for users table
8. Unit tests for authentication

**Acceptance Criteria:**
- [ ] `POST /api/v1/auth/register` creates new user with hashed password
- [ ] `POST /api/v1/auth/login` returns JWT access token
- [ ] `POST /api/v1/auth/refresh` refreshes access token
- [ ] `GET /api/v1/auth/me` returns current user (requires auth)
- [ ] Invalid credentials return 401 Unauthorized
- [ ] Expired tokens return 401 Unauthorized
- [ ] Passwords hashed with bcrypt (never stored plain text)
- [ ] All auth tests passing

**API Endpoints:**
```python
POST /api/v1/auth/register
  Request: {"email": "user@example.com", "password": "...", "full_name": "..."}
  Response: {"id": "...", "email": "...", "full_name": "...", "role": "viewer"}

POST /api/v1/auth/login
  Request: {"email": "user@example.com", "password": "..."}
  Response: {"access_token": "...", "token_type": "bearer", "expires_in": 1800}

POST /api/v1/auth/refresh
  Request: {"refresh_token": "..."}
  Response: {"access_token": "...", "token_type": "bearer", "expires_in": 1800}

GET /api/v1/auth/me
  Headers: {"Authorization": "Bearer <token>"}
  Response: {"id": "...", "email": "...", "full_name": "...", "role": "..."}
```

**User Model Schema:**
```python
class User(Base):
    id: UUID (PK)
    email: str (unique, indexed)
    hashed_password: str
    full_name: str
    role: str (admin, manager, viewer)
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime (nullable)
```

**Files to Create:**
- `backend/app/auth/models.py`
- `backend/app/auth/schemas.py`
- `backend/app/auth/service.py`
- `backend/app/auth/router.py`
- `backend/app/auth/middleware.py`
- `backend/app/auth/dependencies.py`
- `backend/app/migrations/versions/002_add_users_table.py`
- `backend/tests/test_auth.py`

---

## Task 2.3: Migrate Projects API with Repository Pattern (RENUMBERED FROM 2.2)

**Objective:** Refactor Projects API to use repository pattern and fix N+1 query problem under /api/v1/projects.

**Scope:**
- Create ProjectRepository with optimized queries
- Implement single-query project listing (fix N+1)
- Add pagination, sorting, and filtering
- Migrate all project endpoints to new structure
- Add authentication to endpoints
- Implement caching layer

**Prerequisites:**
- Backend structure in place (Task 1.2)
- API versioning structure set up (Task 2.1)
- Authentication implemented (Task 2.2)
- Redis running (Task 1.3)

**Deliverables:**
1. `app/projects/repository.py` - Data access layer
2. `app/projects/service.py` - Business logic
3. `app/projects/router.py` - API endpoints
4. `app/projects/schemas.py` - Pydantic schemas
5. Optimized SQL queries (single query for project listing)
6. Unit and integration tests

**Acceptance Criteria:**
- [ ] `GET /api/v1/projects` returns paginated projects list
- [ ] Project listing executes 1 query instead of 3N queries
- [ ] `GET /api/v1/projects/{id}` returns single project with modules
- [ ] `POST /api/v1/projects` creates new project (requires auth)
- [ ] `PUT /api/v1/projects/{id}` updates project (requires auth)
- [ ] `DELETE /api/v1/projects/{id}` soft-deletes project (requires auth)
- [ ] Pagination works with `?page=1&size=20`
- [ ] Filtering works with `?is_active=true&owner=user@example.com`
- [ ] Response time < 100ms for project listing (with cache)

**Optimized Query (Fix N+1):**
```python
# Before (POC): 1 + 3N queries
for project in projects:  # 1 query
    count_modules()       # N queries
    sum_executions()      # N queries
    get_last_run()        # N queries

# After (Production): 1 query with JOINs
stmt = (
    select(
        Project,
        func.count(distinct(Module.id)).label("modules_count"),
        func.sum(Execution.total).label("total_tests"),
        func.sum(Execution.passed).label("passed_tests"),
        func.max(Execution.created_at).label("last_run"),
    )
    .outerjoin(Module, Module.project_id == Project.id)
    .outerjoin(Execution, Execution.module_id == Module.id)
    .group_by(Project.id)
)
```

**API Endpoints:**
```python
GET /api/v1/projects?page=1&size=20&is_active=true
GET /api/v1/projects/{id}
GET /api/v1/projects/{id}/modules
POST /api/v1/projects
PUT /api/v1/projects/{id}
DELETE /api/v1/projects/{id}
```

**Files to Create:**
- `backend/app/projects/repository.py`
- `backend/app/projects/service.py`
- `backend/app/projects/router.py`
- `backend/app/projects/schemas.py`
- `backend/tests/test_projects.py`

---

## Task 2.4: Migrate Report Upload API with Background Processing and Persistent Status Tracking (RENUMBERED FROM 2.3)

**Objective:** Refactor report upload endpoint to use background task processing with Redis-backed persistent progress tracking.

**Scope:**
- Move Cucumber parser to new structure
- Implement background task for report processing
- Add Redis-backed upload progress tracking (persistent across requests/restarts)
- Support async file processing
- Add validation for uploaded files
- Implement error handling and retry logic
- Store task status in Redis with TTL

**Prerequisites:**
- Backend structure in place (Task 1.2)
- API versioning structure set up (Task 2.1)
- Authentication implemented (Task 2.2)
- Redis running (Task 1.3)

**Deliverables:**
1. `app/reports/router.py` - Upload endpoints under /api/v1/reports
2. `app/reports/service.py` - Report processing logic
3. `app/reports/parsers/base.py` - Abstract parser interface
4. `app/reports/parsers/cucumber.py` - Cucumber parser (from POC)
5. `app/reports/schemas.py` - Request/response schemas
6. Background task implementation with FastAPI BackgroundTasks
7. Redis-backed progress tracking mechanism (persistent)
8. `app/reports/task_status.py` - Redis task status storage
9. Unit tests for parser, service, and task status tracking

**Acceptance Criteria:**
- [ ] `POST /api/v1/reports/upload` accepts Cucumber JSON file
- [ ] Upload returns immediately with task_id for tracking
- [ ] `GET /api/v1/reports/upload/{task_id}/status` returns progress from Redis
- [ ] Task status persists in Redis (survives request completion and server restarts)
- [ ] Task status has appropriate TTL (e.g., 24 hours)
- [ ] File validation rejects invalid formats
- [ ] Parser extracts all metrics correctly
- [ ] Database updated with execution and scenario data
- [ ] Error handling for malformed JSON
- [ ] Support for large files (>10MB)
- [ ] Status includes: task_id, status (processing/completed/failed), progress %, result/error

**API Endpoints:**
```python
POST /api/v1/reports/upload
  Request: multipart/form-data with file
  Response: {"task_id": "...", "status": "processing"}

GET /api/v1/reports/upload/{task_id}/status
  Response: {
    "task_id": "...",
    "status": "completed|processing|failed",
    "progress": 100,
    "result": {"execution_id": "...", "scenarios_processed": 45},
    "error": "..." (if failed)
  }
  # Status retrieved from Redis, persists across requests
```

**Background Task Flow with Redis Status Tracking:**
1. Receive file upload
2. Validate file format and size
3. Generate unique task_id
4. Store initial task status in Redis: {"task_id": "...", "status": "processing", "progress": 0}
5. Create FastAPI background task
6. Return task_id immediately to client
7. Process file asynchronously in background:
   - Parse JSON
   - Extract metrics
   - Update Redis status with progress: {"status": "processing", "progress": 50}
   - Create/update database records
   - Update Redis status on completion: {"status": "completed", "progress": 100, "result": {...}}
8. Handle errors and update Redis status: {"status": "failed", "error": "..."}
9. Set Redis TTL for task status (e.g., 24 hours)

**Redis Task Status Storage:**
```python
# app/reports/task_status.py
class TaskStatusService:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def set_status(self, task_id: str, status: dict, ttl: int = 86400):
        """Store task status in Redis with TTL (default 24 hours)"""
        await self.redis.setex(
            f"task_status:{task_id}",
            ttl,
            json.dumps(status)
        )
    
    async def get_status(self, task_id: str) -> dict | None:
        """Retrieve task status from Redis"""
        data = await self.redis.get(f"task_status:{task_id}")
        return json.loads(data) if data else None
```

**Files to Create:**
- `backend/app/reports/router.py`
- `backend/app/reports/service.py`
- `backend/app/reports/parsers/base.py`
- `backend/app/reports/parsers/cucumber.py`
- `backend/app/reports/schemas.py`
- `backend/app/reports/task_status.py` - Redis-backed task status storage
- `backend/app/core/tasks.py`
- `backend/tests/test_reports.py`
- `backend/tests/test_task_status.py` - Test Redis status persistence
- `backend/tests/fixtures/sample_cucumber_report.json`

---

## Task 2.5: Migrate Execution API with Redis Caching (RENUMBERED FROM 2.4)

**Objective:** Refactor execution endpoints with optimized queries and Redis caching under /api/v1/executions and /api/v1/modules.

**Scope:**
- Create ExecutionRepository with optimized queries
- Implement Redis caching for execution data (NOTE: cache.py created in Task 2.5, not duplicated in Task 5.1)
- Consolidate duplicate endpoints
- Add pagination and filtering
- Implement cache invalidation on data mutation

**Prerequisites:**
- Backend structure in place (Task 1.2)
- API versioning structure set up (Task 2.1)
- Redis running and configured (Task 1.3)
- Authentication implemented (Task 2.2)

**Deliverables:**
1. `app/executions/repository.py` - Data access layer
2. `app/executions/service.py` - Business logic with caching
3. `app/executions/router.py` - Consolidated API endpoints
4. `app/executions/schemas.py` - Pydantic schemas
5. `app/core/cache.py` - Redis cache service (CREATED HERE - Layer 3 of caching strategy)
6. Cache invalidation logic
7. Unit and integration tests

**Acceptance Criteria:**
- [ ] `GET /api/v1/projects/{id}/executions` returns paginated executions
- [ ] `GET /api/v1/modules/{id}/executions` returns module executions
- [ ] `GET /api/v1/executions/{id}` returns single execution
- [ ] `GET /api/v1/executions/{id}/scenarios` returns scenarios with pagination
- [ ] Cached responses return in < 10ms
- [ ] Cache invalidated on new report upload
- [ ] Filtering by status, date range works
- [ ] All tests passing

**Caching Strategy:**
```python
# Cache keys
executions:project:{project_id}:page:{page}  # TTL: 2 min
executions:module:{module_id}:page:{page}    # TTL: 2 min
execution:{execution_id}                     # TTL: 5 min
scenarios:execution:{execution_id}:page:{page} # TTL: 5 min

# Invalidation triggers
- On report upload: invalidate executions:project:*, executions:module:*
- On execution update: invalidate execution:{id}, scenarios:execution:{id}:*
```

**API Endpoints (Consolidated):**
```python
GET /api/v1/projects/{id}/executions?page=1&size=20&status=passed
GET /api/v1/modules/{id}/executions?page=1&size=20
GET /api/v1/executions/{id}
GET /api/v1/executions/{id}/scenarios?page=1&size=50&status=failed
```

**Files to Create:**
- `backend/app/executions/repository.py`
- `backend/app/executions/service.py`
- `backend/app/executions/router.py`
- `backend/app/executions/schemas.py`
- `backend/app/core/cache.py`
- `backend/tests/test_executions.py`
- `backend/tests/test_cache.py`

---

## Task 2.6: Implement Defect Management API (Replace Mock Data) (RENUMBERED FROM 2.5)

**Objective:** Create full CRUD API for defect management to replace POC mock data under /api/v1/defects.

**Scope:**
- Create Defect model and database table
- Implement CRUD operations for defects
- Link defects to scenarios and modules
- Add status workflow (Open → In Progress → Fixed → Closed)
- Implement filtering and search
- Add defect assignment functionality

**Prerequisites:**
- Backend structure in place (Task 1.2)
- API versioning structure set up (Task 2.1)
- Authentication implemented (Task 2.2)
- PostgreSQL running (Task 1.3)

**Deliverables:**
1. `app/defects/models.py` - Defect model
2. `app/defects/schemas.py` - Pydantic schemas
3. `app/defects/repository.py` - Data access layer
4. `app/defects/service.py` - Business logic
5. `app/defects/router.py` - API endpoints
6. Alembic migration for defects table
7. Unit and integration tests

**Acceptance Criteria:**
- [ ] `GET /api/v1/defects` returns paginated defects list
- [ ] `GET /api/v1/defects/{id}` returns single defect
- [ ] `POST /api/v1/defects` creates new defect
- [ ] `PUT /api/v1/defects/{id}` updates defect
- [ ] `DELETE /api/v1/defects/{id}` deletes defect
- [ ] `GET /api/v1/scenarios/{id}/defects` returns linked defects
- [ ] Filtering by status, severity, priority works
- [ ] Search by title/description works
- [ ] Status transitions validated

**Defect Model Schema:**
```python
class Defect(Base):
    id: UUID (PK)
    title: str (max 500 chars)
    description: str (text)
    severity: str (Critical, High, Medium, Low)
    priority: str (P0, P1, P2, P3)
    status: str (Open, In Progress, Fixed, Closed, Won't Fix)
    assigned_to: str (nullable)
    reported_by: str
    project_id: UUID (FK to projects)
    module_id: UUID (FK to modules, nullable)
    scenario_id: UUID (FK to scenarios, nullable)
    resolution: str (text, nullable)
    created_at: datetime
    updated_at: datetime
    closed_at: datetime (nullable)
```

**API Endpoints:**
```python
GET /api/v1/defects?status=Open&severity=Critical&page=1&size=20
GET /api/v1/defects/{id}
POST /api/v1/defects
PUT /api/v1/defects/{id}
DELETE /api/v1/defects/{id}
GET /api/v1/scenarios/{id}/defects
POST /api/v1/defects/{id}/assign
PUT /api/v1/defects/{id}/status
```

**Files to Create:**
- `backend/app/defects/models.py`
- `backend/app/defects/schemas.py`
- `backend/app/defects/repository.py`
- `backend/app/defects/service.py`
- `backend/app/defects/router.py`
- `backend/app/migrations/versions/003_add_defects_table.py`
- `backend/tests/test_defects.py`

---

## Task 2.1: Implement API Versioning (MOVED TO START OF PHASE 2)

**Objective:** Add API versioning with `/api/v1/` prefix to all endpoints BEFORE implementing individual endpoints.

**Scope:**
- Set up API versioning structure with `/api/v1` prefix
- Create versioning middleware
- Configure router registration pattern
- Update API documentation structure
- Ensure backward compatibility strategy
- Add version negotiation logic

**Prerequisites:**
- Backend modular structure in place (Task 1.2)
- PostgreSQL running (Task 1.3)
- Alembic configured (Task 1.4)

**Deliverables:**
1. API versioning structure with `/api/v1` prefix configured in main.py
2. API versioning middleware
3. Router registration pattern established
4. OpenAPI documentation structure configured
5. Version negotiation logic
6. Documentation on versioning strategy

**Acceptance Criteria:**
- [ ] API versioning structure set up with `/api/v1/` prefix
- [ ] OpenAPI docs configured at `/api/v1/docs`
- [ ] Version header support (`API-Version: v1`) implemented
- [ ] 404 response for unsupported versions
- [ ] Health endpoint configured at `/api/v1/health`
- [ ] Router registration pattern documented for subsequent tasks

**Router Registration Pattern (to be followed by all subsequent endpoint tasks):**
```python
# app/main.py
api_v1_router = APIRouter(prefix="/api/v1")

# Subsequent tasks will add routers following this pattern:
# api_v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
# api_v1_router.include_router(projects_router, prefix="/projects", tags=["projects"])
# api_v1_router.include_router(executions_router, prefix="/executions", tags=["executions"])
# api_v1_router.include_router(reports_router, prefix="/reports", tags=["reports"])
# api_v1_router.include_router(defects_router, prefix="/defects", tags=["defects"])

app.include_router(api_v1_router)
```

**Files to Create/Modify:**
- `backend/app/main.py` (create versioning structure)
- `backend/app/core/middleware.py` (add version negotiation middleware)
- `docs/api-versioning-strategy.md`

---

## Task 2.7: Implement Rate Limiting and Request Validation (UNCHANGED NUMBER)

**Objective:** Add rate limiting and comprehensive request validation middleware.

**Scope:**
- Implement rate limiting middleware (per IP, per user)
- Add request size limits
- Implement request validation middleware
- Add CORS configuration
- Implement security headers

**Prerequisites:**
- Backend structure in place (Task 1.2)
- API versioning structure set up (Task 2.1)
- Redis running (Task 1.3)
- Authentication implemented (Task 2.2)

**Deliverables:**
1. `app/core/middleware.py` - Rate limiting middleware
2. `app/core/validators.py` - Request validators
3. Updated CORS configuration
4. Security headers middleware
5. Configuration for rate limits
6. Unit tests for middleware

**Acceptance Criteria:**
- [ ] Rate limiting enforced (100 requests/minute per IP)
- [ ] Authenticated users get higher limits (1000 requests/minute)
- [ ] 429 Too Many Requests returned when limit exceeded
- [ ] Request size limited to 10MB
- [ ] CORS configured with allowed origins from environment
- [ ] Security headers added (HSTS, CSP, X-Frame-Options)
- [ ] All tests passing

**Rate Limiting Strategy:**
```python
# Anonymous users: 100 requests/minute per IP
# Authenticated users: 1000 requests/minute per user
# Upload endpoints: 10 requests/hour per user
# Redis key: rate_limit:{ip|user_id}:{endpoint}
```

**Security Headers:**
```python
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

**Files to Create:**
- `backend/app/core/middleware.py`
- `backend/app/core/validators.py`
- `backend/app/core/rate_limiter.py`
- `backend/tests/test_middleware.py`

---

## Task 2.8: Set Up Structured Logging with Correlation IDs

**Objective:** Implement structured logging with correlation IDs for request tracing.

**Scope:**
- Configure structlog for JSON logging
- Add correlation ID middleware
- Implement log levels (DEBUG, INFO, WARNING, ERROR)
- Add request/response logging
- Configure log output format
- Add error tracking

**Prerequisites:**
- Backend structure in place (Task 1.2)

**Deliverables:**
1. `app/core/logging.py` - Logging configuration
2. `app/core/middleware.py` - Correlation ID middleware
3. Structured log format (JSON)
4. Request/response logging
5. Error logging with stack traces
6. Log configuration per environment

**Acceptance Criteria:**
- [ ] All logs output in JSON format
- [ ] Each request has unique correlation ID
- [ ] Correlation ID included in all log entries
- [ ] Request/response logged with duration
- [ ] Errors logged with stack traces
- [ ] Log level configurable via environment variable
- [ ] Sensitive data (passwords, tokens) redacted from logs

**Log Format:**
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "correlation_id": "abc123-def456-ghi789",
  "service": "taps-backend",
  "endpoint": "/api/v1/projects",
  "method": "GET",
  "status_code": 200,
  "duration_ms": 45,
  "user_id": "user-uuid",
  "message": "Request completed"
}
```

**Files to Create:**
- `backend/app/core/logging.py`
- `backend/app/core/middleware.py` (update)
- `backend/tests/test_logging.py`

---

## Task 2.9: Fix N+1 Queries in Projects Listing (UNCHANGED NUMBER)

**Objective:** Optimize project listing query to execute in single database query.

**Scope:**
- Analyze current query pattern
- Rewrite query with JOINs and aggregations
- Add selectinload for relationships
- Benchmark performance improvement
- Update tests

**Prerequisites:**
- Projects API migrated (Task 2.3)

**Deliverables:**
1. Optimized query in `app/projects/repository.py`
2. Performance benchmark results
3. Updated unit tests
4. Query execution plan documentation

**Acceptance Criteria:**
- [ ] Project listing executes exactly 1 SQL query
- [ ] Query includes all required data (modules count, test stats, last run)
- [ ] Response time < 50ms for 100 projects (without cache)
- [ ] Response time < 10ms with Redis cache
- [ ] All existing tests passing
- [ ] Performance improvement documented

**Optimized Query:**
```python
stmt = (
    select(
        Project,
        func.count(distinct(Module.id)).label("modules_count"),
        func.sum(Execution.total).label("total_tests"),
        func.sum(Execution.passed).label("passed_tests"),
        func.sum(Execution.failed).label("failed_tests"),
        func.max(Execution.created_at).label("last_run"),
    )
    .outerjoin(Module, Module.project_id == Project.id)
    .outerjoin(Execution, Execution.module_id == Module.id)
    .where(Project.is_active == True)
    .group_by(Project.id)
    .options(selectinload(Project.modules))
)
```

**Performance Benchmark:**
- Before: 1 + 3N queries (301 queries for 100 projects)
- After: 1 query
- Expected speedup: 50-100x

**Files to Modify:**
- `backend/app/projects/repository.py`
- `backend/tests/test_projects.py`
- `docs/performance-benchmarks.md`

---

## Task 2.10: Write Pytest Unit and Integration Tests for Backend

**Objective:** Achieve 85%+ test coverage for backend with unit and integration tests.

**Scope:**
- Write unit tests for all services
- Write integration tests for all API endpoints
- Set up test database and fixtures
- Configure pytest with coverage reporting
- Add test data factories
- Mock external dependencies

**Prerequisites:**
- All backend APIs implemented (Tasks 2.1-2.9)

**Deliverables:**
1. `tests/conftest.py` - Pytest configuration and fixtures
2. `tests/unit/` - Unit tests for services, parsers, utilities
3. `tests/integration/` - Integration tests for API endpoints
4. `tests/factories.py` - Test data factories
5. Coverage report (>85%)
6. CI integration for test execution

**Acceptance Criteria:**
- [ ] All API endpoints have integration tests
- [ ] All services have unit tests
- [ ] Test coverage > 85%
- [ ] All tests pass in CI pipeline
- [ ] Test database isolated from development database
- [ ] Fixtures for common test data
- [ ] Mock external services (AI, email, etc.)

**Test Structure:**
```
tests/
├── conftest.py              # Fixtures, test client, test DB
├── factories.py             # Data factories (User, Project, etc.)
├── unit/
│   ├── test_auth_service.py
│   ├── test_project_service.py
│   ├── test_execution_service.py
│   ├── test_report_service.py
│   ├── test_defect_service.py
│   ├── test_cucumber_parser.py
│   └── test_cache.py
└── integration/
    ├── test_auth_api.py
    ├── test_projects_api.py
    ├── test_executions_api.py
    ├── test_reports_api.py
    └── test_defects_api.py
```

**Test Coverage Requirements:**
- Services: 90%+
- Routers: 85%+
- Parsers: 95%+
- Utilities: 90%+
- Overall: 85%+

**Files to Create:**
- `backend/tests/conftest.py`
- `backend/tests/factories.py`
- `backend/tests/unit/*.py` (7 files)
- `backend/tests/integration/*.py` (5 files)
- `backend/pytest.ini`
- `backend/.coveragerc`

---

# PHASE 3: FRONTEND MIGRATION

## Task 3.1: Build Shared Layout (Sidebar, Header, Providers)

**Objective:** Create shared layout components and context providers matching the exact demo app specifications.

**Scope:**
- Build root layout with providers
- Create collapsible sidebar component with exact demo app styling
- Build header/navbar component (4rem height)
- Set up TanStack Query provider
- Set up theme provider
- Create layout templates with dynamic margin-left based on sidebar state

**Prerequisites:**
- Frontend project initialized (Task 1.1)
- Backend API running (Phase 2 completed)

**Deliverables:**
1. `src/app/layout.tsx` - Root layout with providers
2. `src/components/organisms/Sidebar.tsx` - Collapsible sidebar with exact demo app specs
3. `src/components/organisms/Header.tsx` - Header/navbar (4rem height)
4. `src/components/templates/DashboardLayout.tsx` - Dashboard layout template
5. `src/lib/providers.tsx` - All context providers
6. `src/styles/globals.css` - Global styles and design tokens matching demo app

**Acceptance Criteria:**
- [ ] Sidebar renders with navigation links matching demo app
- [ ] Sidebar: 80px collapsed → 280px expanded on hover (transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1))
- [ ] Sidebar gradient background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%)
- [ ] Active nav link gradient: linear-gradient(90deg, #10b981, #059669) with shadow: 0 4px 12px rgba(16, 185, 129, 0.3)
- [ ] Nav link hover: background rgba(16, 185, 129, 0.15), transform translateX(4px)
- [ ] Header height: 4rem (64px)
- [ ] Layout margin-left: 80px (collapsed) → 280px (expanded on sidebar hover)
- [ ] Responsive layout: mobile drawer (< 768px), desktop sidebar (≥ 768px)
- [ ] TanStack Query provider configured (staleTime: 5min, gcTime: 30min, retry: 3)
- [ ] Theme provider supports light/dark mode
- [ ] Font family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
- [ ] Layout persists across page navigation

**Sidebar Exact Specifications (from Demo App):**
```typescript
// Sidebar Dimensions
const sidebarSpecs = {
  collapsedWidth: "80px",
  expandedWidth: "280px",
  headerHeight: "80px",
  footerHeight: "80px",
  transition: "0.3s cubic-bezier(0.4, 0, 0.2, 1)",
};

// Sidebar Gradient Colors
const sidebarGradient = "linear-gradient(180deg, #1e293b 0%, #0f172a 100%)";

// Active Nav Link Styling
const activeNavLink = {
  background: "linear-gradient(90deg, #10b981, #059669)",
  color: "white",
  boxShadow: "0 4px 12px rgba(16, 185, 129, 0.3)",
};

// Nav Link Hover
const navLinkHover = {
  background: "rgba(16, 185, 129, 0.15)",
  color: "#10b981",
  transform: "translateX(4px)",
};

// Nav Icon Wrapper
const navIconWrapper = {
  position: "absolute",
  left: "12px",
  fontSize: "1.2rem",
};

// Nav Text (hidden when collapsed)
const navText = {
  opacity: 0,
  width: 0,
  marginLeft: "48px",
  transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
  // On hover: opacity: 1, width: auto
};
```

**Sidebar Navigation Items (from Demo App):**
```typescript
const navItems = [
  { name: "Projects", href: "/projects", icon: "fas fa-project-diagram" },
  { name: "Execution Summary", href: "/execution-summary", icon: "fas fa-chart-line" },
  { name: "Trends", href: "/trends", icon: "fas fa-chart-bar" },
  { name: "Module Details", href: "/module-details", icon: "fas fa-cogs" },
  { name: "Defect Management", href: "/defect-management", icon: "fas fa-bug" },
  { name: "AI Insights", href: "/ai-failure-analysis", icon: "fas fa-brain" },
  { name: "Settings", href: "/settings", icon: "fas fa-gear" },
];
```

**Layout Margin-Left Dynamics:**
```css
.page-content {
  margin-left: 80px;
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 100vh;
  padding: 2rem;
  background-color: #f8fafc;
}

.sidebar-professional:hover ~ .page-content {
  margin-left: 280px;
}
```

**Typography (from Demo App):**
```css
/* Font Family */
font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 0.95rem;  /* 15px */
--text-lg: 1.1rem;     /* 18px */
--text-xl: 1.5rem;     /* 24px */
--text-2xl: 2rem;      /* 32px */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

**Providers Setup:**
```typescript
<TanStackQueryProvider
  config={{
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000,  // 5 minutes
        gcTime: 30 * 60 * 1000,     // 30 minutes
        retry: 3,
        refetchOnWindowFocus: true,
      },
    },
  }}
>
  <ThemeProvider>
    <AuthProvider>
      <ToastProvider>
        {children}
      </ToastProvider>
    </AuthProvider>
  </ThemeProvider>
</TanStackQueryProvider>
```

**Tailwind CSS Classes (Demo App Equivalents):**
```typescript
// Sidebar collapsed
"fixed top-0 left-0 h-screen w-20 bg-gradient-to-b from-slate-800 to-slate-900 transition-all duration-300"

// Sidebar expanded (on hover)
"hover:w-70"

// Active nav link
"flex items-center px-4 py-3 mx-3 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 text-white shadow-lg shadow-emerald-500/30"

// Nav link hover
"hover:bg-emerald-500/15 hover:text-emerald-500 hover:translate-x-1"
```

**Files to Create:**
- `frontend/src/app/layout.tsx`
- `frontend/src/components/organisms/Sidebar.tsx`
- `frontend/src/components/organisms/Header.tsx`
- `frontend/src/components/templates/DashboardLayout.tsx`
- `frontend/src/lib/providers.tsx`
- `frontend/src/styles/globals.css`

---

## Task 3.2: Build Atom Components

**Objective:** Create reusable atomic UI components matching exact demo app specifications.

**Scope:**
- Install and configure shadcn/ui components
- Create custom atom components with exact demo app styling
- Build SummaryCard component (white card with hover lift)
- Build StatusBadge component (emoji icons with colored backgrounds)
- Build StatusDot component (pulsing animation)
- Build Button variants matching demo app
- Build Input fields with demo app styling
- Build FilterRow component
- Add component documentation

**Prerequisites:**
- Frontend project initialized (Task 1.1)
- shadcn/ui configured

**Deliverables:**
1. `src/components/atoms/SummaryCard.tsx` - White card with hover effects
2. `src/components/atoms/StatusBadge.tsx` - Status badges with emoji icons
3. `src/components/atoms/StatusDot.tsx` - Pulsing status indicator
4. `src/components/atoms/Button.tsx` - Button variants from demo app
5. `src/components/atoms/Input.tsx` - Input fields with demo app styling
6. `src/components/atoms/FilterRow.tsx` - Grey background filter section
7. `src/components/atoms/LoadingSkeleton.tsx` - Loading states
8. Component documentation

**Acceptance Criteria:**
- [ ] SummaryCard: white background, shadow-md, hover: translateY(-5px) + shadow-xl
- [ ] StatusBadge: emoji icons (✅ ⚠️ ❌ ⬜), colored backgrounds (green/yellow/red/grey)
- [ ] StatusDot: 8px circle, pulsing animation (2s infinite), box-shadow glow
- [ ] Button variants: primary, outline-primary, outline-secondary, outline-info, outline-warning
- [ ] Input fields: 6-8px border-radius, proper focus states
- [ ] FilterRow: grey background (#f1f5f9), 20px padding, 8px border-radius
- [ ] All components fully typed with TypeScript
- [ ] Components accessible (ARIA labels, keyboard navigation)

**SummaryCard Component (from Demo App):**
```typescript
interface SummaryCardProps {
  children: React.ReactNode;
  className?: string;
}

// Exact styling from demo app:
const summaryCardStyles = {
  borderRadius: "10px",
  boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
  border: "none",
  backgroundColor: "white",
  transition: "transform 0.2s",
  // Hover state:
  hover: {
    transform: "translateY(-5px)",
    boxShadow: "0 10px 20px rgba(0, 0, 0, 0.12)",
  },
};

// Tailwind equivalent:
"rounded-xl shadow-md border-none bg-white transition-transform hover:-translate-y-1 hover:shadow-xl"

// Usage:
<SummaryCard>
  <div className="flex justify-between items-center">
    <div>
      <h4 className="text-2xl font-bold mb-1">{value}</h4>
      <p className="text-slate-500 text-sm">{label}</p>
    </div>
    <div>
      <Icon className="text-2xl" style={{ color }} />
    </div>
  </div>
</SummaryCard>
```

**StatusBadge Component (from Demo App):**
```typescript
type StatusType = "green" | "yellow" | "red" | "grey";

interface StatusBadgeProps {
  status: StatusType;
  label: string;
}

// Emoji icons mapping
const statusIcons = {
  green: "✅",   // Check mark
  yellow: "⚠️",  // Warning
  red: "❌",     // Cross mark
  grey: "⬜",    // White square
};

// Background colors
const statusColors = {
  green: { bg: "#ecfdf5", text: "#10b981" },
  yellow: { bg: "#fffbeb", text: "#f59e0b" },
  red: { bg: "#fef2f2", text: "#ef4444" },
  grey: { bg: "#f1f5f9", text: "#94a3b8" },
};

// Tailwind equivalent:
"flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs"

// Usage:
<StatusBadge status="green" label="Active" />
// Renders: ✅ Active (with green background)
```

**StatusDot Component (from Demo App):**
```typescript
interface StatusDotProps {
  color: string;  // e.g., "#10b981", "#f59e0b", "#ef4444"
}

const statusDotStyles = {
  width: "8px",
  height: "8px",
  borderRadius: "50%",
  backgroundColor: color,
  boxShadow: `0 0 8px ${color}`,
  animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
};

// Pulsing animation (from demo app):
@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.3);
  }
}

// Tailwind equivalent:
"w-2 h-2 rounded-full animate-pulse"
// Plus custom shadow: style={{ boxShadow: `0 0 8px ${color}` }}

// Usage:
<div className="flex items-center gap-2">
  <StatusDot color="#10b981" />
  <span className="text-xs" style={{ color: "#10b981" }}>Active</span>
</div>
```

**Button Variants (from Demo App):**
```typescript
type ButtonVariant = "primary" | "outline-primary" | "outline-secondary" | "outline-info" | "outline-warning";

const buttonStyles = {
  primary: {
    backgroundColor: "#3b82f6",
    color: "white",
    borderRadius: "6-8px",
    padding: "6px 14px",
    fontSize: "14px",
    fontWeight: "500",
    transition: "all 0.2s ease",
  },
  "outline-primary": {
    border: "1px solid #3b82f6",
    color: "#3b82f6",
    backgroundColor: "transparent",
    hover: { backgroundColor: "#3b82f6", color: "white" },
  },
  "outline-secondary": {
    border: "1px solid #6b7280",
    color: "#6b7280",
  },
  "outline-info": {
    border: "1px solid #17a2b8",
    color: "#17a2b8",
  },
  "outline-warning": {
    border: "1px solid #f59e0b",
    color: "#f59e0b",
  },
};

// Tailwind equivalents:
"rounded-lg px-3.5 py-1.5 text-sm font-medium transition-all"
// + variant-specific classes
```

**FilterRow Component (from Demo App):**
```typescript
interface FilterRowProps {
  children: React.ReactNode;
}

const filterRowStyles = {
  marginBottom: "25px",
  backgroundColor: "#f1f5f9",  // Slate 100
  padding: "20px",
  borderRadius: "8px",
  alignItems: "flex-end",
};

// Tailwind equivalent:
"mb-6 bg-slate-100 p-5 rounded-lg flex items-end gap-4"

// Usage:
<FilterRow>
  <div className="flex-1">
    <label className="block mb-2 text-sm font-semibold text-slate-800">Date Range</label>
    <DatePicker />
  </div>
  <div className="flex-1">
    <label className="block mb-2 text-sm font-semibold text-slate-800">Module</label>
    <Select />
  </div>
</FilterRow>
```

**Input Field Styling (from Demo App):**
```css
.filter-dropdown,
.input-field {
  width: 100%;
  border-radius: 6-8px;
  border: 1px solid #e2e8f0;
  padding: 8px 12px;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

.filter-dropdown:focus,
.input-field:focus {
  outline: none;
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}
```

**Color Palette (from Demo App):**
```typescript
const colors = {
  // Status colors
  statusGreen: "#10b981",
  statusGreenBg: "#ecfdf5",
  statusYellow: "#f59e0b",
  statusYellowBg: "#fffbeb",
  statusRed: "#ef4444",
  statusRedBg: "#fef2f2",
  statusGrey: "#94a3b8",
  statusGreyBg: "#f1f5f9",
  
  // Background
  bgPrimary: "#f8fafc",
  bgSecondary: "#f1f5f9",
  bgCard: "#ffffff",
  
  // Text
  textPrimary: "#0f172a",
  textSecondary: "#64748b",
  textMuted: "#94a3b8",
};
```

**Files to Create:**
- `frontend/src/components/atoms/SummaryCard.tsx`
- `frontend/src/components/atoms/StatusBadge.tsx`
- `frontend/src/components/atoms/StatusDot.tsx`
- `frontend/src/components/atoms/Button.tsx`
- `frontend/src/components/atoms/Input.tsx`
- `frontend/src/components/atoms/FilterRow.tsx`
- `frontend/src/components/atoms/LoadingSkeleton.tsx`
- `frontend/src/lib/colors.ts` - Color palette constants
- `frontend/src/components/atoms/index.ts`

---

## Task 3.3: Build Molecule Components

**Objective:** Create composed molecule components matching exact demo app specifications.

**Scope:**
- Build DataTable component with dark header and status-based row coloring
- Build KPI Cards component (icon + metric + label layout)
- Build Filter sections with exact demo app layout
- Build Modal/Dialog components matching demo app modals
- Build Chart components (Recharts) with demo app color scheme
- Add search and filter functionality

**Prerequisites:**
- Atom components built (Task 3.2)

**Deliverables:**
1. `src/components/molecules/DataTable.tsx` - Reusable table with demo app styling
2. `src/components/molecules/KPICards.tsx` - Metric cards grid
3. `src/components/molecules/FilterSection.tsx` - Filter controls
4. `src/components/molecules/Modal.tsx` - Modal/Dialog component
5. `src/components/molecules/ChartWrapper.tsx` - Chart component wrapper
6. `src/components/molecules/SearchBar.tsx` - Search input

**Acceptance Criteria:**
- [ ] DataTable: dark header (#1e293b), white text, bold font
- [ ] DataTable: status-based row coloring (light green/red/yellow backgrounds)
- [ ] DataTable: 10 rows per page pagination
- [ ] DataTable: supports sorting, filtering, row selection
- [ ] KPICards: icon + metric + label layout from demo app
- [ ] Filter sections: grey background (#f1f5f9), 20px padding, 8px border-radius
- [ ] Modal: max-height 70vh, scrollable, XL size option
- [ ] Charts: Recharts with primary color #10b981
- [ ] SearchBar debounces input (300ms)
- [ ] All components responsive (768px breakpoint)

**DataTable Component (from Demo App):**
```typescript
interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  pagination?: boolean;  // Default: true, 10 rows per page
  sorting?: boolean;
  filtering?: boolean;
  onRowClick?: (row: T) => void;
}

// Exact styling from demo app:
const tableStyles = {
  header: {
    backgroundColor: "#1e293b",  // Slate 800
    color: "white",
    fontWeight: "bold",
    textAlign: "center",
    padding: "10px",
  },
  cell: {
    textAlign: "center",
    fontFamily: "inherit",
    fontSize: "0.9rem",
    padding: "10px",
  },
  // Status-based row coloring
  rowConditional: [
    { status: "✅", backgroundColor: "#e6f7ec" },  // Light green
    { status: "❌", backgroundColor: "#fdecea" },  // Light red
    { status: "⚠️", backgroundColor: "#fffbea" }, // Light yellow
  ],
  pagination: {
    pageSize: 10,
  },
};

// Tailwind equivalent:
// Header: "bg-slate-800 text-white font-bold text-center p-2.5"
// Row (passed): "bg-emerald-50"
// Row (failed): "bg-red-50"
// Row (warning): "bg-yellow-50"

// Usage:
<DataTable
  data={executions}
  columns={[
    { accessorKey: "module", header: "Module" },
    { accessorKey: "passed", header: "Passed" },
    { accessorKey: "failed", header: "Failed" },
    { accessorKey: "status", header: "Status" },
  ]}
  pagination={true}
  sorting={true}
/>
```

**KPICards Component (from Demo App):**
```typescript
interface KPICardData {
  icon: string;  // Font Awesome class, e.g., "fas fa-chart-pie"
  value: string | number;
  label: string;
  color: string;  // Icon color
}

interface KPICardsProps {
  cards: KPICardData[];
  columns?: 2 | 3 | 4 | 6;  // Grid columns (default: 4)
}

// Layout from demo app:
// 4 mini-cards in a row (for project cards)
// Each card: icon on left, value + label on right

const kpiCardLayout = {
  display: "flex",
  alignItems: "center",
  gap: "8px",
  padding: "10px",
  backgroundColor: "#f8fafc",
  borderRadius: "8px",
  border: "1px solid #e2e8f0",
};

// Tailwind equivalent:
"flex items-center gap-2 p-2.5 bg-slate-50 rounded-lg border border-slate-200"

// Usage (from Projects page):
<KPICards
  columns={4}
  cards={[
    { icon: "fas fa-chart-pie", value: "88%", label: "Pass Rate", color: passRateColor },
    { icon: "fas fa-cubes", value: 12, label: "Modules", color: "#6366f1" },
    { icon: "fas fa-vials", value: 1234, label: "Total Tests", color: "#6366f1" },
    { icon: "fas fa-bug", value: 5, label: "Defects", color: "#ef4444" },
  ]}
/>
```

**FilterSection Component (from Demo App):**
```typescript
interface FilterSectionProps {
  children: React.ReactNode;
  columns?: 2 | 3 | 4;  // Number of filter columns
}

// Exact styling from demo app:
const filterSectionStyles = {
  marginBottom: "25px",
  backgroundColor: "#f1f5f9",  // Slate 100
  padding: "20px",
  borderRadius: "8px",
  alignItems: "flex-end",
};

// Filter label styling:
const filterLabelStyles = {
  marginBottom: "8px",
  fontWeight: "600",
  color: "#1e293b",
  fontSize: "0.9rem",
};

// Tailwind equivalent:
"mb-6 bg-slate-100 p-5 rounded-lg grid grid-cols-3 gap-4 items-end"

// Usage (from Execution Summary page):
<FilterSection columns={3}>
  <div>
    <label className="block mb-2 text-sm font-semibold text-slate-800">Date</label>
    <Select options={dateOptions} />
  </div>
  <div>
    <label className="block mb-2 text-sm font-semibold text-slate-800">Module</label>
    <Select options={moduleOptions} />
  </div>
  <div>
    <label className="block mb-2 text-sm font-semibold text-slate-800">Status</label>
    <Select options={statusOptions} />
  </div>
</FilterSection>
```

**Modal Component (from Demo App):**
```typescript
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl";  // xl = max-width: 1200px
  scrollable?: boolean;  // Default: true
}

// Exact styling from demo app:
const modalStyles = {
  body: {
    maxHeight: "70vh",
    overflowY: "auto",
  },
  header: {
    borderBottom: "1px solid #e2e8f0",
    padding: "1rem 1.5rem",
  },
  footer: {
    borderTop: "1px solid #e2e8f0",
    padding: "1rem 1.5rem",
    display: "flex",
    justifyContent: "flex-end",
    gap: "0.5rem",
  },
};

// Usage (from Module Details - Defect Linking):
<Modal isOpen={isOpen} onClose={onClose} title="Link Defect" size="md">
  <div className="p-4">
    <Input placeholder="Enter Defect ID..." />
    <div className="text-red-500 text-sm mt-2">{errorMsg}</div>
  </div>
  <div className="flex justify-end gap-2 p-4 border-t">
    <Button variant="outline-secondary" onClick={onClose}>Cancel</Button>
    <Button variant="primary" onClick={onSubmit}>OK</Button>
  </div>
</Modal>
```

**ChartWrapper Component (from Demo App):**
```typescript
interface ChartWrapperProps {
  title: string;
  children: React.ReactNode;  // Recharts component
  height?: number;  // Default: 400px
}

// Chart configuration from demo app:
const chartConfig = {
  primaryColor: "#10b981",  // Emerald 500
  gridColor: "#e2e8f0",
  textColor: "#64748b",
  lineShape: "spline",  // Smooth curves
  markers: true,
};

// Recharts example (from Trends page):
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

<ChartWrapper title="Pass Rate Over Time">
  <LineChart data={data} width={600} height={400}>
    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
    <XAxis dataKey="day" stroke="#64748b" />
    <YAxis domain={[0, 100]} stroke="#64748b" />
    <Tooltip />
    <Legend />
    <Line
      type="monotone"
      dataKey="pass_rate"
      stroke="#10b981"
      strokeWidth={2}
      dot={{ fill: "#10b981" }}
    />
  </LineChart>
</ChartWrapper>
```

**Table Container Styling (from Demo App):**
```css
.table-container {
  margin-bottom: 30px;
  background-color: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
}

/* Tailwind equivalent: */
"mb-8 bg-white p-5 rounded-xl shadow-lg"
```

**Responsive Breakpoints (from Demo App):**
```css
@media (max-width: 768px) {
  .filter-section {
    grid-template-columns: 1fr;  /* Stack filters vertically */
  }
  
  .kpi-cards {
    grid-template-columns: repeat(2, 1fr);  /* 2 columns instead of 4 */
  }
  
  .data-table {
    font-size: 0.8rem;  /* Smaller text on mobile */
  }
}
```

**Files to Create:**
- `frontend/src/components/molecules/DataTable.tsx`
- `frontend/src/components/molecules/KPICards.tsx`
- `frontend/src/components/molecules/FilterSection.tsx`
- `frontend/src/components/molecules/Modal.tsx`
- `frontend/src/components/molecules/ChartWrapper.tsx`
- `frontend/src/components/molecules/SearchBar.tsx`
- `frontend/src/lib/chart-config.ts` - Chart color scheme constants
- `frontend/src/components/molecules/index.ts`

---

## Task 3.4: Migrate Projects Dashboard Page

**Objective:** Build Projects Dashboard page matching exact demo app layout and functionality.

**Scope:**
- Create projects page with exact demo app layout
- Implement useProjects hook with TanStack Query (15-second auto-refresh)
- Display header + 2 summary cards + 2-column project grid
- Add search and filter functionality
- Implement loading and error states
- Add create project button
- Implement status badges with pulsing dots
- Add empty state with centered icon + message

**Prerequisites:**
- Layout and components built (Tasks 3.1-3.3)
- Projects API available (Task 2.3)

**Deliverables:**
1. `src/app/projects/page.tsx` - Projects dashboard page with exact demo app layout
2. `src/hooks/useProjects.ts` - TanStack Query hook with 15s auto-refresh
3. `src/components/organisms/ProjectCard.tsx` - Project card component
4. `src/lib/api.ts` - API client functions
5. Loading skeleton for projects grid
6. Error boundary for error handling
7. Empty state component

**Acceptance Criteria:**
- [ ] Page layout: Header + 2 summary cards (Total Projects, Active Projects) at top
- [ ] 2-column project grid layout (responsive: 1 column on mobile)
- [ ] Each project card: 4 KPI cards (Total Modules, Pass Rate, Avg Duration, Last Run)
- [ ] Action buttons: Summary, Modules, Trends, Settings (outline variants)
- [ ] Auto-refresh every 15 seconds using TanStack Query interval
- [ ] Status badges with exact demo app colors and pulsing dots
- [ ] Empty state: centered icon + "No projects found" message
- [ ] Loading skeleton shown while fetching
- [ ] Error state shown on API failure
- [ ] Click project card navigates to project detail
- [ ] Real-time data updates on project creation

**Exact Page Layout (from Demo App):**
```typescript
// Page structure:
// 1. Header Section
//    - Title: "Projects"
//    - Subtitle: "Manage your test automation projects"
//    - Last Updated timestamp
//
// 2. Summary Cards Row (2 columns)
//    - Card 1: Active Projects (green check icon)
//    - Card 2: Total Test Cases (blue vials icon)
//
// 3. Section Heading
//    - "All projects" heading
//
// 4. Project Cards Grid (2 columns)
//    - Each project card contains:
//      a. Header: Cube icon + Project name + Status badge
//      b. KPI Row: 4 mini-cards (Pass Rate, Modules, Total Tests, Defects)
//      c. Metadata Row: Owner (left) | Last Run (right)
//      d. Action Buttons Row: 4 buttons (Summary, Modules, Trends, Settings)

const pageLayout = {
  header: {
    title: "Projects",
    subtitle: "Manage your test automation projects",
    lastUpdated: "Last updated: {timestamp}",
  },
  summaryCards: [
    { icon: "fas fa-check-circle", value: 3, label: "Active Projects", color: "#10b981" },
    { icon: "fas fa-vials", value: 1234, label: "Total Test Cases", color: "#3b82f6" },
  ],
  projectGrid: {
    columns: 2,  // 2 columns on desktop, 1 on mobile
    gap: "20px",
  },
};
```

**Project Card Component (from Demo App):**
```typescript
interface ProjectCardProps {
  project: {
    id: string;
    name: string;
    status: "green" | "yellow" | "red" | "grey";
    passRate: number;
    modulesCount: number;
    totalTests: number;
    defectsCount: number;
    owner: string;
    lastRun: string;  // ISO date string
  };
}

// Card structure:
const projectCardLayout = {
  // Header section
  header: {
    icon: "fas fa-cube",
    projectName: "font-size: 1.1rem, font-weight: 600",
    statusBadge: "pulsing dot + label",
  },
  
  // KPI cards row (4 mini-cards)
  kpiCards: [
    {
      icon: "fas fa-chart-pie",
      value: "{passRate}%",
      label: "Pass Rate",
      color: "dynamic based on pass rate",  // >80% green, 50-80% yellow, <50% red
    },
    {
      icon: "fas fa-cubes",
      value: "{modulesCount}",
      label: "Modules",
      color: "#6366f1",
    },
    {
      icon: "fas fa-vials",
      value: "{totalTests}",
      label: "Total Tests",
      color: "#6366f1",
    },
    {
      icon: "fas fa-bug",
      value: "{defectsCount}",
      label: "Defects",
      color: "#ef4444",
    },
  ],
  
  // Metadata row
  metadata: {
    owner: "Owner: {owner}",  // Left-aligned
    lastRun: "Last Run: {formatted date}",  // Right-aligned
  },
  
  // Action buttons row (4 buttons)
  actionButtons: [
    { label: "Summary", variant: "outline-primary", icon: "fas fa-chart-line" },
    { label: "Modules", variant: "outline-secondary", icon: "fas fa-cubes" },
    { label: "Trends", variant: "outline-info", icon: "fas fa-chart-bar" },
    { label: "Settings", variant: "outline-warning", icon: "fas fa-gear" },
  ],
};

// Card styling:
const projectCardStyles = {
  backgroundColor: "white",
  borderRadius: "12px",
  padding: "20px",
  boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
  transition: "transform 0.2s, box-shadow 0.2s",
  hover: {
    transform: "scale(1.01) translateY(-5px)",
    boxShadow: "0 10px 20px rgba(0, 0, 0, 0.12)",
  },
};

// Tailwind equivalent:
"bg-white rounded-xl p-5 shadow-md transition-all hover:scale-[1.01] hover:-translate-y-1 hover:shadow-xl"
```

**Status Badge Colors (from Demo App):**
```typescript
// Status determination logic:
function getProjectStatus(project) {
  if (!project.lastRun) return "grey";  // Never run
  
  const passRate = project.passRate;
  if (passRate >= 80) return "green";   // Healthy
  if (passRate >= 50) return "yellow";  // Warning
  return "red";                          // Critical
}

// Status badge rendering:
<StatusBadge status={projectStatus} label={statusLabel} />
// Where statusLabel = "Active" | "Warning" | "Critical" | "Unknown"
```

**Pass Rate Color Logic (from Demo App):**
```typescript
function getPassRateColor(passRate: number): string {
  if (passRate >= 80) return "#10b981";  // Green
  if (passRate >= 50) return "#f59e0b";  // Yellow/Amber
  return "#ef4444";                       // Red
}
```

**Auto-Refresh with TanStack Query (from Demo App):**
```typescript
// 15-second auto-refresh interval
function useProjects(filters?: ProjectFilters) {
  return useQuery({
    queryKey: ['projects', filters],
    queryFn: () => api.getProjects(filters),
    staleTime: 5 * 60 * 1000,     // 5 minutes
    refetchInterval: 15 * 1000,    // Auto-refresh every 15 seconds
    refetchOnWindowFocus: true,
  });
}
```

**Empty State (from Demo App):**
```typescript
const emptyState = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  padding: "60px 20px",
  textAlign: "center",
};

// Rendering:
<div className="flex flex-col items-center justify-center p-15 text-center">
  <i className="fas fa-folder-open text-6xl text-slate-300 mb-4"></i>
  <h3 className="text-xl font-semibold text-slate-700 mb-2">No projects found</h3>
  <p className="text-slate-500">Create your first project to get started</p>
  <Button variant="primary" className="mt-4" onClick={onCreateProject}>
    <i className="fas fa-plus mr-2"></i>
    Create Project
  </Button>
</div>
```

**Date Formatting (from Demo App):**
```typescript
// Last Run date formatting:
function formatLastRun(isoDate: string): string {
  const date = new Date(isoDate);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
  // Output: "Jan 15, 2024, 10:30 AM"
}
```

**Responsive Grid (from Demo App):**
```css
/* Desktop: 2 columns */
.projects-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

/* Mobile: 1 column */
@media (max-width: 768px) {
  .projects-grid {
    grid-template-columns: 1fr;
  }
}

/* Tailwind equivalent: */
"grid grid-cols-1 md:grid-cols-2 gap-5"
```

**Page Features:**
- Server-side rendering for initial load
- Client-side filtering and search
- Auto-refresh every 15 seconds
- Optimistic updates on create/edit
- Toast notifications for actions
- Hover effects on project cards
- Smooth transitions and animations

**Files to Create:**
- `frontend/src/app/projects/page.tsx`
- `frontend/src/components/organisms/ProjectCard.tsx`
- `frontend/src/components/organisms/EmptyState.tsx`
- `frontend/src/hooks/useProjects.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/types.ts`
- `frontend/src/lib/formatters.ts` - Date/number formatting utilities

---

## Task 3.5: Migrate Execution Summary Page

**Objective:** Build Execution Summary page matching exact demo app layout and functionality.

**Scope:**
- Create execution summary page with exact demo app layout
- Implement useExecutions hook with latest execution per module logic
- Build execution table with status icons and row coloring
- Add 3 summary cards at top (Total Executions, Passed, Failed)
- Add filter row with Date/Module/Status dropdowns
- Implement "View Module" action buttons
- Add status-based row coloring (light green/red/yellow)
- Implement 10 rows per page pagination
- Add export to CSV functionality

**Prerequisites:**
- Layout and components built (Tasks 3.1-3.3)
- Executions API available (Task 2.5)

**Deliverables:**
1. `src/app/projects/[id]/executions/page.tsx` - Execution summary page with exact demo app layout
2. `src/hooks/useExecutions.ts` - TanStack Query hook with latest execution logic
3. `src/components/organisms/ExecutionTable.tsx` - Execution table with status icons
4. Filter state management with URL params
5. Export functionality
6. Last updated timestamp footer

**Acceptance Criteria:**
- [ ] Page layout: 3 summary cards at top (Total Executions, Passed, Failed)
- [ ] Filter row: 3 dropdowns (Date, Module, Status) with grey background (#f1f5f9)
- [ ] Execution table shows latest execution per module for selected date
- [ ] Table columns: Module | Passed | Failed | Total | Duration | Status | Actions
- [ ] Status icons in table: ✅ (green), ⚠️ (yellow), ❌ (red), ⬜ (grey)
- [ ] Row coloring based on status: light green (#e6f7ec), light red (#fdecea), light yellow (#fffbea)
- [ ] "View Module" button in Actions column
- [ ] Pagination: 10 rows per page
- [ ] Last updated timestamp at bottom
- [ ] Filters work: date, module, status
- [ ] Sorting works on all columns
- [ ] Export to CSV downloads filtered data
- [ ] URL reflects current filters (shareable links)
- [ ] Loading states for table rows

**Exact Page Layout (from Demo App):**
```typescript
// Page structure:
// 1. Back Button
//    - "← Back to Projects" button (top-left)
//
// 2. Header
//    - Title: "Execution Summary: {Project Name}"
//
// 3. Summary Cards Row (3 columns)
//    - Card 1: Total Executions (85% or count)
//    - Card 2: Passed Tests (1234)
//    - Card 3: Avg Duration (45m)
//
// 4. Filter Row (3 dropdowns)
//    - Date dropdown
//    - Module dropdown
//    - Status dropdown
//
// 5. Execution Table
//    - Shows latest execution per module
//    - Status icons and row coloring
//    - "View Module" action buttons
//
// 6. Footer
//    - Last updated timestamp

const pageLayout = {
  backButton: {
    label: "← Back to Projects",
    href: "/projects",
    variant: "outline-secondary",
  },
  header: {
    title: "Execution Summary: {projectName}",
  },
  summaryCards: [
    { icon: "fas fa-chart-pie", value: "85%", label: "Pass Rate", color: "#10b981" },
    { icon: "fas fa-vials", value: 1234, label: "Total Tests", color: "#3b82f6" },
    { icon: "fas fa-clock", value: "45m", label: "Avg Duration", color: "#6366f1" },
  ],
  filterRow: {
    columns: 3,
    filters: [
      { label: "Date", type: "dropdown", options: ["Today", "Last 7 days", "Last 30 days"] },
      { label: "Module", type: "dropdown", options: ["All", "Auth", "Payment", "..."] },
      { label: "Status", type: "dropdown", options: ["All", "Passed", "Failed", "Warning"] },
    ],
  },
};
```

**Execution Table (from Demo App):**
```typescript
interface ExecutionTableRow {
  module: string;
  passed: number;
  failed: number;
  total: number;
  duration: string;  // e.g., "3.2m"
  status: "✅" | "⚠️" | "❌" | "⬜";
  executionId: string;
}

// Table columns (from demo app):
const columns = [
  { accessorKey: "module", header: "Module" },
  { accessorKey: "passed", header: "Passed" },
  { accessorKey: "failed", header: "Failed" },
  { accessorKey: "total", header: "Total" },
  { accessorKey: "duration", header: "Duration" },
  { accessorKey: "status", header: "Status" },
  { accessorKey: "actions", header: "Actions" },
];

// Status icon rendering:
function renderStatusIcon(status: string) {
  const icons = {
    "✅": { icon: "✅", color: "#10b981" },  // Green check
    "⚠️": { icon: "⚠️", color: "#f59e0b" },  // Yellow warning
    "❌": { icon: "❌", color: "#ef4444" },  // Red cross
    "⬜": { icon: "⬜", color: "#94a3b8" },  // Grey square
  };
  return <span style={{ fontSize: "1.2rem" }}>{icons[status].icon}</span>;
}

// Row coloring (conditional styling):
const rowStyles = [
  { condition: (row) => row.status === "✅", backgroundColor: "#e6f7ec" },  // Light green
  { condition: (row) => row.status === "❌", backgroundColor: "#fdecea" },  // Light red
  { condition: (row) => row.status === "⚠️", backgroundColor: "#fffbea" }, // Light yellow
];
```

**Latest Execution Logic (from Demo App):**
```typescript
// Data flow:
// 1. Fetch all executions for project from API
// 2. Filter by selected date
// 3. Group by module
// 4. Take latest execution per module (most recent created_at)
// 5. Apply module/status filters
// 6. Render table

function getLatestExecutionPerModule(executions: Execution[], selectedDate: string) {
  // Filter by date
  const filtered = executions.filter(e => 
    e.created_at.startsWith(selectedDate)
  );
  
  // Group by module
  const grouped = filtered.reduce((acc, exec) => {
    if (!acc[exec.module_id] || exec.created_at > acc[exec.module_id].created_at) {
      acc[exec.module_id] = exec;
    }
    return acc;
  }, {});
  
  return Object.values(grouped);
}
```

**"View Module" Action Button (from Demo App):**
```typescript
// Actions column rendering:
function renderActionsColumn(row: ExecutionTableRow) {
  return (
    <Button
      variant="outline-primary"
      size="sm"
      onClick={() => navigateToModule(row.executionId)}
    >
      View Module
    </Button>
  );
}

// Button is rendered as HTML in markdown cell (in Dash):
// In Next.js, use actual Button component
```

**Table Styling (from Demo App):**
```typescript
const tableStyles = {
  header: {
    backgroundColor: "#1e293b",
    color: "white",
    fontWeight: "bold",
    textAlign: "center",
  },
  cell: {
    textAlign: "center",
    fontSize: "0.9rem",
    padding: "10px",
  },
  pagination: {
    pageSize: 10,
  },
};

// Tailwind equivalent:
// Header: "bg-slate-800 text-white font-bold text-center"
// Cell: "text-center text-sm p-2.5"
```

**Filter Row Styling (from Demo App):**
```typescript
const filterRowStyles = {
  marginBottom: "25px",
  backgroundColor: "#f1f5f9",
  padding: "20px",
  borderRadius: "8px",
  display: "grid",
  gridTemplateColumns: "repeat(3, 1fr)",
  gap: "16px",
  alignItems: "flex-end",
};

// Tailwind equivalent:
"mb-6 bg-slate-100 p-5 rounded-lg grid grid-cols-3 gap-4 items-end"
```

**Last Updated Footer (from Demo App):**
```typescript
const footerStyles = {
  marginTop: "30px",
  textAlign: "center",
  color: "#64748b",
  fontSize: "0.875rem",
};

// Rendering:
<div className="mt-8 text-center text-slate-500 text-sm">
  Last updated: {new Date().toLocaleString()}
</div>
```

**Status Determination Logic (from Demo App):**
```typescript
function getExecutionStatus(execution: Execution): string {
  const passRate = (execution.passed / execution.total) * 100;
  
  if (passRate === 100) return "✅";      // All passed
  if (passRate >= 80) return "⚠️";    // Warning (some failures)
  if (execution.failed > 0) return "❌";  // Failed
  return "⬜";                            // Unknown/Not run
}
```

**Filter State (URL Params):**
```typescript
// URL: /projects/123/executions?date=2024-01-15&module=auth&status=failed
const [searchParams, setSearchParams] = useSearchParams();

const filters = {
  date: searchParams.get('date') || 'today',
  module: searchParams.get('module') || 'all',
  status: searchParams.get('status') || 'all',
};

// Update URL on filter change:
function updateFilters(newFilters: Filters) {
  setSearchParams(newFilters);
}
```

**Responsive Layout (from Demo App):**
```css
@media (max-width: 768px) {
  .summary-cards {
    grid-template-columns: 1fr;  /* Stack vertically */
  }
  
  .filter-row {
    grid-template-columns: 1fr;  /* Stack vertically */
  }
  
  .execution-table {
    font-size: 0.8rem;  /* Smaller text */
  }
}
```

**Files to Create:**
- `frontend/src/app/projects/[id]/executions/page.tsx`
- `frontend/src/hooks/useExecutions.ts`
- `frontend/src/components/organisms/ExecutionTable.tsx`
- `frontend/src/lib/execution-utils.ts` - Latest execution logic
- `frontend/src/lib/export.ts`
- `frontend/src/components/atoms/BackButton.tsx`

---

## Task 3.6: Migrate Trends Page with Recharts

**Objective:** Build Trends analysis page with Recharts replacing Plotly.

**Scope:**
- Create trends page with pass rate and duration charts
- Implement useTrends hook
- Build line charts with Recharts
- Add project/module toggle
- Implement responsive charts
- Add chart interactions (tooltips, zoom)

**Prerequisites:**
- Layout and components built (Tasks 3.1-3.3)
- Backend trends data endpoint available

**Deliverables:**
1. `src/app/projects/[id]/trends/page.tsx` - Trends page
2. `src/hooks/useTrends.ts` - TanStack Query hook
3. `src/components/organisms/TrendCharts.tsx` - Chart components
4. Responsive chart layouts
5. Chart configuration and theming

**Acceptance Criteria:**
- [ ] Pass rate trend chart displays correctly
- [ ] Duration trend chart displays correctly
- [ ] Toggle between project-level and module-level trends
- [ ] Charts responsive to window resize
- [ ] Tooltips show detailed data on hover
- [ ] Date range filter updates charts
- [ ] Loading skeleton for charts
- [ ] Charts render in < 200ms

**Charts to Build:**
```typescript
// 1. Pass Rate Trend (Line Chart)
// X-axis: Date, Y-axis: Pass Rate %
// Multiple lines for different modules

// 2. Duration Trend (Line Chart)
// X-axis: Date, Y-axis: Duration (seconds)
// Multiple lines for different modules

// 3. Test Count Trend (Area Chart)
// X-axis: Date, Y-axis: Test Count
// Stacked areas for passed/failed/skipped
```

**Recharts Configuration:**
```typescript
<ResponsiveContainer width="100%" height={400}>
  <LineChart data={trendData}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="date" />
    <YAxis />
    <Tooltip />
    <Legend />
    <Line type="monotone" dataKey="pass_rate" stroke="#10b981" />
  </LineChart>
</ResponsiveContainer>
```

**Files to Create:**
- `frontend/src/app/projects/[id]/trends/page.tsx`
- `frontend/src/hooks/useTrends.ts`
- `frontend/src/components/organisms/TrendCharts.tsx`
- `frontend/src/lib/chart-config.ts`

---

## Task 3.7: Migrate Module Details Page

**Objective:** Build Module Details page with execution runs and scenario drill-down.

**Scope:**
- Create module details page
- Display module execution history
- Build collapsible scenario list
- Add defect linking functionality
- Implement scenario filtering
- Add execution comparison

**Prerequisites:**
- Layout and components built (Tasks 3.1-3.3)
- Executions and Scenarios APIs available

**Deliverables:**
1. `src/app/projects/[id]/modules/[moduleId]/page.tsx` - Module details page
2. `src/hooks/useModuleExecutions.ts` - TanStack Query hook
3. `src/components/organisms/ScenarioList.tsx` - Scenario accordion
4. Defect linking modal
5. Execution comparison view

**Acceptance Criteria:**
- [ ] Module info displayed (name, description, stats)
- [ ] Execution history table shows all runs
- [ ] Click execution expands scenario list
- [ ] Scenarios grouped by status (failed, passed, skipped)
- [ ] Failed scenarios show error details
- [ ] Link defect to scenario works
- [ ] Filter scenarios by status, tags
- [ ] Compare two executions side-by-side

**Page Sections:**
```typescript
// 1. Module Header
// - Module name, description
// - Summary metrics (total runs, avg pass rate, last run)

// 2. Execution History Table
// - Date, total tests, passed, failed, duration, status
// - Click row to expand scenarios

// 3. Scenario List (Collapsible)
// - Grouped by status
// - Show scenario name, status, duration, tags
// - Failed scenarios: show error message, stack trace
// - Link to defect button

// 4. Execution Comparison (Optional)
// - Select two executions
// - Show diff of scenarios
```

**Files to Create:**
- `frontend/src/app/projects/[id]/modules/[moduleId]/page.tsx`
- `frontend/src/hooks/useModuleExecutions.ts`
- `frontend/src/components/organisms/ScenarioList.tsx`
- `frontend/src/components/organisms/DefectLinkModal.tsx`

---

## Task 3.8: Build Defect Management Page (Full CRUD)

**Objective:** Build complete Defect Management page replacing POC mock data.

**Scope:**
- Create defect management page
- Implement useDefects hook
- Build defect table with filtering
- Create defect form (create/edit)
- Add defect status workflow
- Implement defect assignment

**Prerequisites:**
- Layout and components built (Tasks 3.1-3.3)
- Defects API available (Task 2.5)

**Deliverables:**
1. `src/app/defects/page.tsx` - Defect management page
2. `src/hooks/useDefects.ts` - TanStack Query hook
3. `src/components/organisms/DefectTable.tsx` - Defect table
4. `src/components/organisms/DefectForm.tsx` - Create/edit form
5. Defect detail modal
6. Status transition workflow

**Acceptance Criteria:**
- [ ] Defect table displays all defects
- [ ] Filter by status, severity, priority, assignee
- [ ] Search by title/description
- [ ] Create new defect opens form modal
- [ ] Edit defect pre-fills form
- [ ] Delete defect shows confirmation
- [ ] Status transitions validated (Open → In Progress → Fixed → Closed)
- [ ] Assign defect to user
- [ ] Link defect to scenario

**Defect Table Columns:**
```typescript
const columns: ColumnDef<Defect>[] = [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "title", header: "Title" },
  { accessorKey: "severity", header: "Severity" },
  { accessorKey: "priority", header: "Priority" },
  { accessorKey: "status", header: "Status" },
  { accessorKey: "assigned_to", header: "Assignee" },
  { accessorKey: "created_at", header: "Created" },
  { accessorKey: "actions", header: "Actions" },
];
```

**Defect Form Fields:**
```typescript
interface DefectFormData {
  title: string;
  description: string;
  severity: "Critical" | "High" | "Medium" | "Low";
  priority: "P0" | "P1" | "P2" | "P3";
  assigned_to?: string;
  module_id?: string;
  scenario_id?: string;
}
```

**Files to Create:**
- `frontend/src/app/defects/page.tsx`
- `frontend/src/hooks/useDefects.ts`
- `frontend/src/components/organisms/DefectTable.tsx`
- `frontend/src/components/organisms/DefectForm.tsx`
- `frontend/src/components/organisms/DefectDetailModal.tsx`

---

## Task 3.9: Build Settings Page with Form Validation

**Objective:** Build Settings page for project management with form validation.

**Scope:**
- Create settings page
- Build project form with React Hook Form
- Implement Zod validation schema
- Add form error handling
- Implement optimistic updates
- Add toast notifications

**Prerequisites:**
- Layout and components built (Tasks 3.1-3.3)
- Projects API available (Task 2.2)

**Deliverables:**
1. `src/app/settings/page.tsx` - Settings page
2. `src/components/organisms/ProjectForm.tsx` - Project form
3. `src/lib/validations.ts` - Zod schemas
4. Form error handling
5. Toast notification integration

**Acceptance Criteria:**
- [ ] Settings page displays project form
- [ ] Form validates all fields with Zod
- [ ] Validation errors shown inline
- [ ] Submit creates/updates project
- [ ] Optimistic update shows immediate feedback
- [ ] Success toast on save
- [ ] Error toast on failure
- [ ] Form resets after successful submit

**Project Form Fields:**
```typescript
interface ProjectFormData {
  name: string;          // Required, min 3 chars
  description: string;   // Optional
  repo_url: string;      // Optional, valid URL
  owner: string;         // Required, email format
  is_active: boolean;    // Default true
}
```

**Zod Validation Schema:**
```typescript
const projectSchema = z.object({
  name: z.string().min(3, "Name must be at least 3 characters"),
  description: z.string().optional(),
  repo_url: z.string().url("Invalid URL").optional().or(z.literal("")),
  owner: z.string().email("Invalid email address"),
  is_active: z.boolean().default(true),
});
```

**React Hook Form Setup:**
```typescript
const form = useForm<ProjectFormData>({
  resolver: zodResolver(projectSchema),
  defaultValues: project || {
    name: "",
    description: "",
    repo_url: "",
    owner: "",
    is_active: true,
  },
});
```

**Files to Create:**
- `frontend/src/app/settings/page.tsx`
- `frontend/src/components/organisms/ProjectForm.tsx`
- `frontend/src/lib/validations.ts`
- `frontend/src/hooks/useToast.ts`

---

## Task 3.10: Implement TanStack Query Hooks for All API Calls

**Objective:** Create comprehensive TanStack Query hooks for all API endpoints.

**Scope:**
- Create hooks for all GET endpoints (queries)
- Create hooks for all POST/PUT/DELETE endpoints (mutations)
- Implement cache invalidation strategies
- Add optimistic updates
- Configure stale times and cache times
- Add error handling

**Prerequisites:**
- All backend APIs available (Phase 2 completed)
- TanStack Query provider configured (Task 3.1)

**Deliverables:**
1. `src/hooks/useProjects.ts` - Project queries and mutations
2. `src/hooks/useExecutions.ts` - Execution queries
3. `src/hooks/useModules.ts` - Module queries
4. `src/hooks/useDefects.ts` - Defect queries and mutations
5. `src/hooks/useTrends.ts` - Trend data queries
6. `src/hooks/useReports.ts` - Report upload mutation
7. `src/lib/api.ts` - API client functions
8. Query key factory

**Acceptance Criteria:**
- [ ] All GET endpoints have useQuery hooks
- [ ] All POST/PUT/DELETE endpoints have useMutation hooks
- [ ] Cache invalidation works on mutations
- [ ] Optimistic updates implemented for critical mutations
- [ ] Error handling with retry logic
- [ ] Loading and error states exposed
- [ ] TypeScript types for all responses

**Query Hooks Pattern:**
```typescript
// GET /api/v1/projects
export function useProjects(filters?: ProjectFilters) {
  return useQuery({
    queryKey: ['projects', filters],
    queryFn: () => api.getProjects(filters),
    staleTime: 5 * 60 * 1000,
  });
}

// POST /api/v1/projects
export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateProjectData) => api.createProject(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      toast.success('Project created successfully');
    },
    onError: (error) => {
      toast.error('Failed to create project');
    },
  });
}
```

**Cache Invalidation Strategy:**
```typescript
// On project create/update: invalidate ['projects']
// On execution create: invalidate ['executions', 'projects', 'trends']
// On defect create: invalidate ['defects', 'scenarios']
// On report upload: invalidate ['executions', 'scenarios', 'trends']
```

**Files to Create:**
- `frontend/src/hooks/useProjects.ts`
- `frontend/src/hooks/useExecutions.ts`
- `frontend/src/hooks/useModules.ts`
- `frontend/src/hooks/useDefects.ts`
- `frontend/src/hooks/useTrends.ts`
- `frontend/src/hooks/useReports.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/query-keys.ts`

---

## Task 3.11: Implement Zustand Stores for UI State

**Objective:** Create Zustand stores for client-side UI state management.

**Scope:**
- Create filter state store
- Create UI state store (sidebar, modals)
- Create user preferences store
- Implement persistence for preferences
- Add TypeScript types

**Prerequisites:**
- Frontend project initialized (Task 1.1)

**Deliverables:**
1. `src/store/useFilterStore.ts` - Filter state (project, module, date)
2. `src/store/useUIStore.ts` - UI state (sidebar, modals, theme)
3. `src/store/useUserPreferencesStore.ts` - User preferences
4. Persistence middleware for preferences
5. Store TypeScript types

**Acceptance Criteria:**
- [ ] Filter store manages all filter state
- [ ] UI store manages sidebar collapse state
- [ ] UI store manages modal open/close state
- [ ] User preferences persisted to localStorage
- [ ] Theme preference persisted
- [ ] All stores fully typed
- [ ] No unnecessary re-renders

**Filter Store:**
```typescript
interface FilterState {
  projectId: string | null;
  moduleId: string | null;
  dateRange: [Date, Date] | null;
  status: string[];
  setProjectId: (id: string | null) => void;
  setModuleId: (id: string | null) => void;
  setDateRange: (range: [Date, Date] | null) => void;
  setStatus: (status: string[]) => void;
  resetFilters: () => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  projectId: null,
  moduleId: null,
  dateRange: null,
  status: [],
  setProjectId: (id) => set({ projectId: id }),
  setModuleId: (id) => set({ moduleId: id }),
  setDateRange: (range) => set({ dateRange: range }),
  setStatus: (status) => set({ status }),
  resetFilters: () => set({
    projectId: null,
    moduleId: null,
    dateRange: null,
    status: [],
  }),
}));
```

**UI Store:**
```typescript
interface UIState {
  sidebarCollapsed: boolean;
  activeModal: string | null;
  theme: "light" | "dark";
  toggleSidebar: () => void;
  openModal: (modal: string) => void;
  closeModal: () => void;
  setTheme: (theme: "light" | "dark") => void;
}
```

**Files to Create:**
- `frontend/src/store/useFilterStore.ts`
- `frontend/src/store/useUIStore.ts`
- `frontend/src/store/useUserPreferencesStore.ts`
- `frontend/src/store/middleware/persistence.ts`

---

## Task 3.12: Add Loading Skeletons and Error Boundaries

**Objective:** Implement comprehensive loading states and error handling.

**Scope:**
- Create loading skeleton components
- Implement error boundary components
- Add suspense boundaries
- Create error fallback UI
- Add retry mechanisms

**Prerequisites:**
- All pages implemented (Tasks 3.4-3.9)

**Deliverables:**
1. `src/components/atoms/LoadingSkeleton.tsx` - Skeleton components
2. `src/components/ErrorBoundary.tsx` - Error boundary
3. `src/components/ErrorFallback.tsx` - Error UI
4. Suspense boundaries for async components
5. Retry logic for failed requests

**Acceptance Criteria:**
- [ ] Loading skeletons match component shapes
- [ ] Error boundary catches React errors
- [ ] Error fallback shows user-friendly message
- [ ] Retry button on error fallback
- [ ] Suspense boundaries prevent layout shift
- [ ] No flash of loading state for cached data
- [ ] Skeleton shows during initial load only

**Loading Skeleton Components:**
```typescript
// ProjectCardSkeleton
// ExecutionTableSkeleton
// ChartSkeleton
// DefectTableSkeleton
// FormSkeleton
```

**Error Boundary:**
```typescript
class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    // Log error to monitoring service
    logError(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback onReset={this.reset} />;
    }
    return this.props.children;
  }
}
```

**Error Fallback UI:**
```typescript
interface ErrorFallbackProps {
  error?: Error;
  onReset?: () => void;
}

// Shows:
// - Error icon
// - Error message (user-friendly)
// - Retry button
// - Report issue link
```

**Files to Create:**
- `frontend/src/components/atoms/LoadingSkeleton.tsx`
- `frontend/src/components/ErrorBoundary.tsx`
- `frontend/src/components/ErrorFallback.tsx`
- `frontend/src/lib/error-logger.ts`

---

# PHASE 4: ADVANCED FEATURES

## Task 4.1: Migrate AI Failure Analysis with Streaming Responses

**Objective:** Build AI Failure Analysis page with streaming AI responses.

**Scope:**
- Create AI analysis page
- Implement streaming response handling
- Build AI insight modal with tabs
- Add failure pattern detection
- Implement fix suggestion generation
- Add loading states for AI processing

**Prerequisites:**
- Layout and components built (Phase 3)
- AI analysis backend endpoint available

**Deliverables:**
1. `src/app/ai-analysis/page.tsx` - AI analysis page
2. `src/hooks/useAIAnalysis.ts` - AI analysis hook
3. `src/components/organisms/AIInsightModal.tsx` - Insight modal
4. Streaming response handler
5. AI response markdown renderer

**Acceptance Criteria:**
- [ ] AI analysis page displays failed scenarios
- [ ] Click "Analyze" triggers AI analysis
- [ ] AI response streams in real-time
- [ ] Modal shows analysis in tabs (Summary, Patterns, Suggestions)
- [ ] Markdown rendering for AI responses
- [ ] Loading spinner during AI processing
- [ ] Error handling for AI failures
- [ ] Copy to clipboard for suggestions

**AI Analysis Flow:**
```typescript
// 1. User selects failed scenarios
// 2. Click "Generate AI Analysis"
// 3. Send request to /api/v1/analytics/ai-analysis
// 4. Stream response using Server-Sent Events (SSE)
// 5. Render streaming response in modal
// 6. Show tabs: Summary, Failure Patterns, Fix Suggestions
```

**Streaming Response Handler:**
```typescript
async function streamAIAnalysis(scenarioIds: string[]) {
  const response = await fetch('/api/v1/analytics/ai-analysis', {
    method: 'POST',
    body: JSON.stringify({ scenario_ids: scenarioIds }),
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    onChunk(chunk); // Update UI with chunk
  }
}
```

**Modal Tabs:**
```typescript
// Tab 1: Summary
// - Overall analysis
// - Affected modules
// - Severity assessment

// Tab 2: Failure Patterns
// - Common error patterns
// - Frequency analysis
// - Root cause hypothesis

// Tab 3: Fix Suggestions
// - Suggested fixes
// - Code snippets
// - Priority ranking
```

**Files to Create:**
- `frontend/src/app/ai-analysis/page.tsx`
- `frontend/src/hooks/useAIAnalysis.ts`
- `frontend/src/components/organisms/AIInsightModal.tsx`
- `frontend/src/lib/stream-handler.ts`
- `frontend/src/components/atoms/MarkdownRenderer.tsx`

---

## Task 4.2: Implement WebSocket for Real-Time Execution Updates

**Objective:** Add WebSocket connection for real-time execution status updates with JWT authentication.

**Scope:**
- Create WebSocket connection manager
- Implement WebSocket endpoint in backend at /api/v1/ws/executions
- Add JWT token authentication to WebSocket connection flow
- Add RBAC authorization for WebSocket connections
- Add real-time updates to execution pages
- Show live execution progress
- Add connection status indicator
- Implement reconnection logic

**Prerequisites:**
- API versioning structure set up (Task 2.1)
- Authentication implemented (Task 2.2)
- Execution pages built (Task 3.5)

**Deliverables:**
1. `src/lib/websocket.ts` - WebSocket manager with JWT token handling
2. `src/hooks/useWebSocket.ts` - WebSocket hook
3. Backend: `app/websocket/router.py` - WebSocket endpoint at /api/v1/ws/executions
4. Backend: `app/websocket/auth.py` - JWT authentication for WebSocket
5. Real-time update integration in execution pages
6. Connection status indicator

**Acceptance Criteria:**
- [ ] WebSocket endpoint accessible at /api/v1/ws/executions (not /ws/executions)
- [ ] WebSocket connection requires valid JWT token
- [ ] JWT token validated on connection establishment
- [ ] RBAC authorization enforced (user role checked)
- [ ] Unauthorized connections rejected with 401/403
- [ ] WebSocket connects on page load after authentication
- [ ] Real-time updates shown for new executions
- [ ] Execution status updates in real-time
- [ ] Connection indicator shows online/offline status
- [ ] Auto-reconnect on connection loss (with token refresh if needed)
- [ ] Graceful degradation if WebSocket unavailable
- [ ] No duplicate updates

**WebSocket Events:**
```typescript
// Client → Server
type ClientEvents = {
  subscribe: { project_id: string };
  unsubscribe: { project_id: string };
};

// Server → Client
type ServerEvents = {
  execution_started: Execution;
  execution_updated: Execution;
  execution_completed: Execution;
  scenario_updated: Scenario;
};
```

**WebSocket Hook with JWT Authentication:**
```typescript
function useWebSocket(projectId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const queryClient = useQueryClient();
  const { getAccessToken } = useAuth(); // Get JWT token

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      console.error('No access token available for WebSocket connection');
      return;
    }

    // Connect to WebSocket at /api/v1/ws/executions with JWT token
    const ws = new WebSocket(`${WS_URL}/api/v1/ws/executions?token=${token}`);

    ws.onopen = () => {
      setIsConnected(true);
      ws.send(JSON.stringify({ type: 'subscribe', project_id: projectId }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Invalidate queries to refetch data
      queryClient.invalidateQueries({ queryKey: ['executions'] });
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = (event) => {
      setIsConnected(false);
      if (event.code === 401 || event.code === 403) {
        console.error('WebSocket authentication failed');
        // Optionally trigger token refresh
      } else {
        // Reconnect after 5 seconds
        setTimeout(() => connectWebSocket(), 5000);
      }
    };

    return () => ws.close();
  }, [projectId]);

  return { isConnected };
}
```

**Backend WebSocket Authentication:**
```python
# app/websocket/router.py
from fastapi import WebSocket, WebSocketDisconnect, Depends, status
from app.auth.dependencies import get_current_user_ws

@router.websocket("/api/v1/ws/executions")
async def websocket_executions(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user_ws),  # JWT auth dependency
):
    """WebSocket endpoint for real-time execution updates with JWT authentication."""
    await websocket.accept()
    
    try:
        # User is authenticated via JWT token
        # Check RBAC authorization
        if current_user.role not in ["admin", "manager", "viewer"]:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Subscribe to updates
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "subscribe":
                project_id = message["project_id"]
                # Add to subscription manager
                await manager.subscribe(websocket, project_id, current_user.id)
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket)

# app/auth/dependencies.py
async def get_current_user_ws(websocket: WebSocket, token: str = Query(...)):
    """Validate JWT token for WebSocket connections."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        
        user = await get_user_by_id(user_id)
        if user is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        
        return user
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
```

**Files to Create:**
- `frontend/src/lib/websocket.ts` (with JWT token handling)
- `frontend/src/hooks/useWebSocket.ts` (with authentication)
- `backend/app/websocket/router.py` (at /api/v1/ws/executions with JWT auth)
- `backend/app/websocket/manager.py`
- `backend/app/websocket/auth.py` (JWT authentication for WebSocket)
- `backend/app/auth/dependencies.py` (update with get_current_user_ws)
- `frontend/src/components/atoms/ConnectionIndicator.tsx`
- `backend/tests/test_websocket_auth.py` (test JWT authentication)

---

## Task 4.3: Add Export Functionality (CSV, PDF Reports)

**Objective:** Implement data export functionality for tables and reports.

**Scope:**
- Add CSV export for all tables
- Implement PDF report generation
- Create export configuration options
- Add export progress indicator
- Implement server-side export for large datasets

**Prerequisites:**
- All data tables implemented (Phase 3)

**Deliverables:**
1. `src/lib/export.ts` - Export utilities
2. Export button components
3. Backend: `app/exports/router.py` - Export endpoints
4. PDF template for reports
5. Export configuration modal

**Acceptance Criteria:**
- [ ] CSV export works for all tables
- [ ] Exported CSV includes filtered data only
- [ ] PDF report generation works
- [ ] PDF includes charts and tables
- [ ] Export progress shown for large datasets
- [ ] Server-side export for >1000 rows
- [ ] Downloaded file has meaningful name

**Export Types:**
```typescript
// 1. CSV Export (Client-Side)
// - Projects list
// - Executions table
// - Scenarios table
// - Defects table

// 2. PDF Report (Server-Side)
// - Project summary report
// - Execution detail report
// - Trend analysis report
// - Defect summary report
```

**CSV Export Function:**
```typescript
function exportToCSV<T>(data: T[], filename: string, columns: Column<T>[]) {
  const headers = columns.map(col => col.header).join(',');
  const rows = data.map(row => 
    columns.map(col => row[col.accessorKey]).join(',')
  );
  const csv = [headers, ...rows].join('\n');
  
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}_${new Date().toISOString()}.csv`;
  link.click();
}
```

**PDF Report Endpoint:**
```python
# POST /api/v1/exports/pdf/project-summary
# Request: { project_id: string, date_range: [Date, Date] }
# Response: PDF file download
```

**Files to Create:**
- `frontend/src/lib/export.ts`
- `frontend/src/components/atoms/ExportButton.tsx`
- `frontend/src/components/organisms/ExportConfigModal.tsx`
- `backend/app/exports/router.py`
- `backend/app/exports/pdf_generator.py`
- `backend/app/exports/templates/project_summary.html`

---

## Task 4.4: Implement Dark Mode Toggle

**Objective:** Add dark mode support with theme toggle.

**Scope:**
- Implement theme provider with dark mode
- Create theme toggle component
- Define dark mode color tokens
- Update all components for dark mode
- Persist theme preference

**Prerequisites:**
- All components built (Phase 3)
- Theme provider configured (Task 3.1)

**Deliverables:**
1. `src/lib/theme-provider.tsx` - Theme provider with dark mode
2. `src/components/atoms/ThemeToggle.tsx` - Toggle button
3. Dark mode color tokens in Tailwind config
4. Updated component styles for dark mode
5. Theme persistence to localStorage

**Acceptance Criteria:**
- [ ] Theme toggle switches between light/dark mode
- [ ] All components render correctly in dark mode
- [ ] Theme preference persisted to localStorage
- [ ] System preference detected on first load
- [ ] Smooth transition between themes
- [ ] Charts update colors for dark mode
- [ ] No flash of wrong theme on page load

**Theme Tokens:**
```typescript
// tailwind.config.ts
theme: {
  extend: {
    colors: {
      background: "hsl(var(--background))",
      foreground: "hsl(var(--foreground))",
      primary: "hsl(var(--primary))",
      secondary: "hsl(var(--secondary))",
      // ... more tokens
    },
  },
}

// globals.css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  // ...
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --primary: 217.2 91.2% 59.8%;
  // ...
}
```

**Theme Provider:**
```typescript
function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    // Load from localStorage or detect system preference
    const stored = localStorage.getItem("theme");
    const systemPreference = window.matchMedia("(prefers-color-scheme: dark)").matches;
    setTheme(stored || (systemPreference ? "dark" : "light"));
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("theme", theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

**Files to Create:**
- `frontend/src/lib/theme-provider.tsx`
- `frontend/src/components/atoms/ThemeToggle.tsx`
- `frontend/tailwind.config.ts` (update)
- `frontend/src/styles/globals.css` (update)

---

## Task 4.5: Add Keyboard Shortcuts and Accessibility Audit

**Objective:** Implement keyboard shortcuts and ensure WCAG 2.1 AA compliance.

**Scope:**
- Implement keyboard shortcuts for common actions
- Add keyboard shortcut help modal
- Conduct accessibility audit
- Fix accessibility issues
- Add ARIA labels and roles
- Ensure keyboard navigation works

**Prerequisites:**
- All pages and components built (Phase 3)

**Deliverables:**
1. `src/hooks/useKeyboardShortcuts.ts` - Keyboard shortcut hook
2. `src/components/organisms/ShortcutHelpModal.tsx` - Help modal
3. Accessibility audit report
4. Fixed accessibility issues
5. ARIA labels added to all interactive elements

**Acceptance Criteria:**
- [ ] Keyboard shortcuts work for common actions
- [ ] `?` key opens shortcut help modal
- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible
- [ ] Screen reader tested (NVDA/JAWS)
- [ ] Lighthouse accessibility score > 95
- [ ] WCAG 2.1 AA compliant
- [ ] Color contrast ratios meet standards

**Keyboard Shortcuts:**
```typescript
const shortcuts = {
  "?": "Show keyboard shortcuts",
  "g p": "Go to Projects",
  "g e": "Go to Executions",
  "g d": "Go to Defects",
  "g a": "Go to AI Analysis",
  "n": "Create new project",
  "/": "Focus search",
  "Escape": "Close modal",
  "Ctrl+K": "Command palette",
};
```

**useKeyboardShortcuts Hook:**
```typescript
function useKeyboardShortcuts() {
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Check for shortcuts
      if (e.key === "?" && !isInputFocused()) {
        openShortcutHelp();
      }
      if (e.key === "/" && !isInputFocused()) {
        e.preventDefault();
        focusSearch();
      }
      // ... more shortcuts
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, []);
}
```

**Accessibility Checklist:**
- [ ] All images have alt text
- [ ] All buttons have accessible names
- [ ] Form inputs have labels
- [ ] Color contrast ratios ≥ 4.5:1
- [ ] Focus indicators visible
- [ ] Keyboard navigation works
- [ ] ARIA roles and labels added
- [ ] Heading hierarchy correct
- [ ] Skip to main content link
- [ ] Screen reader tested

**Files to Create:**
- `frontend/src/hooks/useKeyboardShortcuts.ts`
- `frontend/src/components/organisms/ShortcutHelpModal.tsx`
- `docs/accessibility-audit.md`
- `docs/keyboard-shortcuts.md`

---

## Task 4.6: Implement Notification System (Toast + In-App)

**Objective:** Build comprehensive notification system for user feedback.

**Scope:**
- Implement toast notifications
- Create in-app notification center
- Add notification persistence
- Implement notification preferences
- Add sound/badge support

**Prerequisites:**
- Layout and components built (Phase 3)

**Deliverables:**
1. `src/components/organisms/ToastNotification.tsx` - Toast component
2. `src/components/organisms/NotificationCenter.tsx` - Notification center
3. `src/hooks/useNotifications.ts` - Notification hook
4. `src/store/useNotificationStore.ts` - Notification state
5. Notification preferences UI

**Acceptance Criteria:**
- [ ] Toast notifications show for user actions
- [ ] Toast auto-dismisses after 5 seconds
- [ ] Toast supports variants (success, error, warning, info)
- [ ] Notification center shows all notifications
- [ ] Notifications persist across sessions
- [ ] Mark as read functionality
- [ ] Clear all notifications
- [ ] Notification preferences (enable/disable types)

**Toast Notification:**
```typescript
interface ToastProps {
  variant: "success" | "error" | "warning" | "info";
  title: string;
  description?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// Usage:
toast.success("Project created successfully");
toast.error("Failed to upload report", {
  description: "Please try again later",
  action: { label: "Retry", onClick: retryUpload },
});
```

**Notification Center:**
```typescript
interface Notification {
  id: string;
  type: "execution_completed" | "defect_assigned" | "report_uploaded";
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  link?: string;
}

// Features:
// - Badge count on bell icon
// - Dropdown panel with notifications
// - Mark as read/unread
// - Clear all
// - Filter by type
```

**Notification Types:**
```typescript
// 1. Execution Completed
// 2. Report Upload Success/Failure
// 3. Defect Assigned to You
// 4. AI Analysis Complete
// 5. Project Created/Updated
```

**Files to Create:**
- `frontend/src/components/organisms/ToastNotification.tsx`
- `frontend/src/components/organisms/NotificationCenter.tsx`
- `frontend/src/hooks/useNotifications.ts`
- `frontend/src/hooks/useToast.ts`
- `frontend/src/store/useNotificationStore.ts`
- `frontend/src/components/atoms/NotificationBadge.tsx`

---

# PHASE 5: PERFORMANCE OPTIMIZATION

## Task 5.1: Implement Multi-Layer Caching Strategy (HTTP Headers, Materialized Views, Cross-Endpoint Optimization)

**Objective:** Implement comprehensive multi-layer caching strategy covering HTTP cache headers (Layer 1), materialized views for DB query cache (Layer 4), and cross-endpoint TTL tuning.

**Scope:**
- Implement HTTP cache headers (ETag/If-None-Match handling) for browser cache - Layer 1
- Create materialized views for DB query cache optimization - Layer 4
- Configure cross-endpoint TTL tuning and optimization
- Add cache warming strategies
- Add cache monitoring dashboard
- NOTE: Redis cache service (Layer 3) already created in Task 2.4

**Prerequisites:**
- Redis running (Task 1.3)
- All backend APIs implemented (Phase 2)
- Redis cache service created (Task 2.4)

**Deliverables:**
1. HTTP cache headers middleware (ETag/If-None-Match) - Layer 1
2. PostgreSQL materialized views for aggregations - Layer 4
3. Cross-endpoint cache TTL configuration and tuning
4. Cache warming strategies
5. Cache monitoring dashboard
6. Cache performance benchmarks

**Acceptance Criteria:**
- [ ] HTTP cache headers (ETag/If-None-Match) implemented for API responses - Layer 1
- [ ] Materialized views created for expensive aggregations - Layer 4
- [ ] Cross-endpoint cache TTLs optimized and documented
- [ ] Cache hit rate > 70% across all layers
- [ ] ETag-based responses return 304 Not Modified when appropriate
- [ ] Materialized views refresh strategy configured
- [ ] Cache monitoring shows hit/miss metrics for all layers
- [ ] No stale data served

**Multi-Layer Cache Strategy (4 Layers):**
```python
# Layer 1: Browser Cache (HTTP Cache Headers)
# ETag generation and If-None-Match handling
# Cache-Control headers for static and dynamic content

# Layer 2: TanStack Query (Client-Side) - Frontend responsibility
# staleTime: 5 minutes (projects list)
# staleTime: 1 minute (execution data)

# Layer 3: Redis (Server-Side) - Already implemented in Task 2.4
# Cache Keys:
projects:all:page:{page}              # TTL: 5 min
project:{id}                          # TTL: 10 min
project:{id}:modules                  # TTL: 10 min
executions:project:{id}:page:{page}   # TTL: 2 min
executions:module:{id}:page:{page}    # TTL: 2 min
execution:{id}                        # TTL: 5 min
scenarios:execution:{id}:page:{page}  # TTL: 5 min
trends:project:{id}                   # TTL: 5 min
defects:all:page:{page}               # TTL: 3 min

# Layer 4: Database Query Cache (PostgreSQL)
# Materialized views for:
# - Project aggregations (module count, test stats)
# - Execution summaries
# - Trend data calculations

# Invalidation Triggers
- Project create/update: invalidate projects:*, project:{id}*, refresh materialized views
- Report upload: invalidate executions:*, scenarios:*, trends:*, refresh materialized views
- Defect create/update: invalidate defects:*
```

**HTTP Cache Headers (ETag) Implementation:**
```python
from fastapi import Response, Request
import hashlib

@router.get("/projects")
async def list_projects(
    request: Request,
    response: Response,
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    data = await project_service.list_projects(db, page, size)
    
    # Generate ETag from response data
    etag = hashlib.md5(json.dumps(data).encode()).hexdigest()
    
    # Check If-None-Match header
    if request.headers.get("If-None-Match") == etag:
        response.status_code = 304  # Not Modified
        return None
    
    # Set ETag and Cache-Control headers
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "max-age=300"  # 5 minutes
    
    return data
```

**Materialized Views (PostgreSQL):**
```sql
-- Materialized view for project aggregations
CREATE MATERIALIZED VIEW project_stats AS
SELECT 
    p.id,
    p.name,
    COUNT(DISTINCT m.id) as modules_count,
    SUM(e.total) as total_tests,
    SUM(e.passed) as passed_tests,
    MAX(e.created_at) as last_run
FROM projects p
LEFT JOIN modules m ON m.project_id = p.id
LEFT JOIN executions e ON e.module_id = m.id
GROUP BY p.id, p.name;

-- Create index on materialized view
CREATE INDEX idx_project_stats_id ON project_stats(id);

-- Refresh strategy (can be manual, scheduled, or on-demand)
REFRESH MATERIALIZED VIEW CONCURRENTLY project_stats;
```

**Cross-Endpoint TTL Configuration:**
```python
# app/core/cache_config.py
CACHE_TTL_CONFIG = {
    "projects:all": 300,        # 5 min - frequently accessed
    "project:detail": 600,      # 10 min - less frequently changed
    "executions:list": 120,     # 2 min - updated on report upload
    "trends:data": 300,         # 5 min - expensive computation
    "defects:list": 180,        # 3 min - moderate update frequency
}
```

**Files to Create:**
- `backend/app/core/http_cache.py` - ETag/If-None-Match middleware
- `backend/app/core/cache_config.py` - Cross-endpoint TTL configuration
- `backend/app/migrations/versions/00X_create_materialized_views.py` - Materialized views
- `backend/app/core/materialized_views.py` - Materialized view refresh logic
- `backend/tests/test_http_cache.py`
- `backend/tests/test_materialized_views.py`
- `docs/multi-layer-caching-strategy.md`

---

## Task 5.2: Add Database Connection Pooling (pgBouncer)

**Objective:** Configure pgBouncer for efficient database connection pooling.

**Scope:**
- Install and configure pgBouncer
- Configure pool size and modes
- Update database connection strings
- Add connection health checks
- Monitor connection pool metrics

**Prerequisites:**
- PostgreSQL running (Task 1.3)

**Deliverables:**
1. pgBouncer configuration file
2. Updated docker-compose with pgBouncer
3. Connection pool monitoring
4. Health check endpoints
5. Performance benchmarks

**Acceptance Criteria:**
- [ ] pgBouncer running and accepting connections
- [ ] Backend connects through pgBouncer
- [ ] Connection pool size optimized (20 connections)
- [ ] Pool mode set to transaction pooling
- [ ] Health checks pass
- [ ] Connection metrics monitored
- [ ] No connection exhaustion under load

**pgBouncer Configuration:**
```ini
# pgbouncer.ini
[databases]
taps = host=postgres port=5432 dbname=taps user=taps_user password=secret

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
reserve_pool_size = 5
reserve_pool_timeout = 3
server_lifetime = 3600
server_idle_timeout = 600
```

**Docker Compose Update:**
```yaml
services:
  pgbouncer:
    image: pgbouncer/pgbouncer:latest
    environment:
      - DATABASES_HOST=postgres
      - DATABASES_PORT=5432
      - DATABASES_DBNAME=taps
      - PGBOUNCER_POOL_MODE=transaction
      - PGBOUNCER_MAX_CLIENT_CONN=100
      - PGBOUNCER_DEFAULT_POOL_SIZE=20
    ports:
      - "6432:6432"
    depends_on:
      - postgres

  backend:
    environment:
      - DATABASE_URL=postgresql+asyncpg://taps_user:password@pgbouncer:6432/taps
```

**Files to Create:**
- `pgbouncer/pgbouncer.ini`
- `pgbouncer/userlist.txt`
- `docker-compose.yml` (update)
- `docs/connection-pooling.md`

---

## Task 5.3: Optimize Next.js Bundle (Code Splitting, Tree Shaking)

**Objective:** Optimize frontend bundle size and loading performance.

**Scope:**
- Analyze bundle with @next/bundle-analyzer
- Implement dynamic imports for heavy components
- Configure tree shaking
- Optimize dependencies
- Add bundle size budgets
- Implement route-based code splitting

**Prerequisites:**
- All frontend pages built (Phase 3)

**Deliverables:**
1. Bundle analysis report
2. Dynamic imports for charts and heavy components
3. Optimized dependencies
4. Bundle size budgets configuration
5. Performance improvement metrics

**Acceptance Criteria:**
- [ ] Initial bundle size < 200KB (gzipped)
- [ ] First Contentful Paint < 1.0s
- [ ] Time to Interactive < 2.0s
- [ ] Lighthouse Performance score > 90
- [ ] No duplicate dependencies
- [ ] Heavy components lazy-loaded
- [ ] Bundle size budgets enforced in CI

**Bundle Optimization Techniques:**
```typescript
// 1. Dynamic imports for heavy components
const TrendCharts = dynamic(() => import('@/components/organisms/TrendCharts'), {
  loading: () => <ChartSkeleton />,
  ssr: false,
});

// 2. Dynamic imports for modals
const AIInsightModal = dynamic(() => import('@/components/organisms/AIInsightModal'));

// 3. Route-based code splitting (automatic with Next.js App Router)

// 4. Optimize imports (import only what's needed)
// Bad: import _ from 'lodash';
// Good: import debounce from 'lodash/debounce';

// 5. Remove unused dependencies
// Run: npx depcheck
```

**Bundle Size Budgets:**
```javascript
// next.config.js
module.exports = {
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.performance = {
        maxAssetSize: 200000, // 200KB
        maxEntrypointSize: 200000,
        hints: 'error',
      };
    }
    return config;
  },
};
```

**Bundle Analysis:**
```bash
# Install analyzer
npm install @next/bundle-analyzer

# Analyze bundle
ANALYZE=true npm run build

# Review:
# - Largest packages
# - Duplicate dependencies
# - Unused code
```

**Files to Create/Modify:**
- `frontend/next.config.js` (update)
- `frontend/package.json` (remove unused deps)
- `docs/bundle-analysis-report.md`
- `.github/workflows/bundle-size.yml`

---

## Task 5.4: Implement Virtual Scrolling for Large Datasets

**Objective:** Add virtual scrolling to tables with large datasets.

**Scope:**
- Install TanStack Virtual
- Implement virtual scrolling for execution table
- Implement virtual scrolling for scenario list
- Add virtual scrolling for defect table
- Optimize rendering performance

**Prerequisites:**
- DataTable component built (Task 3.3)
- All table pages implemented (Phase 3)

**Deliverables:**
1. Virtual scrolling implementation for DataTable
2. Updated execution table with virtual scrolling
3. Updated scenario list with virtual scrolling
4. Performance benchmarks
5. Smooth scrolling experience

**Acceptance Criteria:**
- [ ] Tables with >100 rows use virtual scrolling
- [ ] Smooth scrolling with no lag
- [ ] Constant memory usage regardless of row count
- [ ] Render time < 50ms for 10,000 rows
- [ ] Scroll position preserved on navigation
- [ ] Works with sorting and filtering

**Virtual Scrolling Implementation:**
```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualTable({ data, columns }: TableProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50, // Row height
    overscan: 10, // Render 10 extra rows
  });

  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      <div style={{ height: `${rowVirtualizer.getTotalSize()}px`, position: 'relative' }}>
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const row = data[virtualRow.index];
          return (
            <div
              key={virtualRow.index}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <TableRow data={row} columns={columns} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

**Performance Benchmarks:**
- Without virtual scrolling: 1000 rows = ~2s render, high memory
- With virtual scrolling: 10,000 rows = <50ms render, constant memory

**Files to Modify:**
- `frontend/src/components/molecules/DataTable.tsx`
- `frontend/src/components/organisms/ExecutionTable.tsx`
- `frontend/src/components/organisms/ScenarioList.tsx`
- `docs/performance-benchmarks.md`

---

## Task 5.5: Add API Response Compression (gzip/brotli)

**Objective:** Enable response compression for API endpoints.

**Scope:**
- Configure gzip compression middleware
- Enable brotli compression
- Set compression thresholds
- Test compression ratios
- Measure performance impact

**Prerequisites:**
- Backend APIs implemented (Phase 2)

**Deliverables:**
1. Compression middleware configured
2. Compression enabled for all responses
3. Compression ratio benchmarks
4. Performance improvement metrics

**Acceptance Criteria:**
- [ ] gzip compression enabled for responses > 1KB
- [ ] Brotli compression enabled (if supported)
- [ ] Compression ratio > 60% for JSON responses
- [ ] Response time impact < 5ms
- [ ] Content-Encoding header set correctly
- [ ] Compression works for all endpoints

**Compression Middleware:**
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB
```

**Compression Configuration:**
```python
# app/main.py
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add compression middleware
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Only compress responses larger than 1KB
    compresslevel=6,    # Compression level (1-9, 6 is balanced)
)
```

**Compression Benchmarks:**
```
Endpoint: GET /api/v1/projects (100 projects)
- Uncompressed: 45KB
- Gzipped: 12KB (73% reduction)
- Brotli: 10KB (78% reduction)

Endpoint: GET /api/v1/executions (500 executions)
- Uncompressed: 180KB
- Gzipped: 35KB (81% reduction)
- Brotli: 28KB (84% reduction)
```

**Files to Modify:**
- `backend/app/main.py`
- `backend/app/core/middleware.py`
- `docs/performance-benchmarks.md`

---

## Task 5.6: Configure CDN for Static Assets

**Objective:** Set up CDN for serving static assets (images, fonts, JS, CSS).

**Scope:**
- Configure Nginx for static asset serving
- Set up cache headers
- Configure asset versioning
- Add CDN integration (CloudFront/Cloudflare)
- Test asset delivery

**Prerequisites:**
- Frontend built and deployed

**Deliverables:**
1. Nginx configuration for static assets
2. Cache headers configured
3. Asset versioning strategy
4. CDN integration (optional)
5. Performance improvement metrics

**Acceptance Criteria:**
- [ ] Static assets served with long cache headers
- [ ] Asset versioning prevents cache issues
- [ ] Nginx serves static files directly
- [ ] CDN integration working (if applicable)
- [ ] Asset load time < 100ms
- [ ] Lighthouse score improved

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name taps.example.com;

    # Static assets (Next.js build output)
    location /_next/static/ {
        alias /app/frontend/.next/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Images
    location /images/ {
        alias /app/frontend/public/images/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # API proxy
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend (Next.js)
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Cache Headers Strategy:**
```
/_next/static/*  : Cache-Control: public, max-age=31536000, immutable
/images/*        : Cache-Control: public, max-age=2592000
/fonts/*         : Cache-Control: public, max-age=31536000, immutable
/api/*           : Cache-Control: no-cache (or short TTL with ETag)
```

**Files to Create:**
- `nginx/nginx.conf`
- `nginx/Dockerfile`
- `docker-compose.yml` (update)
- `docs/cdn-setup.md`

---

## Task 5.7: Performance Profiling and Bottleneck Resolution

**Objective:** Identify and resolve performance bottlenecks.

**Scope:**
- Profile frontend with React DevTools Profiler
- Profile backend with cProfile
- Identify slow queries with query logging
- Analyze API response times
- Optimize identified bottlenecks
- Run Lighthouse audits

**Prerequisites:**
- All features implemented (Phases 1-4)

**Deliverables:**
1. Frontend profiling report
2. Backend profiling report
3. Slow query analysis
4. Lighthouse audit report
5. Optimization implementations
6. Performance improvement metrics

**Acceptance Criteria:**
- [ ] All pages load in < 2 seconds
- [ ] API responses < 100ms (p95)
- [ ] No slow queries (>100ms)
- [ ] Lighthouse Performance score > 90
- [ ] Core Web Vitals meet thresholds:
  - LCP < 2.5s
  - FID < 100ms
  - CLS < 0.1
- [ ] All bottlenecks documented and resolved

**Profiling Tools:**
```bash
# Frontend profiling
# 1. React DevTools Profiler
# 2. Chrome DevTools Performance tab
# 3. Lighthouse CI

# Backend profiling
# 1. cProfile for Python
python -m cProfile -o profile.stats app/main.py

# 2. Query logging
# Enable in database.py:
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log all queries
)

# 3. API response time monitoring
# Add middleware to log response times
```

**Common Bottlenecks to Check:**
```
Frontend:
- Large bundle sizes
- Unnecessary re-renders
- Unoptimized images
- Blocking JavaScript
- No code splitting

Backend:
- N+1 queries
- Missing indexes
- Synchronous I/O
- Large response payloads
- No caching
```

**Lighthouse Audit:**
```bash
# Run Lighthouse
npx lighthouse https://taps.example.com --output html --output-path report.html

# Check:
# - Performance score
# - Accessibility score
# - Best Practices score
# - SEO score
```

**Files to Create:**
- `docs/frontend-profiling-report.md`
- `docs/backend-profiling-report.md`
- `docs/lighthouse-audit.md`
- `docs/performance-improvements.md`

---

## Task 5.8: Security Hardening (CSP, HSTS, Input Sanitization)

**Objective:** Implement comprehensive security measures.

**Scope:**
- Configure Content Security Policy (CSP)
- Enable HTTP Strict Transport Security (HSTS)
- Implement input sanitization
- Add SQL injection prevention
- Configure CORS properly
- Add rate limiting
- Enable security headers

**Prerequisites:**
- All features implemented (Phases 1-4)

**Deliverables:**
1. CSP configuration
2. Security headers middleware
3. Input validation and sanitization
4. SQL injection prevention
5. Security audit report
6. Penetration testing results

**Acceptance Criteria:**
- [ ] CSP configured and enforced
- [ ] HSTS enabled with long max-age
- [ ] All user inputs validated and sanitized
- [ ] SQL injection prevented (parameterized queries)
- [ ] XSS prevention implemented
- [ ] CSRF protection enabled
- [ ] Security headers present on all responses
- [ ] No critical vulnerabilities in security audit

**Security Headers:**
```python
# app/core/middleware.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.example.com;"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

**Input Validation:**
```python
# Use Pydantic for automatic validation
from pydantic import BaseModel, validator, EmailStr

class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    repo_url: str | None = None
    owner: EmailStr
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 3:
            raise ValueError('Name must be at least 3 characters')
        # Sanitize: remove HTML tags, SQL injection attempts
        return sanitize_input(v)
```

**SQL Injection Prevention:**
```python
# Always use parameterized queries (SQLAlchemy does this automatically)
# NEVER use string concatenation for queries

# Good:
stmt = select(Project).where(Project.name == name)

# Bad:
query = f"SELECT * FROM projects WHERE name = '{name}'"  # NEVER DO THIS
```

**Files to Create:**
- `backend/app/core/security.py`
- `backend/app/core/middleware.py` (update)
- `backend/app/core/sanitization.py`
- `docs/security-audit.md`
- `docs/security-guidelines.md`

---

# PHASE 6: TESTING & DEPLOYMENT

## Task 6.1: Write Jest + RTL Unit Tests for React Components

**Objective:** Achieve 80%+ test coverage for frontend components.

**Scope:**
- Write unit tests for all atom components
- Write unit tests for all molecule components
- Write unit tests for all organism components
- Test component rendering, interactions, and edge cases
- Configure Jest and React Testing Library
- Add coverage reporting

**Prerequisites:**
- All components built (Phase 3)

**Deliverables:**
1. `frontend/jest.config.js` - Jest configuration
2. `frontend/tests/components/atoms/*.test.tsx` - Atom tests
3. `frontend/tests/components/molecules/*.test.tsx` - Molecule tests
4. `frontend/tests/components/organisms/*.test.tsx` - Organism tests
5. Coverage report (>80%)
6. CI integration for tests

**Acceptance Criteria:**
- [ ] All components have unit tests
- [ ] Test coverage > 80%
- [ ] All tests pass in CI
- [ ] Tests cover happy paths and edge cases
- [ ] Accessibility tested with jest-axe
- [ ] User interactions tested
- [ ] Error states tested

**Test Structure:**
```
frontend/tests/
├── components/
│   ├── atoms/
│   │   ├── Badge.test.tsx
│   │   ├── StatusIcon.test.tsx
│   │   ├── KPICard.test.tsx
│   │   └── LoadingSkeleton.test.tsx
│   ├── molecules/
│   │   ├── FilterBar.test.tsx
│   │   ├── DataTable.test.tsx
│   │   ├── SummaryCards.test.tsx
│   │   └── ProjectCard.test.tsx
│   └── organisms/
│       ├── Sidebar.test.tsx
│       ├── ExecutionTable.test.tsx
│       ├── TrendCharts.test.tsx
│       └── AIInsightModal.test.tsx
├── hooks/
│   ├── useProjects.test.ts
│   ├── useExecutions.test.ts
│   └── useDebounce.test.ts
└── lib/
    ├── api.test.ts
    └── utils.test.ts
```

**Example Test:**
```typescript
// Badge.test.tsx
import { render, screen } from '@testing-library/react';
import { Badge } from '@/components/atoms/Badge';

describe('Badge', () => {
  it('renders with correct text', () => {
    render(<Badge variant="success">Passed</Badge>);
    expect(screen.getByText('Passed')).toBeInTheDocument();
  });

  it('applies correct variant class', () => {
    const { container } = render(<Badge variant="error">Failed</Badge>);
    expect(container.firstChild).toHaveClass('badge-error');
  });

  it('is accessible', async () => {
    const { container } = render(<Badge variant="success">Passed</Badge>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

**Files to Create:**
- `frontend/jest.config.js`
- `frontend/jest.setup.js`
- `frontend/tests/components/**/*.test.tsx` (20+ files)
- `frontend/tests/hooks/*.test.ts` (5+ files)
- `frontend/.coveragerc`

---

## Task 6.2: Write Playwright E2E Tests for Critical Flows

**Objective:** Create end-to-end tests for critical user flows.

**Scope:**
- Set up Playwright test environment
- Write E2E tests for critical flows
- Configure test data setup/teardown
- Add visual regression testing
- Integrate with CI pipeline

**Prerequisites:**
- All pages implemented (Phase 3)
- Backend APIs deployed

**Deliverables:**
1. `frontend/playwright.config.ts` - Playwright configuration
2. `frontend/e2e/*.spec.ts` - E2E test files
3. Test fixtures and helpers
4. Visual regression baselines
5. CI integration

**Acceptance Criteria:**
- [ ] All critical flows have E2E tests
- [ ] Tests run in CI on every PR
- [ ] Tests pass consistently (no flakiness)
- [ ] Visual regression tests detect UI changes
- [ ] Test data isolated per test
- [ ] Tests run in parallel
- [ ] Test report generated

**Critical E2E Test Scenarios:**
```typescript
// 1. Project Lifecycle
test('create project and upload report', async ({ page }) => {
  // Navigate to projects
  await page.goto('/projects');
  
  // Create new project
  await page.click('button:has-text("New Project")');
  await page.fill('input[name="name"]', 'Test Project');
  await page.fill('input[name="owner"]', 'test@example.com');
  await page.click('button:has-text("Create")');
  
  // Verify project created
  await expect(page.locator('text=Test Project')).toBeVisible();
  
  // Upload report
  await page.click('text=Test Project');
  await page.click('button:has-text("Upload Report")');
  await page.setInputFiles('input[type="file"]', 'fixtures/cucumber-report.json');
  await page.click('button:has-text("Upload")');
  
  // Verify execution created
  await expect(page.locator('text=Execution #1')).toBeVisible();
});

// 2. Drill-Down Flow
test('navigate from projects to scenario details', async ({ page }) => {
  // ... test implementation
});

// 3. Defect Workflow
test('create and link defect to scenario', async ({ page }) => {
  // ... test implementation
});

// 4. AI Analysis Flow
test('generate AI analysis for failures', async ({ page }) => {
  // ... test implementation
});

// 5. Filter and Search
test('filter executions by date and status', async ({ page }) => {
  // ... test implementation
});
```

**Playwright Configuration:**
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
});
```

**Files to Create:**
- `frontend/playwright.config.ts`
- `frontend/e2e/project-lifecycle.spec.ts`
- `frontend/e2e/drill-down-flow.spec.ts`
- `frontend/e2e/defect-workflow.spec.ts`
- `frontend/e2e/ai-analysis.spec.ts`
- `frontend/e2e/filter-search.spec.ts`
- `frontend/e2e/fixtures/`
- `frontend/e2e/helpers/`

---

## Task 6.3: Write Pytest Integration Tests for All API Endpoints

**Objective:** Achieve 85%+ test coverage for backend with integration tests.

**Scope:**
- Write integration tests for all API endpoints
- Test authentication and authorization
- Test error handling
- Test edge cases and validation
- Configure test database
- Add test data factories

**Prerequisites:**
- All backend APIs implemented (Phase 2)

**Deliverables:**
1. `backend/tests/integration/*.py` - Integration tests
2. Test database configuration
3. Test data factories
4. Coverage report (>85%)
5. CI integration

**Acceptance Criteria:**
- [ ] All API endpoints have integration tests
- [ ] Test coverage > 85%
- [ ] All tests pass in CI
- [ ] Authentication tested
- [ ] Authorization tested
- [ ] Error cases tested
- [ ] Validation tested

**Integration Test Structure:**
```
backend/tests/integration/
├── test_auth_api.py
├── test_projects_api.py
├── test_executions_api.py
├── test_reports_api.py
├── test_defects_api.py
└── test_analytics_api.py
```

**Example Integration Test:**
```python
# test_projects_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, auth_headers):
    """Test project creation endpoint."""
    response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Test Project",
            "description": "Test Description",
            "owner": "test@example.com",
        },
        headers=auth_headers,
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["owner"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_project_validation_error(client: AsyncClient, auth_headers):
    """Test project creation with invalid data."""
    response = await client.post(
        "/api/v1/projects",
        json={"name": "AB"},  # Too short
        headers=auth_headers,
    )
    
    assert response.status_code == 422
    assert "validation error" in response.json()["detail"][0]["msg"].lower()

@pytest.mark.asyncio
async def test_list_projects_pagination(client: AsyncClient, auth_headers, test_projects):
    """Test project listing with pagination."""
    response = await client.get(
        "/api/v1/projects?page=1&size=10",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 10
    assert "total" in data
    assert "page" in data
```

**Test Fixtures:**
```python
# conftest.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def auth_headers(client):
    # Create test user and login
    response = await client.post("/api/v1/auth/login", json={...})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def test_projects(db_session):
    # Create test projects
    projects = [ProjectFactory() for _ in range(20)]
    db_session.add_all(projects)
    await db_session.commit()
    return projects
```

**Files to Create:**
- `backend/tests/integration/test_auth_api.py`
- `backend/tests/integration/test_projects_api.py`
- `backend/tests/integration/test_executions_api.py`
- `backend/tests/integration/test_reports_api.py`
- `backend/tests/integration/test_defects_api.py`
- `backend/tests/conftest.py` (update)

---

## Task 6.4: Load Testing with k6 or Locust

**Objective:** Conduct load testing to validate performance under stress.

**Scope:**
- Set up k6 or Locust for load testing
- Create load test scenarios
- Test API endpoints under load
- Identify performance bottlenecks
- Validate performance targets
- Generate load test reports

**Prerequisites:**
- All backend APIs deployed
- Performance optimizations completed (Phase 5)

**Deliverables:**
1. Load test scripts (k6 or Locust)
2. Load test scenarios
3. Load test execution results
4. Performance bottleneck analysis
5. Recommendations for scaling

**Acceptance Criteria:**
- [ ] Load tests run successfully
- [ ] API handles 500 concurrent users
- [ ] p95 response time < 500ms under load
- [ ] No errors under normal load
- [ ] Error rate < 1% under peak load
- [ ] Database connections stable
- [ ] Memory usage stable

**Load Test Scenarios:**
```javascript
// k6 script: load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 500 },  // Ramp up to 500 users
    { duration: '5m', target: 500 },  // Stay at 500 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests < 500ms
    http_req_failed: ['rate<0.01'],    // Error rate < 1%
  },
};

export default function () {
  // Test 1: List projects
  let res = http.get('http://api.example.com/api/v1/projects');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);

  // Test 2: Get project details
  res = http.get('http://api.example.com/api/v1/projects/123');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);

  // Test 3: List executions
  res = http.get('http://api.example.com/api/v1/projects/123/executions');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
```

**Running Load Tests:**
```bash
# Install k6
brew install k6  # macOS

# Run load test
k6 run load-test.js

# Run with output to InfluxDB (for visualization)
k6 run --out influxdb=http://localhost:8086/k6 load-test.js
```

**Metrics to Monitor:**
```
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate
- Throughput (MB/s)
- Concurrent connections
- Database connection pool usage
- CPU usage
- Memory usage
- Cache hit rate
```

**Files to Create:**
- `load-tests/k6/load-test.js`
- `load-tests/k6/stress-test.js`
- `load-tests/k6/spike-test.js`
- `docs/load-test-results.md`
- `docs/scaling-recommendations.md`

---

## Task 6.5: Set Up Kubernetes Helm Charts

**Objective:** Create Kubernetes deployment configuration using Helm.

**Scope:**
- Create Helm chart for TAPS application
- Define deployments for frontend, backend, postgres, redis
- Configure services and ingress
- Set up ConfigMaps and Secrets
- Configure horizontal pod autoscaling
- Create environment-specific values files

**Prerequisites:**
- Docker images built for frontend and backend
- Kubernetes cluster available

**Deliverables:**
1. `k8s/helm/taps/` - Helm chart directory
2. Deployment manifests for all services
3. Service and Ingress configurations
4. ConfigMaps and Secrets
5. HorizontalPodAutoscaler configurations
6. Values files for staging and production

**Acceptance Criteria:**
- [ ] Helm chart installs successfully
- [ ] All pods running and healthy
- [ ] Services accessible via ingress
- [ ] ConfigMaps and Secrets properly configured
- [ ] HPA scales pods based on CPU/memory
- [ ] Rolling updates work without downtime
- [ ] Health checks configured

**Helm Chart Structure:**
```
k8s/helm/taps/
├── Chart.yaml
├── values.yaml
├── values-staging.yaml
├── values-production.yaml
└── templates/
    ├── frontend-deployment.yaml
    ├── frontend-service.yaml
    ├── backend-deployment.yaml
    ├── backend-service.yaml
    ├── postgres-statefulset.yaml
    ├── postgres-service.yaml
    ├── redis-deployment.yaml
    ├── redis-service.yaml
    ├── ingress.yaml
    ├── configmap.yaml
    ├── secrets.yaml
    ├── hpa.yaml
    └── _helpers.tpl
```

**Backend Deployment:**
```yaml
# templates/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "taps.fullname" . }}-backend
spec:
  replicas: {{ .Values.backend.replicaCount }}
  selector:
    matchLabels:
      app: {{ include "taps.name" . }}-backend
  template:
    metadata:
      labels:
        app: {{ include "taps.name" . }}-backend
    spec:
      containers:
      - name: backend
        image: "{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}"
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: {{ include "taps.fullname" . }}-secrets
              key: database-url
        - name: REDIS_URL
          value: "redis://{{ include "taps.fullname" . }}-redis:6379/0"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

**HorizontalPodAutoscaler:**
```yaml
# templates/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "taps.fullname" . }}-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "taps.fullname" . }}-backend
  minReplicas: {{ .Values.backend.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.backend.autoscaling.maxReplicas }}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ .Values.backend.autoscaling.targetCPUUtilizationPercentage }}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {{ .Values.backend.autoscaling.targetMemoryUtilizationPercentage }}
```

**Deploying with Helm:**
```bash
# Install chart
helm install taps ./k8s/helm/taps -f ./k8s/helm/taps/values-staging.yaml

# Upgrade chart
helm upgrade taps ./k8s/helm/taps -f ./k8s/helm/taps/values-production.yaml

# Rollback
helm rollback taps 1
```

**Files to Create:**
- `k8s/helm/taps/Chart.yaml`
- `k8s/helm/taps/values.yaml`
- `k8s/helm/taps/values-staging.yaml`
- `k8s/helm/taps/values-production.yaml`
- `k8s/helm/taps/templates/*.yaml` (10+ files)
- `docs/kubernetes-deployment.md`

---

## Task 6.6: Configure Monitoring (Prometheus + Grafana)

**Objective:** Set up comprehensive monitoring with Prometheus and Grafana.

**Scope:**
- Deploy Prometheus for metrics collection
- Deploy Grafana for visualization
- Configure metrics exporters
- Create Grafana dashboards
- Set up alerts
- Monitor application and infrastructure

**Prerequisites:**
- Kubernetes cluster with application deployed

**Deliverables:**
1. Prometheus deployment configuration
2. Grafana deployment configuration
3. Metrics exporters for backend, postgres, redis
4. Grafana dashboards (application, infrastructure)
5. Alert rules configuration
6. Monitoring documentation

**Acceptance Criteria:**
- [ ] Prometheus collecting metrics from all services
- [ ] Grafana dashboards visualizing key metrics
- [ ] Alerts configured for critical conditions
- [ ] Metrics retention configured (30 days)
- [ ] Dashboards accessible to team
- [ ] Alert notifications sent to Slack/email

**Metrics to Monitor:**
```
Application Metrics:
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate
- Active users
- Cache hit rate
- Database query duration

Infrastructure Metrics:
- CPU usage
- Memory usage
- Disk I/O
- Network I/O
- Pod count
- Container restarts

Database Metrics:
- Connection pool usage
- Query duration
- Slow queries
- Deadlocks
- Cache hit ratio

Redis Metrics:
- Memory usage
- Hit rate
- Evicted keys
- Connected clients
```

**Prometheus Configuration:**
```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'taps-backend'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: taps-backend

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

**Grafana Dashboards:**
```
1. Application Overview Dashboard
   - Request rate
   - Response time
   - Error rate
   - Active users

2. API Performance Dashboard
   - Endpoint response times
   - Endpoint error rates
   - Slowest endpoints
   - Request distribution

3. Database Dashboard
   - Connection pool usage
   - Query duration
   - Slow queries
   - Cache hit ratio

4. Infrastructure Dashboard
   - CPU usage per pod
   - Memory usage per pod
   - Network I/O
   - Disk I/O
```

**Alert Rules:**
```yaml
# alert-rules.yaml
groups:
  - name: taps-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"

      - alert: DatabaseConnectionPoolExhausted
        expr: db_connection_pool_usage > 0.9
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool near exhaustion"
```

**Files to Create:**
- `k8s/monitoring/prometheus-deployment.yaml`
- `k8s/monitoring/prometheus-config.yaml`
- `k8s/monitoring/grafana-deployment.yaml`
- `k8s/monitoring/alert-rules.yaml`
- `grafana/dashboards/application-overview.json`
- `grafana/dashboards/api-performance.json`
- `grafana/dashboards/database.json`
- `docs/monitoring-setup.md`

---

## Task 6.7: Set Up Structured Logging (Loki/ELK)

**Objective:** Implement centralized structured logging with Loki or ELK stack.

**Scope:**
- Deploy Loki or Elasticsearch for log aggregation
- Configure log shipping from all services
- Set up log parsing and indexing
- Create log dashboards in Grafana/Kibana
- Configure log retention
- Add log-based alerts

**Prerequisites:**
- Structured logging implemented in backend (Task 2.8)
- Kubernetes cluster with application deployed

**Deliverables:**
1. Loki/Elasticsearch deployment
2. Log shipping configuration (Promtail/Fluentd)
3. Log parsing and indexing configuration
4. Log dashboards
5. Log-based alerts
6. Log retention policy

**Acceptance Criteria:**
- [ ] All application logs centralized
- [ ] Logs searchable by correlation ID, user, endpoint
- [ ] Log dashboards show error trends
- [ ] Log retention set to 30 days
- [ ] Log-based alerts configured
- [ ] Log volume manageable

**Loki Deployment:**
```yaml
# loki-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: loki
spec:
  replicas: 1
  selector:
    matchLabels:
      app: loki
  template:
    metadata:
      labels:
        app: loki
    spec:
      containers:
      - name: loki
        image: grafana/loki:latest
        ports:
        - containerPort: 3100
        volumeMounts:
        - name: loki-config
          mountPath: /etc/loki
        - name: loki-data
          mountPath: /loki
      volumes:
      - name: loki-config
        configMap:
          name: loki-config
      - name: loki-data
        persistentVolumeClaim:
          claimName: loki-pvc
```

**Promtail Configuration:**
```yaml
# promtail-config.yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        target_label: app
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
```

**Log Queries (LogQL):**
```
# All errors in last hour
{app="taps-backend"} |= "ERROR" | json

# Logs for specific correlation ID
{app="taps-backend"} | json | correlation_id="abc123"

# Slow requests (>1s)
{app="taps-backend"} | json | duration_ms > 1000

# Error rate over time
rate({app="taps-backend"} |= "ERROR" [5m])
```

**Log Dashboards:**
```
1. Error Logs Dashboard
   - Error count over time
   - Top error messages
   - Errors by endpoint
   - Errors by user

2. Request Logs Dashboard
   - Request rate
   - Request duration distribution
   - Slowest endpoints
   - Request by status code

3. Audit Logs Dashboard
   - User actions
   - Authentication events
   - Data modifications
```

**Files to Create:**
- `k8s/logging/loki-deployment.yaml`
- `k8s/logging/loki-config.yaml`
- `k8s/logging/promtail-daemonset.yaml`
- `k8s/logging/promtail-config.yaml`
- `grafana/dashboards/error-logs.json`
- `grafana/dashboards/request-logs.json`
- `docs/logging-setup.md`

---

## Task 6.8: Production Deployment and Smoke Testing

**Objective:** Deploy application to production and run smoke tests.

**Scope:**
- Deploy to production Kubernetes cluster
- Run smoke tests to verify deployment
- Verify all services healthy
- Test critical user flows
- Monitor for errors
- Document deployment process

**Prerequisites:**
- All testing completed (Tasks 6.1-6.4)
- Monitoring and logging configured (Tasks 6.6-6.7)
- Kubernetes Helm charts ready (Task 6.5)

**Deliverables:**
1. Production deployment checklist
2. Smoke test suite
3. Deployment runbook
4. Rollback plan
5. Post-deployment verification report

**Acceptance Criteria:**
- [ ] Application deployed to production
- [ ] All pods running and healthy
- [ ] All smoke tests passing
- [ ] No errors in logs
- [ ] Monitoring dashboards showing healthy metrics
- [ ] SSL certificates configured
- [ ] DNS configured
- [ ] Backup and disaster recovery tested

**Deployment Checklist:**
```
Pre-Deployment:
- [ ] All tests passing in CI
- [ ] Database migrations reviewed
- [ ] Secrets configured in Kubernetes
- [ ] SSL certificates valid
- [ ] DNS records updated
- [ ] Backup taken
- [ ] Rollback plan documented
- [ ] Team notified

Deployment:
- [ ] Deploy database migrations
- [ ] Deploy backend (rolling update)
- [ ] Deploy frontend (rolling update)
- [ ] Verify pods healthy
- [ ] Run smoke tests
- [ ] Check logs for errors
- [ ] Verify monitoring dashboards

Post-Deployment:
- [ ] Smoke tests passing
- [ ] Critical flows tested manually
- [ ] Performance metrics normal
- [ ] No errors in logs
- [ ] Team notified of success
- [ ] Documentation updated
```

**Smoke Test Suite:**
```bash
#!/bin/bash
# smoke-test.sh

BASE_URL="https://taps.example.com"

echo "Running smoke tests..."

# Test 1: Health check
echo "Test 1: Health check"
curl -f "$BASE_URL/api/v1/health" || exit 1

# Test 2: Frontend loads
echo "Test 2: Frontend loads"
curl -f "$BASE_URL" || exit 1

# Test 3: API authentication
echo "Test 3: API authentication"
TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  | jq -r '.access_token')

[ -n "$TOKEN" ] || exit 1

# Test 4: List projects
echo "Test 4: List projects"
curl -f "$BASE_URL/api/v1/projects" \
  -H "Authorization: Bearer $TOKEN" || exit 1

# Test 5: Database connectivity
echo "Test 5: Database connectivity"
curl -f "$BASE_URL/api/v1/projects" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -e '.items | length >= 0' || exit 1

# Test 6: Redis connectivity
echo "Test 6: Redis connectivity (cache)"
curl -f "$BASE_URL/api/v1/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -w "%{time_total}" || exit 1

echo "All smoke tests passed!"
```

**Deployment Commands:**
```bash
# 1. Deploy database migrations
kubectl exec -it taps-backend-pod -- alembic upgrade head

# 2. Deploy application
helm upgrade taps ./k8s/helm/taps \
  -f ./k8s/helm/taps/values-production.yaml \
  --namespace production

# 3. Wait for rollout
kubectl rollout status deployment/taps-backend -n production
kubectl rollout status deployment/taps-frontend -n production

# 4. Run smoke tests
./smoke-test.sh

# 5. Monitor logs
kubectl logs -f deployment/taps-backend -n production
```

**Rollback Plan:**
```bash
# Rollback to previous version
helm rollback taps -n production

# Or rollback specific deployment
kubectl rollout undo deployment/taps-backend -n production

# Verify rollback
kubectl rollout status deployment/taps-backend -n production
./smoke-test.sh
```

**Files to Create:**
- `scripts/smoke-test.sh`
- `scripts/deploy-production.sh`
- `scripts/rollback.sh`
- `docs/deployment-runbook.md`
- `docs/rollback-plan.md`
- `docs/post-deployment-verification.md`

---

## Task 6.9: Documentation (API Docs, Runbooks, Architecture)

**Objective:** Create comprehensive documentation for the application.

**Scope:**
- Generate API documentation (OpenAPI/Swagger)
- Write architecture documentation
- Create operational runbooks
- Document deployment procedures
- Write user guides
- Create troubleshooting guides

**Prerequisites:**
- All features implemented and deployed

**Deliverables:**
1. API documentation (auto-generated from OpenAPI)
2. Architecture documentation with diagrams
3. Operational runbooks
4. Deployment guide
5. User guide
6. Troubleshooting guide
7. Contributing guide

**Acceptance Criteria:**
- [ ] API documentation complete and accessible
- [ ] Architecture diagrams created
- [ ] Runbooks cover common operations
- [ ] Deployment guide tested
- [ ] User guide covers all features
- [ ] Troubleshooting guide covers common issues
- [ ] Documentation hosted and searchable

**Documentation Structure:**
```
docs/
├── README.md
├── architecture/
│   ├── overview.md
│   ├── backend-architecture.md
│   ├── frontend-architecture.md
│   ├── database-schema.md
│   ├── caching-strategy.md
│   └── diagrams/
│       ├── high-level-architecture.png
│       ├── backend-modules.png
│       ├── frontend-components.png
│       └── data-flow.png
├── api/
│   ├── README.md
│   ├── authentication.md
│   ├── projects.md
│   ├── executions.md
│   ├── reports.md
│   ├── defects.md
│   └── analytics.md
├── deployment/
│   ├── local-development.md
│   ├── docker-compose.md
│   ├── kubernetes.md
│   ├── environment-variables.md
│   └── database-migrations.md
├── operations/
│   ├── runbooks/
│   │   ├── deployment.md
│   │   ├── rollback.md
│   │   ├── scaling.md
│   │   ├── backup-restore.md
│   │   └── incident-response.md
│   ├── monitoring.md
│   ├── logging.md
│   └── troubleshooting.md
├── user-guide/
│   ├── getting-started.md
│   ├── projects.md
│   ├── executions.md
│   ├── trends.md
│   ├── defects.md
│   ├── ai-analysis.md
│   └── settings.md
└── development/
    ├── setup.md
    ├── contributing.md
    ├── code-style.md
    ├── testing.md
    └── release-process.md
```

**API Documentation (Auto-Generated):**
```python
# FastAPI automatically generates OpenAPI docs
# Accessible at:
# - http://localhost:8000/docs (Swagger UI)
# - http://localhost:8000/redoc (ReDoc)

# Enhance with descriptions:
@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=201,
    summary="Create a new project",
    description="""
    Create a new project with the provided details.
    
    **Required fields:**
    - name: Project name (min 3 characters)
    - owner: Project owner email
    
    **Optional fields:**
    - description: Project description
    - repo_url: Repository URL
    """,
    responses={
        201: {"description": "Project created successfully"},
        400: {"description": "Invalid request data"},
        401: {"description": "Unauthorized"},
    },
)
async def create_project(...):
    ...
```

**Architecture Diagrams:**
```
Tools to use:
- draw.io / diagrams.net (free, web-based)
- Mermaid (markdown-based diagrams)
- PlantUML (code-based diagrams)

Diagrams to create:
1. High-level architecture
2. Backend module structure
3. Frontend component hierarchy
4. Database schema (ERD)
5. Data flow diagrams
6. Deployment architecture
```

**Runbook Template:**
```markdown
# Runbook: [Operation Name]

## Overview
Brief description of the operation.

## Prerequisites
- List prerequisites
- Required access/permissions
- Required tools

## Procedure
1. Step-by-step instructions
2. Include commands
3. Include expected outputs

## Verification
How to verify the operation succeeded.

## Rollback
How to rollback if something goes wrong.

## Troubleshooting
Common issues and solutions.
```

**Files to Create:**
- `docs/README.md`
- `docs/architecture/*.md` (5+ files)
- `docs/api/*.md` (6+ files)
- `docs/deployment/*.md` (5+ files)
- `docs/operations/runbooks/*.md` (5+ files)
- `docs/user-guide/*.md` (7+ files)
- `docs/development/*.md` (5+ files)
- Architecture diagrams (PNG/SVG)

---

# COMPLETION CHECKLIST

Use this checklist to track overall migration progress:

## Phase 1: Foundation
- [ ] Task 1.1: Next.js project initialized
- [ ] Task 1.2: Backend restructured
- [ ] Task 1.3: PostgreSQL and Redis configured
- [ ] Task 1.4: Alembic migrations set up
- [ ] Task 1.5: CI/CD pipeline configured
- [ ] Task 1.6: Code quality tools configured
- [ ] Task 1.7: Environment management set up
- [ ] Task 1.8: Data migrated to PostgreSQL

## Phase 2: Backend API Migration
- [ ] Task 2.1: Authentication implemented
- [ ] Task 2.2: Projects API migrated
- [ ] Task 2.3: Report upload migrated
- [ ] Task 2.4: Execution API migrated
- [ ] Task 2.5: Defect Management API implemented
- [ ] Task 2.6: API versioning implemented
- [ ] Task 2.7: Rate limiting implemented
- [ ] Task 2.8: Structured logging implemented
- [ ] Task 2.9: N+1 queries fixed
- [ ] Task 2.10: Backend tests written

## Phase 3: Frontend Migration
- [ ] Task 3.1: Shared layout built
- [ ] Task 3.2: Atom components built
- [ ] Task 3.3: Molecule components built
- [ ] Task 3.4: Projects dashboard migrated
- [ ] Task 3.5: Execution summary migrated
- [ ] Task 3.6: Trends page migrated
- [ ] Task 3.7: Module details migrated
- [ ] Task 3.8: Defect management built
- [ ] Task 3.9: Settings page built
- [ ] Task 3.10: TanStack Query hooks implemented
- [ ] Task 3.11: Zustand stores implemented
- [ ] Task 3.12: Loading states and error boundaries added

## Phase 4: Advanced Features
- [ ] Task 4.1: AI analysis migrated
- [ ] Task 4.2: WebSocket implemented
- [ ] Task 4.3: Export functionality added
- [ ] Task 4.4: Dark mode implemented
- [ ] Task 4.5: Keyboard shortcuts and accessibility
- [ ] Task 4.6: Notification system implemented

## Phase 5: Performance Optimization
- [ ] Task 5.1: Redis caching implemented
- [ ] Task 5.2: Connection pooling configured
- [ ] Task 5.3: Bundle optimized
- [ ] Task 5.4: Virtual scrolling implemented
- [ ] Task 5.5: Response compression enabled
- [ ] Task 5.6: CDN configured
- [ ] Task 5.7: Performance profiling completed
- [ ] Task 5.8: Security hardening completed

## Phase 6: Testing & Deployment
- [ ] Task 6.1: Frontend unit tests written
- [ ] Task 6.2: E2E tests written
- [ ] Task 6.3: Backend integration tests written
- [ ] Task 6.4: Load testing completed
- [ ] Task 6.5: Kubernetes Helm charts created
- [ ] Task 6.6: Monitoring configured
- [ ] Task 6.7: Logging configured
- [ ] Task 6.8: Production deployment completed
- [ ] Task 6.9: Documentation completed

---

**Total Tasks:** 53
**Estimated Timeline:** 14 weeks with 2-3 engineers
**Migration Status:** Ready for execution

---

*Document Version: 1.0*  
*Created: Based on TAPS Migration Plan*  
*Purpose: AI Model Executable Task Breakdown*
