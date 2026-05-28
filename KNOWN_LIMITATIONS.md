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
- Source binary storage (`storage_path`) is referenced but ingestion/storage service is not part of current CRUD scope.

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
