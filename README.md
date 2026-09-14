# TAPS Docker Compose Setup

## Task 1.3: PostgreSQL 16 and Redis 7 with Docker Compose

This directory contains the production-ready Docker Compose configuration for the Test Analytics & Predictive System (TAPS) migration project.

## Services

The Docker Compose setup includes the following services:

### 1. PostgreSQL 16 (`postgres`)
- **Image**: `postgres:16-alpine`
- **Port**: `5432`
- **Database**: `taps`
- **User**: `taps_user`
- **Features**:
  - Health checks with `pg_isready`
  - Persistent volume for data storage
  - Automatic initialization scripts
  - UTF-8 encoding
  - Production-ready configuration

### 2. Redis 7 (`redis`)
- **Image**: `redis:7-alpine`
- **Port**: `6379`
- **Features**:
  - Custom configuration file (`redis.conf`)
  - 256MB memory limit with LRU eviction policy
  - Health checks with `redis-cli ping`
  - Persistent volume for data storage
  - RDB snapshots for persistence

### 3. Backend Service (`backend`)
- **Build**: `./backend/Dockerfile`
- **Port**: `8000`
- **Features**:
  - Depends on PostgreSQL and Redis (waits for health checks)
  - Environment variables for database connections
  - Health check endpoint at `/health`
  - Auto-restart on failure

### 4. pgAdmin 4 (`pgadmin`) - Optional
- **Image**: `dpage/pgadmin4:latest`
- **Port**: `5050` (HTTP)
- **Features**:
  - Web-based PostgreSQL management interface
  - Pre-configured to connect to the `postgres` service
  - Persistent volume for configuration

## Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+

### 1. Environment Setup

Copy the environment template and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` and update the following critical variables:
- `DB_PASSWORD`: Strong password for PostgreSQL
- `JWT_SECRET_KEY`: Secure random string for authentication
- `ALLOWED_ORIGINS`: Your frontend URL(s)

### 2. Start Services

**Start all services:**
```bash
docker-compose up -d
```

**Start specific services (PostgreSQL and Redis only):**
```bash
docker-compose up -d postgres redis
```

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f backend
```

### 3. Verify Services

**Check service health:**
```bash
docker-compose ps
```

All services should show `healthy` status.

**Test PostgreSQL connection:**
```bash
docker-compose exec postgres psql -U taps_user -d taps -c "SELECT version();"
```

**Test Redis connection:**
```bash
docker-compose exec redis redis-cli ping
# Expected output: PONG
```

**Test backend health:**
```bash
curl http://localhost:8000/health
```

### 4. Access Services

- **PostgreSQL**: `localhost:5432`
  - Database: `taps`
  - Username: `taps_user`
  - Password: (from `.env` file)

- **Redis**: `localhost:6379`

- **Backend API**: `http://localhost:8000`
  - Health: `http://localhost:8000/health`
  - API Docs: `http://localhost:8000/docs` (when implemented)

- **pgAdmin**: `http://localhost:5050`
  - Email: (from `.env` file, default: `admin@taps.local`)
  - Password: (from `.env` file, default: `admin`)

## File Structure

```
.
├── docker-compose.yml          # Main Docker Compose configuration
├── .env.example                # Environment variables template
├── .env                        # Your environment variables (gitignored)
├── redis.conf                  # Redis production configuration
├── init-scripts/               # PostgreSQL initialization scripts
│   ├── init-db.sql            # Database setup and extensions
│   └── README.md              # Initialization scripts documentation
└── README.md                   # This file
```

## Configuration Details

### PostgreSQL Configuration

- **Health Check**: Runs every 5 seconds with 5 retries
- **Initialization**: Scripts in `init-scripts/` run on first startup
- **Extensions Enabled**:
  - `uuid-ossp`: UUID generation
  - `pg_trgm`: Full-text search support
- **Timezone**: UTC
- **Encoding**: UTF-8

### Redis Configuration

- **Memory Limit**: 256MB
- **Eviction Policy**: `allkeys-lru` (evicts least recently used keys)
- **Persistence**: RDB snapshots
  - Save after 900s if 1+ keys changed
  - Save after 300s if 10+ keys changed
  - Save after 60s if 10000+ keys changed
- **Slow Log**: Queries slower than 10ms logged
- **Max Connections**: Managed by client (backend: 50)

### Networking

- **Network**: `taps-network` (bridge driver)
- All services communicate via service names (e.g., `postgres`, `redis`)
- Only necessary ports exposed to host

### Volumes

- `postgres_data`: PostgreSQL data persistence
- `redis_data`: Redis data persistence
- `pgadmin_data`: pgAdmin configuration persistence

All volumes use local driver and persist across container restarts.

## Common Operations

### Stop Services

```bash
# Stop all services
docker-compose stop

# Stop specific service
docker-compose stop postgres
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart redis
```

### Remove Services (keeps volumes)

```bash
docker-compose down
```

### Remove Services and Volumes (⚠️ deletes all data)

```bash
docker-compose down -v
```

### View Resource Usage

```bash
docker stats
```

### Execute Commands in Containers

**PostgreSQL:**
```bash
# Open psql shell
docker-compose exec postgres psql -U taps_user -d taps

# Run SQL file
docker-compose exec -T postgres psql -U taps_user -d taps < backup.sql
```

**Redis:**
```bash
# Open redis-cli
docker-compose exec redis redis-cli

# Get Redis info
docker-compose exec redis redis-cli INFO
```

**Backend:**
```bash
# Open shell
docker-compose exec backend /bin/sh

# Run database migrations (when implemented)
docker-compose exec backend alembic upgrade head
```

