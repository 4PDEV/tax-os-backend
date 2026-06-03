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
b5c3e9a04d47
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

### TASK-006K change detection engine skeleton tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_change_detection_engine_skeleton.py -q --tb=short
```

### TASK-006L source promotion workflow tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_source_promotion_workflow.py backend/tests/test_source_promotion_alembic_migration.py -q --tb=short
```

### TASK-006N extraction trigger persistence tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_extraction_trigger_persistence.py backend/tests/test_extraction_trigger_alembic_migration.py -q --tb=short
```

### TASK-006O extraction worker skeleton tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_extraction_worker_skeleton.py -q --tb=short
```

### TASK-006P controlled extraction execution tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_controlled_extraction_execution.py -q --tb=short
```

### TASK-006P1 extraction replay idempotency tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_extraction_replay_idempotency_hardening.py backend/tests/test_extraction_replay_idempotency_alembic_migration.py -q --tb=short
```

### TASK-006R parsing trigger persistence tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_parsing_trigger_persistence.py backend/tests/test_parsing_trigger_alembic_migration.py -q --tb=short
```

### TASK-006X controlled legal object promotion execution tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_controlled_legal_object_promotion_execution.py -q --tb=short
```

### TASK-006W legal object promotion worker skeleton tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_legal_object_promotion_worker_skeleton.py -q --tb=short
```

### TASK-006V legal object promotion persistence tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_legal_object_promotion_persistence.py backend/tests/test_legal_object_promotion_alembic_migration.py -q --tb=short
```

### TASK-006S parsing worker skeleton tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_parsing_worker_skeleton.py -q --tb=short
```

### TASK-006T controlled parsing execution tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_controlled_parsing_execution.py -q --tb=short
```

### TASK-006T1A parsed structure identity tests

```bash
TEST_DATABASE_URL='postgresql://taxos:P%405sw0rd%21234@localhost:5432/taxos_test' \
.venv/bin/pytest backend/tests/test_parsed_structure_identity_hardening.py backend/tests/test_parsed_structure_identity_alembic_migration.py -q --tb=short
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
