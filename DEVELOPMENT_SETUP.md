# Development Setup

Developer bootstrap for `tax-os-backend` on the Ubuntu VM (or equivalent Linux host).

All commands assume repository root:

```bash
cd /opt/tax-os/repos/tax-os-backend
```

## Prerequisites

- Python 3.14+ with `venv` support
- Docker (for `taxos-postgres` and optional pgAdmin)
- `postgresql-client` package (`pg_isready`, `psql`) recommended
- Git

## Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Verify:

```bash
python -c "import fastapi, sqlalchemy, alembic; print('ok')"
```

## Environment Variables

Create `backend/.env` (not committed). Required keys match `app.core.config.Settings`:

```bash
cp .env.example backend/.env
# Edit backend/.env with real credentials
```

Example `backend/.env`:

```env
APP_NAME=tax-os
APP_ENV=development

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=taxos
POSTGRES_USER=taxos
POSTGRES_PASSWORD=<your-password>
```

Settings are loaded from `backend/.env` relative to the working directory used when importing the app (run API and Alembic from repository root).

## Docker / PostgreSQL

Start infrastructure per your VM layout (container name is commonly `taxos-postgres`):

```bash
docker ps
docker start taxos-postgres   # if stopped
```

Verify PostgreSQL:

```bash
pg_isready -h localhost -p 5432 -U taxos
```

Create application database if it does not exist (one-time, as superuser or via container exec):

```bash
docker exec -it taxos-postgres psql -U taxos -d postgres -c "CREATE DATABASE taxos;"
```

Create test database for integration tests:

```bash
docker exec -it taxos-postgres psql -U taxos -d postgres -c "CREATE DATABASE taxos_test;"
```

## Migrations

From repository root with venv active and `backend/.env` configured:

```bash
alembic current
alembic upgrade head
```

Expected head revision: `fd6be8e34b7b`.

Verify downgrade/upgrade cycle in a non-production database before relying on a new revision — see [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md).

## FastAPI Startup

From repository root:

```bash
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

Health check:

```bash
curl -s http://localhost:8000/health | jq .
```

Interactive API docs: `http://localhost:8000/docs`

## Test Execution

Integration tests require a reachable test database. Configure test variables (development defaults shown):

```bash
export TEST_POSTGRES_HOST=localhost
export TEST_POSTGRES_PORT=5432
export TEST_POSTGRES_DB=taxos_test
export TEST_POSTGRES_USER=taxos
export TEST_POSTGRES_PASSWORD='<same as POSTGRES_PASSWORD>'
```

Or set a single URL:

```bash
export TEST_DATABASE_URL="postgresql://taxos:<password>@localhost:5432/taxos_test"
```

Run tests:

```bash
source .venv/bin/activate
pytest -q
pytest -q -m integration   # integration tests only
```

**Acceptance rule:** `pytest -q` must **pass** integration tests on the VM with PostgreSQL running. Skipped integration tests (DB unreachable) are not sufficient for TASK-001F merge acceptance.

## Common Setup Failures

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `Connection refused` on port 5432 | Postgres container stopped | `docker start taxos-postgres` |
| Alembic cannot connect | Wrong `backend/.env` | Verify `POSTGRES_*` values |
| `ModuleNotFoundError: app` | Wrong working directory | Run from repo root; use `--app-dir backend` for uvicorn |
| All tests skipped | Test DB unreachable | Set `TEST_POSTGRES_*` and ensure `taxos_test` exists |

## Next Steps

- [OPERATIONAL_RUNBOOK.md](OPERATIONAL_RUNBOOK.md) — operations
- [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md) — schema changes
- [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) — task and AI workflow
