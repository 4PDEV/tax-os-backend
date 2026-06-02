# Testing Guide

Operational test discipline for deterministic, isolated, migration-safe execution.

## 1) Safety rules (must follow)

1. Integration tests require `TEST_DATABASE_URL`.
2. `TEST_DATABASE_URL` must point to a dedicated test DB (`test` in DB name, or `_ci` suffix).
3. Do not run destructive migration tests against development or production databases.
4. Keep `REQUIRE_TEST_DATABASE_URL=1` (default) unless explicitly debugging local-only non-destructive behavior.

## 2) Required environment

Example:

```bash
export TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test'
```

Optional override (not recommended for normal governance runs):

```bash
export REQUIRE_TEST_DATABASE_URL=0
```

## 3) Migration expectations

Expected Alembic head:

```text
f4c3b2a190de
```

Session fixture behavior (`backend/tests/conftest.py`):

- Session-scoped migrate: downgrade base → upgrade head
- Per-test DB session: outer transaction + nested savepoint
- Service-level rollbacks are isolated from test setup state

## 4) Commands

### Full backend suite

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest -q --tb=line
```

### Ingestion-only

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_ingestion_hashing.py backend/tests/test_ingestion_alembic_migration.py backend/tests/test_ingestion_persistence.py -q --tb=short
```

### Legal-object integrity + retrieval focus

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_legal_object_persistence_integrity.py backend/tests/test_retrieval_service.py -q --tb=short
```

### TASK-006H controlled fetch tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_fetch_controlled_local_dry_run.py -q --tb=short
```

### TASK-006I fetch persistence tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_fetch_persistence.py backend/tests/test_fetch_alembic_migration.py -q --tb=short
```

### TASK-006J change detection persistence tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_change_detection_persistence.py backend/tests/test_change_detection_alembic_migration.py -q --tb=short
```

## 5) Prohibited practices

- Running integration tests without an explicit `TEST_DATABASE_URL`
- Pointing test URL at non-test DBs
- Assuming test order for correctness
- Relying on manual cleanup between tests
- Changing migration state outside Alembic in tests

## 6) TASK-006B stability record

- TEST-GAP-001 reproduced from 006A validation context.
- Root causes isolated:
  - rollback scope contamination in integrity rejection paths,
  - stale legal-object migration downgrade assertion,
  - non-canonical effective-date resolver ordering key.
- Validation:
  - Ingestion suite: 12 passed
  - Integrity + retrieval focus: 27 passed
  - Full suite: 390 passed × 3 consecutive runs
