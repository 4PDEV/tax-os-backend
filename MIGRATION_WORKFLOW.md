# Migration Workflow

Alembic governance for `tax-os-backend`.

## Core Rule

**NO DIRECT DATABASE MODIFICATION.**

All schema changes must be expressed as Alembic revisions, reviewed, and applied via `alembic upgrade`. Manual `ALTER TABLE` in production or development undermines auditability and reproducibility.

## Layout

| Path | Purpose |
|------|---------|
| `alembic.ini` | Alembic configuration (repo root) |
| `backend/migrations/` | Script directory |
| `backend/migrations/versions/` | Revision files |
| `backend/migrations/env.py` | Runtime URL from `backend/.env` |

Current head: **`fd6be8e34b7b`** (`create_source_registry_tables`).

## Prerequisites

```bash
cd /opt/tax-os/repos/tax-os-backend
source .venv/bin/activate
# backend/.env must define POSTGRES_*
```

## Upgrade Procedures

Check current revision:

```bash
alembic current
alembic history
```

Apply latest:

```bash
alembic upgrade head
```

Apply one step:

```bash
alembic upgrade +1
```

## Downgrade Procedures

Downgrade one revision:

```bash
alembic downgrade -1
```

Downgrade to base (destructive—dev/test only):

```bash
alembic downgrade base
```

Always verify downgrade on a **non-production** database before relying on rollback in production.

## Migration Generation Workflow

1. Update SQLAlchemy models under `backend/app/models/`.
2. Ensure models are imported in `backend/app/models/__init__.py` and `backend/migrations/env.py`.
3. Generate revision:

```bash
alembic revision --autogenerate -m "short descriptive slug"
```

4. **Review** generated file manually. Autogenerate is advisory—not authoritative.
5. Test on empty database: `downgrade base` → `upgrade head`.
6. Test on database with seed data (dev clone).
7. Commit revision with bounded task reference.

## Migration Review Requirements

Every revision must be reviewed for:

- Correct table/column names and types
- Foreign keys and `ON DELETE` behavior
- Indexes and unique constraints
- Backward compatibility with existing API code
- Data migration safety (if `op.execute` used)
- Downgrade symmetry (or documented irreversibility)

## Rebuild Verification

Fresh rebuild procedure (test database recommended):

```bash
export TEST_POSTGRES_DB=taxos_test
# ensure DB exists and is empty or dropped/recreated

alembic downgrade base
alembic upgrade head
pytest -q -m integration
```

Integration test fixture also runs downgrade/upgrade at session start when DB is reachable.

## Prohibited Practices

- Manual schema edits via psql/pgAdmin without a matching Alembic revision.
- Editing applied migration files after they are merged to main (create a new revision instead).
- Skipping downgrade testing for reversible releases.
- Running `upgrade head` against production without backup — see [BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md).
- Changing `alembic_version` by hand except under documented incident recovery.

## Failure Handling

If `alembic upgrade` fails:

1. Capture full error output.
2. Do not apply ad-hoc SQL without incident process — see [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md).
3. Restore from backup if database is in unknown state.

## Related Documents

- [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md)
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
- [BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md)
