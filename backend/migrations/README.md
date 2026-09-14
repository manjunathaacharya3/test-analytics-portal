# Alembic Database Migrations

This directory contains Alembic database migrations for the Test Analytics Portal.

## Overview

Alembic is used to manage database schema changes in a version-controlled manner. Each migration file represents a specific change to the database schema.

## Migration Files

- **001_initial_migration.py**: Creates the initial database schema with 4 tables:
  - `projects`: Stores project information
  - `modules`: Stores test modules belonging to projects
  - `executions`: Stores test execution results
  - `scenarios`: Stores individual test scenario results

## Indexes Created

### Standard Indexes (8 total)
1. `idx_projects_name` - Index on projects.name
2. `idx_projects_owner` - Index on projects.owner
3. `idx_modules_project_id` - Index on modules.project_id
4. `idx_modules_project_name` - Unique composite index on modules(project_id, name)
5. `idx_executions_module_id` - Index on executions.module_id
6. `idx_executions_created_at` - Index on executions.created_at (DESC)
7. `idx_scenarios_execution_id` - Index on scenarios.execution_id
8. `idx_scenarios_status` - Index on scenarios.status

### Full-Text Search Index
- `idx_scenarios_error_fulltext` - GIN index on scenarios.error for full-text search

## Running Migrations

### Apply migrations (upgrade to latest)
```bash
cd backend
alembic upgrade head
```

### Rollback migrations (downgrade)
```bash
cd backend
alembic downgrade base  # Rollback all migrations
alembic downgrade -1    # Rollback one migration
```

### View migration history
```bash
cd backend
alembic history
alembic current
```

### Create a new migration
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

## Configuration

- **alembic.ini**: Alembic configuration file
- **env.py**: Migration environment configuration
  - Configured for synchronous PostgreSQL connections using psycopg2
  - Loads database URL from environment variable `DATABASE_URL`
  - Imports all SQLAlchemy models for autogenerate support

## Database Connection

The migration system uses the `DATABASE_URL` environment variable:
```
DATABASE_URL=postgresql://taps_user:password@localhost:5432/taps
```

Note: For migrations, the async driver (`postgresql+asyncpg://`) is automatically converted to sync driver (`postgresql://`) as Alembic requires psycopg2.

## Prerequisites

- PostgreSQL 16+ running and accessible
- Python packages installed: `alembic`, `sqlalchemy`, `psycopg2-binary`
- Database created: `taps`
- Database user created with appropriate permissions

## Troubleshooting

### Connection refused error
Ensure PostgreSQL is running:
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Start PostgreSQL (Docker)
docker-compose up -d postgres
```

### Module import errors
Ensure you're running commands from the `backend` directory and all dependencies are installed:
```bash
cd backend
pip install -r requirements.txt
```
