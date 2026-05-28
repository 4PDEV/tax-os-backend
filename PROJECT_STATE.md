# Project State

Canonical snapshot for `tax-os-backend`. Update this file when tasks complete or infrastructure changes.

**Last updated:** 2026-05-28

## Infrastructure

| Component | Status | Notes |
|-----------|--------|-------|
| Ubuntu VM | Operational | Primary dev host |
| Docker | Operational | `taxos-postgres` container |
| PostgreSQL 16 | Operational | DB `taxos`, port 5432 |
| pgAdmin | Operational | Optional admin UI |
| GitHub | Operational | `tax-os-backend` repository |

## Application State

| Area | Status |
|------|--------|
| FastAPI | Operational |
| SQLAlchemy 2.x | Operational |
| Alembic | Operational — head `fd6be8e34b7b` |
| Internal admin CRUD | Operational |
| Authentication | Not implemented (by design, current phase) |
| Frontend | Not in this repository |
| AI / embeddings | Not implemented |

## Database Tables

- `countries`
- `tax_types`
- `source_documents`
- `source_versions` (immutable via API: no PUT/DELETE routes)
- `source_retrieval_log`
- `audit_log`

## API Endpoints (Current)

| Prefix | Methods |
|--------|---------|
| `/health` | GET |
| `/countries` | POST, GET, GET/{id}, PUT/{id}, DELETE/{id} (soft) |
| `/tax-types` | POST, GET, GET/{id}, PUT/{id}, DELETE/{id} (soft) |
| `/source-documents` | POST, GET, GET/{id}, PUT/{id}, DELETE/{id} (soft) |
| `/source-versions` | POST, GET, GET/{id} only |

## Completed Tasks

| Task | Summary |
|------|---------|
| TASK-001 (series) | Source registry foundation |
| TASK-001C | Alembic infrastructure |
| TASK-001E | Migration discipline |
| TASK-001 (CRUD) | Admin CRUD APIs — tag `v0.1.1-crud-foundation` |
| TASK-001F | Baseline API tests — **implementation accepted; VM merge acceptance pending** |
| TASK-001G | Documentation + operational runbook |

## Active Tasks

None formally in progress in this snapshot.

## Pending / Follow-Up

| Item | Notes |
|------|-------|
| TASK-001F final acceptance | Run `pytest -q` on VM with `TEST_POSTGRES_*` — must pass, not skip |
| Source file storage | `storage_path` on versions; backup procedures documented, implementation evolving |
| Audit log population | Table exists; write path not yet in CRUD APIs |
| Retrieval pipeline | Out of current phase |

## Testing

- Location: `backend/tests/`
- Marker: `@pytest.mark.integration` (module-level `pytestmark`)
- Skip guard: integration tests skip with clear message if test DB unreachable
- **Sandbox-only skipped runs are not merge acceptance**

## Known Limitations

See [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md).

## Operational Notes

- Application config: `backend/.env` (`POSTGRES_*`, `APP_NAME`, `APP_ENV`).
- Run Alembic and uvicorn from repository root.
- Test DB defaults: `taxos_test` via `TEST_POSTGRES_*` or `TEST_DATABASE_URL`.
- Docker container name on VM: commonly `taxos-postgres` (confirm with `docker ps`).

## Repository Paths

```
/opt/tax-os/repos/tax-os-backend
```