## Backup and Restore

### PostgreSQL Backup

```bash
# Backup database
docker-compose exec -T postgres pg_dump -U taps_user taps > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup with compression
docker-compose exec -T postgres pg_dump -U taps_user taps | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### PostgreSQL Restore

```bash
# Restore from backup
docker-compose exec -T postgres psql -U taps_user -d taps < backup.sql

# Restore from compressed backup
gunzip -c backup.sql.gz | docker-compose exec -T postgres psql -U taps_user -d taps
```

### Redis Backup

```bash
# Trigger RDB snapshot
docker-compose exec redis redis-cli BGSAVE

# Copy RDB file
docker cp taps-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d_%H%M%S).rdb
```

### Redis Restore

```bash
# Stop Redis
docker-compose stop redis

# Copy RDB file to volume
docker cp redis_backup.rdb taps-redis:/data/dump.rdb

# Start Redis
docker-compose start redis
```

## Troubleshooting

### PostgreSQL won't start

1. Check logs: `docker-compose logs postgres`
2. Verify volume permissions
3. Ensure port 5432 is not in use: `lsof -i :5432` (macOS/Linux) or `netstat -ano | findstr :5432` (Windows)
4. Try removing volume and restarting: `docker-compose down -v && docker-compose up -d`

### Redis won't start

1. Check logs: `docker-compose logs redis`
2. Verify `redis.conf` syntax
3. Ensure port 6379 is not in use
4. Check memory limits

### Backend can't connect to databases

1. Verify services are healthy: `docker-compose ps`
2. Check environment variables in `.env`
3. Verify network connectivity: `docker-compose exec backend ping postgres`
4. Check logs: `docker-compose logs backend`

### Data not persisting

1. Verify volumes exist: `docker volume ls | grep taps`
2. Check volume mounts in `docker-compose.yml`
3. Ensure you're not using `docker-compose down -v` (which deletes volumes)

### pgAdmin can't connect to PostgreSQL

1. In pgAdmin, add new server:
   - **Host**: `postgres` (not `localhost`)
   - **Port**: `5432`
   - **Database**: `taps`
   - **Username**: `taps_user`
   - **Password**: (from `.env`)

## Acceptance Criteria Verification

Task 1.3 Acceptance Criteria:

- ✅ `docker-compose up -d postgres redis` starts both services
- ✅ PostgreSQL accessible on port 5432 with credentials
- ✅ Redis accessible on port 6379
- ✅ Health checks pass for both services
- ✅ Data persists after container restart
- ✅ Backend can connect to both PostgreSQL and Redis

**Verification Commands:**

```bash
# 1. Start services
docker-compose up -d postgres redis

# 2. Check health status
docker-compose ps
# Expected: postgres and redis show "healthy"

# 3. Test PostgreSQL connection
docker-compose exec postgres psql -U taps_user -d taps -c "SELECT 1;"
# Expected: Output shows "1"

# 4. Test Redis connection
docker-compose exec redis redis-cli ping
# Expected: PONG

# 5. Test data persistence
docker-compose exec redis redis-cli SET test_key "test_value"
docker-compose restart redis
docker-compose exec redis redis-cli GET test_key
# Expected: "test_value"

# 6. Start backend and verify connections
docker-compose up -d backend
docker-compose logs backend
# Expected: No connection errors in logs
```

## Production Deployment Notes

### Security Considerations

1. **Change default passwords**: Update `DB_PASSWORD`, `PGADMIN_PASSWORD` in `.env`
2. **Enable Redis authentication**: Uncomment `requirepass` in `redis.conf`
3. **Use secrets management**: Consider Docker secrets or external secret managers
4. **Restrict network access**: Use firewall rules to limit database access
5. **Enable SSL/TLS**: Configure PostgreSQL and Redis for encrypted connections

### Performance Tuning

1. **PostgreSQL**:
   - Adjust `shared_buffers`, `work_mem`, `maintenance_work_mem`
   - Configure connection pooling (pgBouncer)
   - Tune autovacuum settings

2. **Redis**:
   - Adjust `maxmemory` based on available RAM
   - Consider AOF persistence for critical data
   - Monitor memory usage and eviction metrics

3. **Docker**:
   - Set resource limits (CPU, memory) in `docker-compose.yml`
   - Use `--cpus` and `--memory` flags

### Monitoring

1. **PostgreSQL**: Use `pg_stat_statements` extension
2. **Redis**: Monitor with `redis-cli INFO` and `MONITOR`
3. **Docker**: Use `docker stats` or Prometheus exporters

## Next Steps

After completing Task 1.3, proceed to:

- **Task 1.4**: Configure Alembic Migrations from Existing Models
- **Task 1.5**: Set Up GitHub Actions CI/CD Pipeline
- **Task 1.8**: Migrate SQLite Data to PostgreSQL

## References

- [PostgreSQL 16 Documentation](https://www.postgresql.org/docs/16/)
- [Redis 7 Documentation](https://redis.io/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [TAPS Migration Plan](./MIGRATION_PLAN.md)
- [TAPS Low-Level Tasks](./MIGRATION_LOW_LEVEL_TASKS.md)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Docker Compose logs
3. Consult the TAPS migration documentation
4. Contact the development team

---

**Task 1.3 Status**: ✅ **COMPLETED**

**Created Files**:
- `docker-compose.yml` - Main configuration with all services
- `redis.conf` - Production-ready Redis configuration
- `.env.example` - Environment variables template
- `init-scripts/init-db.sql` - PostgreSQL initialization script
- `init-scripts/README.md` - Initialization scripts documentation
- `README.md` - This comprehensive setup guide
