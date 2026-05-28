# Backup and Recovery

Data protection procedures for `tax-os-backend`. Legal source registry data requires recoverable backups and verified restore discipline.

## Scope

| Asset | Priority | Method |
|-------|----------|--------|
| PostgreSQL (`taxos` database) | Critical | `pg_dump` / `pg_restore` |
| Docker volumes (if used for Postgres data) | Critical | Volume backup or dump-based |
| Git repository | High | Remote push + optional archive |
| VM disk | High | Hypervisor snapshot |
| Uploaded source files (`storage_path` on versions) | Critical when populated | Filesystem backup of storage root |

Current phase: database and repository are primary recovery targets.

## PostgreSQL Backup

From VM host with Postgres reachable:

```bash
export BACKUP_DIR=/opt/tax-os/backups/postgres
mkdir -p "$BACKUP_DIR"
export STAMP=$(date +%Y%m%d_%H%M%S)

pg_dump -h localhost -p 5432 -U taxos -d taxos -Fc \
  -f "$BACKUP_DIR/taxos_${STAMP}.dump"
```

Plain SQL format (human-readable):

```bash
pg_dump -h localhost -p 5432 -U taxos -d taxos \
  -f "$BACKUP_DIR/taxos_${STAMP}.sql"
```

Via Docker exec (when client tools are only in container):

```bash
docker exec taxos-postgres pg_dump -U taxos -d taxos -Fc \
  > "$BACKUP_DIR/taxos_${STAMP}.dump"
```

Record backup metadata: timestamp, Alembic revision (`alembic current`), git commit hash.

## PostgreSQL Restore

**Warning:** restore overwrites target database content. Perform on a staging database first when possible.

### Custom format (`.dump`)

```bash
# Optional: drop and recreate database on staging
psql -h localhost -p 5432 -U taxos -d postgres -c "DROP DATABASE IF EXISTS taxos_restore;"
psql -h localhost -p 5432 -U taxos -d postgres -c "CREATE DATABASE taxos_restore;"

pg_restore -h localhost -p 5432 -U taxos -d taxos_restore --clean --if-exists \
  /opt/tax-os/backups/postgres/taxos_YYYYMMDD_HHMMSS.dump
```

### SQL format

```bash
psql -h localhost -p 5432 -U taxos -d taxos_restore -f /path/to/taxos_YYYYMMDD_HHMMSS.sql
```

## Docker Volume Considerations

If PostgreSQL data persists in a named volume:

1. Prefer **logical backup** (`pg_dump`) for portability across hosts.
2. Volume-level copy/snapshot is a secondary option when coordinated with Postgres shutdown or volume-consistent snapshot tooling.
3. Never rely on copying a live data directory without vendor-approved procedures.

Identify volume:

```bash
docker inspect taxos-postgres --format '{{ json .Mounts }}' | jq .
```

## Repository Backup

```bash
cd /opt/tax-os/repos/tax-os-backend
git status
git push origin <branch>
```

Optional tarball (excludes venv):

```bash
tar -czf /opt/tax-os/backups/repo/tax-os-backend_$(date +%Y%m%d).tar.gz \
  --exclude='.venv' --exclude='.pytest_cache' \
  -C /opt/tax-os/repos tax-os-backend
```

## VM Snapshot Recommendations

- Take hypervisor snapshots before major migrations or releases.
- Label snapshots with date, task ID, and Alembic revision.
- Snapshots complement—not replace—logical database dumps.

## Recovery Validation Steps

After any restore:

1. `pg_isready -h localhost -p 5432 -U taxos`
2. `psql ... -c "\dt"` — confirm core tables exist.
3. `alembic current` — revision matches expected release.
4. `curl http://localhost:8000/health`
5. Spot-check registry rows: `SELECT COUNT(*) FROM countries;`
6. Run `pytest -q` against `taxos_test` (or restored clone) with integration DB configured.

Document restore outcome and any data loss window.

## Recovery Order (Suggested)

1. Restore VM snapshot (if full environment loss).
2. Start `taxos-postgres` container.
3. Restore PostgreSQL from latest verified dump.
4. Checkout known-good git commit.
5. `pip install -r requirements.txt` in venv.
6. `alembic upgrade head` only if DB revision is behind application code.
7. Start API and run validation steps above.

## Prohibited Practices

- Restoring production dumps into shared dev DB without renaming/isolation.
- Deleting backups without retention policy approval.
- Assuming Docker volume copy alone is sufficient without `pg_dump` verification.
