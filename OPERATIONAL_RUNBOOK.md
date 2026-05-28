# Operational Runbook

Day-to-day procedures for `tax-os-backend` on the Ubuntu VM.

Repository root:

```bash
cd /opt/tax-os/repos/tax-os-backend
```

## Service Inventory

| Component | Typical name | Port | Notes |
|-----------|--------------|------|-------|
| PostgreSQL 16 | `taxos-postgres` (Docker) | 5432 | Primary data store |
| FastAPI | `uvicorn` process | 8000 | Backend API |
| pgAdmin | Docker (optional) | varies | DB administration UI |

Docker Compose files may live outside this repository; use `docker ps` to identify actual container names on the VM.

## Docker Operations

List containers:

```bash
docker ps -a
```

Start PostgreSQL:

```bash
docker start taxos-postgres
```

Stop PostgreSQL (maintenance only—stops API dependency):

```bash
docker stop taxos-postgres
```

Container logs:

```bash
docker logs taxos-postgres --tail 100
docker logs -f taxos-postgres
```

Shell into database container:

```bash
docker exec -it taxos-postgres psql -U taxos -d taxos
```

## PostgreSQL Verification

Readiness:

```bash
pg_isready -h localhost -p 5432 -U taxos
```

Simple query:

```bash
psql -h localhost -p 5432 -U taxos -d taxos -c "SELECT 1;"
```

List tables:

```bash
psql -h localhost -p 5432 -U taxos -d taxos -c "\dt"
```

Expected core tables: `countries`, `tax_types`, `source_documents`, `source_versions`, `source_retrieval_log`, `audit_log`.

## Environment Verification

Confirm `backend/.env` exists and matches running Postgres:

```bash
grep -E '^POSTGRES_' backend/.env
```

Application settings are read at import time from `backend/.env`.

## Migration Execution

From repository root with venv active:

```bash
source .venv/bin/activate
alembic current
alembic upgrade head
```

After upgrade, verify:

```bash
alembic current
psql -h localhost -p 5432 -U taxos -d taxos -c "\dt"
```

See [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md) for downgrade and rebuild procedures.

## FastAPI Service

Start (development):

```bash
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

Restart: stop the uvicorn process (`Ctrl+C` or `kill <pid>`), then start again.

Health check:

```bash
curl -s http://localhost:8000/health
```

Expected: `{"status":"ok","environment":"development"}` (environment value follows `APP_ENV`).

## Log Locations

| Source | Location |
|--------|----------|
| FastAPI / uvicorn | Terminal stdout where process was started |
| PostgreSQL | `docker logs taxos-postgres` |
| Alembic | Terminal stdout during `alembic` commands |

No centralized log aggregation is configured in the current phase.

## Routine Checks

Daily or pre-release:

```bash
docker ps | grep taxos-postgres
pg_isready -h localhost -p 5432 -U taxos
curl -s http://localhost:8000/health
alembic current
```

Pre-merge (with test env):

```bash
export TEST_POSTGRES_HOST=localhost
export TEST_POSTGRES_PORT=5432
export TEST_POSTGRES_DB=taxos_test
export TEST_POSTGRES_USER=taxos
export TEST_POSTGRES_PASSWORD='<password>'
pytest -q
```

## Common Failure Handling

### PostgreSQL connection refused

1. `docker ps` — confirm `taxos-postgres` is running.
2. `docker start taxos-postgres`.
3. `pg_isready -h localhost -p 5432 -U taxos`.

### API returns 500 on CRUD

1. Check API terminal for stack trace.
2. Verify migrations: `alembic current` matches expected head.
3. Verify FK targets exist (e.g. country before tax_type).

### Migration fails mid-run

1. Do not apply manual SQL fixes without governance review.
2. See [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md) and [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md).

### Integration tests skipped

Tests skip when test DB is unreachable. This is expected in environments without Postgres; it is **not** merge acceptance for TASK-001F. Run `pytest -q` on the VM with `TEST_POSTGRES_*` configured.

## Related Documents

- [BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md)
- [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md)
- [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md)
