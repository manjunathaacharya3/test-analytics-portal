# PostgreSQL Initialization Scripts

This directory contains SQL scripts that are automatically executed when the PostgreSQL container starts for the first time.

## Files

### init-db.sql

This script performs the following initialization tasks:

1. **Extensions**: Enables required PostgreSQL extensions
   - `uuid-ossp`: For UUID generation support
   - `pg_trgm`: For full-text search and trigram matching support

2. **Configuration**: Sets up database configuration
   - Sets timezone to UTC for consistent timestamp handling

3. **Permissions**: Grants necessary privileges
   - Grants all privileges on the `taps` database to `taps_user`
   - Sets default privileges for future tables, sequences, and functions

## Execution Order

Scripts in this directory are executed in alphabetical order by PostgreSQL's docker-entrypoint-initdb.d mechanism.

## Adding New Scripts

To add new initialization scripts:

1. Create a new `.sql` file in this directory
2. Name it with a numeric prefix to control execution order (e.g., `02-create-tables.sql`)
3. The script will automatically run on the next container initialization

**Note**: These scripts only run when the PostgreSQL data directory is empty (first-time initialization). To re-run scripts, you must delete the PostgreSQL volume:

```bash
docker-compose down -v
docker-compose up -d
```

## Best Practices

- Use `IF NOT EXISTS` clauses to make scripts idempotent
- Add comments to explain complex operations
- Keep scripts focused on a single responsibility
- Test scripts in a development environment before production use
