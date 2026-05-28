# Release Checklist

Controlled release discipline for `tax-os-backend` tags and merges to `main`.

Use this checklist before tagging (e.g. `v0.1.x`) or declaring a task merge-ready.

## Pre-Release

### Code and scope

- [ ] All changes tied to approved task ID(s)
- [ ] No scope creep (auth, frontend, AI, vector DB, unrelated refactors)
- [ ] Feature branch rebased or merged cleanly with `main`

### Tests

- [ ] VM: PostgreSQL running (`pg_isready -h localhost -p 5432 -U taxos`)
- [ ] VM: `TEST_POSTGRES_*` configured for `taxos_test`
- [ ] `pytest -q` — **passed** (not all integration tests skipped)
- [ ] Immutability tests verified for `source_versions` (PUT/DELETE → 405)

### Migrations

- [ ] `alembic current` shows expected head revision
- [ ] `alembic upgrade head` succeeds on target database
- [ ] `alembic downgrade -1` then `alembic upgrade head` verified on non-production DB
- [ ] No direct manual schema changes

### Documentation

- [ ] `PROJECT_STATE.md` updated
- [ ] `CHANGELOG.md` updated for release
- [ ] `TASK_REGISTRY.md` updated
- [ ] Operational docs updated if procedures changed

### Backup

- [ ] `pg_dump` taken and stored with timestamp
- [ ] Backup path and Alembic revision recorded
- [ ] Git pushed to remote

### Runtime verification

- [ ] `curl http://localhost:8000/health` returns ok
- [ ] Spot-check one CRUD path per major resource (optional smoke)

## Release Execution

```bash
cd /opt/tax-os/repos/tax-os-backend
git tag -a v0.1.x -m "Release v0.1.x: <summary>"
git push origin v0.1.x
```

On target environment:

```bash
git pull
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
# restart uvicorn
```

## Post-Release

- [ ] Confirm `alembic current` on environment
- [ ] Confirm health endpoint
- [ ] Archive backup metadata with release notes

## Rollback Readiness

Before release, confirm:

- [ ] Previous git tag/commit identified
- [ ] Reversible migration path documented OR backup restore path confirmed
- [ ] `BACKUP_AND_RECOVERY.md` restore steps understood

## No-Go Conditions

Do not release if:

- integration tests only skipped (DB unreachable)
- migration downgrade untested for new revision
- undocumented breaking API change
- secrets committed or present in artifacts

## Related Documents

- [TASK_EXECUTION_STANDARD.md](TASK_EXECUTION_STANDARD.md)
- [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md)
- [BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md)
