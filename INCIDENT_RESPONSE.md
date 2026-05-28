# Incident Response

Operational failure handling for `tax-os-backend`.

## Severity Guidance

| Level | Example | Response time target |
|-------|---------|----------------------|
| S1 | Production DB unavailable, data corruption suspected | Immediate |
| S2 | API down, migrations failed on release | Same day |
| S3 | Dev environment broken, tests failing | Next work session |

Adjust targets per deployment phase. Current phase is primarily development VM.

## Database Failure

### Symptoms

- `Connection refused` from API or Alembic
- `pg_isready` fails
- CRUD returns 500 with DB errors

### Response

1. `docker ps` — check `taxos-postgres` state.
2. `docker start taxos-postgres` or restart container per runbook.
3. `docker logs taxos-postgres --tail 200` — identify crash/OOM/disk full.
4. `pg_isready -h localhost -p 5432 -U taxos`
5. If data suspect: **stop writes**, take `pg_dump`, then investigate.

### Escalation

- Disk full on VM: expand volume or prune logs/images.
- Corrupted data: restore from [BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md).

## Docker Failure

### Symptoms

- `Cannot connect to Docker daemon`
- Container exit loop

### Response

1. `sudo systemctl status docker`
2. `sudo systemctl restart docker`
3. `docker ps -a` — inspect exit codes.
4. `docker start taxos-postgres`
5. Verify Postgres readiness before starting API.

### Escalation

- Recreate container from known compose/spec (document any volume mounts).
- Restore database from logical backup after container is healthy.

## Migration Failure

### Symptoms

- `alembic upgrade` aborts mid-transaction
- `alembic current` inconsistent with schema

### Response

1. Capture error and `alembic current` output.
2. **Do not** apply manual DDL without governance approval.
3. If transaction rolled back: fix revision file or model, re-run on test DB.
4. If unknown DB state: restore test DB from dump; for production, invoke backup restore procedure.

### Rollback

```bash
alembic downgrade -1
```

Only when downgrade is safe and reviewed. See [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md).

## Corrupted Environment Response

### Symptoms

- Mixed package versions
- Wrong Python interpreter
- Stale `.env` pointing to wrong host

### Response

1. Recreate venv:

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Verify `backend/.env`.
3. `alembic current` and `pytest -q` on test DB.

## API Failure (Non-DB)

### Symptoms

- Health OK but CRUD fails validation unexpectedly
- 405/404 not matching spec

### Response

1. Reproduce with `curl` or `/docs`.
2. Check recent commits for route/schema changes.
3. Run integration tests on VM.
4. Revert commit if regression confirmed and rollback is faster than fix-forward.

## Rollback Procedures

| Layer | Action |
|-------|--------|
| Application code | `git revert <commit>` or reset branch pre-merge |
| Schema | `alembic downgrade -1` (if reversible) |
| Data | `pg_restore` from last known-good dump |
| Full VM | Hypervisor snapshot restore |

After rollback, run health check and `pytest -q -m integration`.

## Escalation Principles

1. Preserve evidence (logs, `alembic current`, git SHA).
2. Prefer restore-over-debug for production data incidents.
3. Record incident outcome in `PROJECT_STATE.md` operational notes.
4. Open follow-up task for root cause fix—no silent one-off patches.

## Related Documents

- [OPERATIONAL_RUNBOOK.md](OPERATIONAL_RUNBOOK.md)
- [BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md)
- [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md)
