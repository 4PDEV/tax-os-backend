# Known Limitations

Explicit gaps in the current `tax-os-backend` phase. Not a backlog commitment order.

## Platform

- No authentication or authorization on admin APIs.
- No rate limiting or API gateway integration.
- No multi-tenant isolation.
- Single-VM development deployment; no production HA documented here.

## Data and Registry

- `source_versions` immutability enforced at API layer only; database does not block direct SQL updates.
- Soft delete sets `status` / `version_status` to inactive; records remain in database.
- `audit_log` and `source_retrieval_log` tables exist without automated write integration from CRUD routes.
- No full-text search or citation graph APIs.
- Cross-reference detection contract exists (TASK-002E) but references are not persisted, resolved to registry entities, or ranked by authority.
- Structural parser contract exists (TASK-002F) but structural units are not persisted; relationship to segmentation/legal-object layers not yet unified.
- TASK-003A–003C schema/ORM/migration materialize legal object tables. TASK-003D adds controlled repository write path from `ConvergedLegalObjectCandidate` — **no CRUD APIs or ingestion wiring yet**. **`legal_object_lineage` and `legal_object_duplicates` writes deferred** (duplicate detection only; no auto-merge or lineage persistence).
- Source binary storage (`storage_path`) is referenced but ingestion/storage service is not part of current CRUD scope.

## Legal Memory and Citation (TASK-004A–004C)

- TASK-004A retrieval and TASK-004B effective-date resolver are merged; integrity verified on read.
- TASK-004C citation candidates are in-memory DTOs only — not persisted, not formatted citations.
- `authority_level` on candidates is descriptive metadata only; not used for sorting, scoring, or weighting.

### TASK-004C → TASK-004D forward-governance (reviewer notes, non-blocking)

- **`ready` without `effective_on`:** When `effective_on` is absent, `CitationCandidateBuilder` uses retrieval only and may mark candidates `ready` on integrity + traceability alone. This does **not** assert the object is effective on any calendar date. TASK-004D must not treat `ready` without a resolution path as “effective today.”
- **`_resolve_version_id` ordering:** Version lookup uses `.first()` keyed on `(legal_object_id, text_hash)` without explicit SQL ordering. Content is deterministic when `text_hash` matches; `legal_object_version_id` could differ only if duplicate rows exist. Confirm uniqueness at schema layer or add explicit ordering if duplicates are possible.
- **Zero-UUID sentinel:** On traceability failure, `legal_object_version_id` may be `UUID(int=0)`. Consumers must gate on `candidate_status` before trusting version IDs.
- **Unmapped `ResolutionStatus`:** New 004B statuses not in `_RESOLUTION_TO_CANDIDATE_STATUS` raise `KeyError` (fail-loud). Extending 004B requires extending the map — intentional, not a defect.

## Operations

- Docker Compose may live outside this repository; container names must be confirmed per host.
- No centralized logging or metrics stack.
- No CI/CD pipeline in repository.
- Integration tests require explicit `TEST_POSTGRES_*` configuration.

## Testing

- All current API tests are integration-marked and require PostgreSQL.
- No dedicated unit-test layer separate from DB yet.
- Skipped integration tests in CI-less sandbox environments do not validate API behavior.

## Jurisdiction and Content

- Rwanda-first focus is architectural intent; registry content population is not automated in this repo phase.

## Documentation

- Cloud production orchestration (Kubernetes, managed RDS) is out of scope for current docs.

Update this file when limitations are resolved or new ones are discovered.
