# TAX-OS Backend

Backend for the **Source-Referenced Business & Tax Research Platform**.

## Purpose

This repository provides deterministic backend infrastructure for:

- legal source registry
- immutable source versioning
- effective-date-aware source metadata
- audit logging foundation
- internal admin CRUD APIs for registry entities

The platform is built for operational auditability and source-backed research—not probabilistic outputs.

## Architecture Philosophy

- **Deterministic-first** — behavior is explicit and reproducible.
- **Source-referenced** — conclusions trace to versioned legal sources.
- **Immutable historical versions** — `source_versions` are append-only at the API layer.
- **Effective-date-aware** — temporal fields are first-class on versions.
- **Auditability** — changes must be traceable over time.
- **Bounded execution** — tasks implement only approved scope.

Architecture governance lives in the separate `tax-os-architecture` repository. This repo implements approved tasks only.

## Technology Stack

| Component | Version / tool |
|-----------|----------------|
| Python | 3.14+ (project venv) |
| FastAPI | 0.136.x |
| SQLAlchemy | 2.x |
| Alembic | 1.18.x |
| PostgreSQL | 16 |
| Pytest | 9.x |
| Docker | PostgreSQL / pgAdmin on VM |

## Repository Structure

```
tax-os-backend/
  alembic.ini
  requirements.txt
  pytest.ini
  backend/
    .env                 # local credentials (not committed)
    app/
      api/routes/        # countries, tax-types, source-documents, source-versions
      core/              # settings
      db/                # session, dependencies
      models/
      schemas/
    migrations/
      versions/          # Alembic revisions
    tests/               # baseline API tests (integration marker)
```

## Current Development Status

| Area | Status |
|------|--------|
| Platform phase | Legal memory + temporal governance + ingestion persistence (see [CURRENT_STATUS.md](CURRENT_STATUS.md)) |
| Alembic migrations | Head `c9a2f3b81d06` |
| Approved next task | **Awaiting next bounded task after TASK-006H** (local/dry-run fetch implementation complete; no live acquisition) |
| Admin CRUD APIs | Operational |
| Legal object / citation contracts | Merged on `main` (003A–004D) |
| Temporal governance | Merged (005A–005C); tag `checkpoint-task-005a-spec` |
| Ingestion artifact persistence | TASK-006A on `main` |

Initial jurisdiction focus: **Rwanda**. Initial tax domains: VAT, PAYE/PIT, WHT, corporate tax, capital gains, customs & excise (registry phase only).

## Setup Summary

1. Clone repository to VM (e.g. `/opt/tax-os/repos/tax-os-backend`).
2. Create Python venv and install dependencies — see [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md).
3. Configure `backend/.env` and start PostgreSQL (Docker) — see [OPERATIONAL_RUNBOOK.md](OPERATIONAL_RUNBOOK.md).
4. Run migrations: `alembic upgrade head` from repository root.
5. Start API: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000`.
6. Run tests with `TEST_POSTGRES_*` set — see [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md).

## Documentation Index

| Document | Purpose |
|----------|---------|
| [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) | Developer bootstrap |
| [OPERATIONAL_RUNBOOK.md](OPERATIONAL_RUNBOOK.md) | Day-to-day operations |
| [BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md) | Backup and restore |
| [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md) | Alembic discipline |
| [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) | AI-assisted dev governance |
| [TASK_EXECUTION_STANDARD.md](TASK_EXECUTION_STANDARD.md) | Task implementation rules |
| [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md) | Failure handling |
| [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) | Release discipline |
| [CURRENT_STATUS.md](CURRENT_STATUS.md) | **Canonical** high-level platform status (onboarding) |
| [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) | Authoritative task sequencing (COMPLETE / NEXT / DEFERRED) |
| [ARCHITECTURE_PHASE_MAP.md](ARCHITECTURE_PHASE_MAP.md) | Architecture phase evolution map |
| [PROJECT_STATE.md](PROJECT_STATE.md) | Detailed milestone history |
| [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) | Known gaps |
| [OPEN_DECISIONS.md](OPEN_DECISIONS.md) | Pending decisions |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | Test DB safety + deterministic suite commands |
- [TASK_REGISTRY.md](TASK_REGISTRY.md) | Task tracking |
| [TASKS/](TASKS/) | **Authoritative task specs (required for review)** |
| [SOURCE_ATTACHMENT_WORKFLOW.md](SOURCE_ATTACHMENT_WORKFLOW.md) | Source file attachment lifecycle |
| [SOURCE_PROCESSING_WORKFLOW.md](SOURCE_PROCESSING_WORKFLOW.md) | Processing queue and job finalization |
| [WORKER_CONTRACT.md](WORKER_CONTRACT.md) | Worker processor contract and no-op harness |
| [EXTRACTION_CONTRACT.md](EXTRACTION_CONTRACT.md) | Source text extraction contract and extractors |
| [SEGMENTATION_CONTRACT.md](SEGMENTATION_CONTRACT.md) | Structural source segmentation contract and segmenters |
| [LEGAL_OBJECT_CONTRACT.md](LEGAL_OBJECT_CONTRACT.md) | Legal object extraction contract and extractors |
| [CITATION_ANCHOR_CONTRACT.md](CITATION_ANCHOR_CONTRACT.md) | Canonical citation anchor contract and generators |
| [CROSS_REFERENCE_CONTRACT.md](CROSS_REFERENCE_CONTRACT.md) | Cross-reference detection contract and detector |
| [STRUCTURE_PARSER_CONTRACT.md](STRUCTURE_PARSER_CONTRACT.md) | Structural section parser contract and parser |
| [LEGAL_OBJECT_EXTRACTION_CONTRACT.md](backend/app/services/legal_object_extraction/LEGAL_OBJECT_EXTRACTION_CONTRACT.md) | Structural legal object extraction contract (structural units → candidates) |
| [LEGAL_OBJECT_CONVERGENCE_CONTRACT.md](backend/app/services/legal_object_convergence/LEGAL_OBJECT_CONVERGENCE_CONTRACT.md) | Legal object candidate convergence contract (OD-010; canonical shape enforcement) |
| [LEGAL_OBJECT_PERSISTENCE_PLANNING_CONTRACT.md](backend/app/services/legal_object_persistence_planning/LEGAL_OBJECT_PERSISTENCE_PLANNING_CONTRACT.md) | Legal object persistence planning contract (governance only; no implementation) |
| [LEGAL_OBJECT_SCHEMA_CONTRACT.md](backend/app/services/legal_object_schema_contract/LEGAL_OBJECT_SCHEMA_CONTRACT.md) | Canonical legal object persistence schema contract (planning only; no DB code) |
| [LEGAL_OBJECT_PERSISTENCE_REPOSITORY_CONTRACT.md](backend/app/services/legal_object_persistence/LEGAL_OBJECT_PERSISTENCE_REPOSITORY_CONTRACT.md) | Legal object persistence repository contract (controlled write path) |
| [LEGAL_OBJECT_PERSISTENCE_INTEGRITY_CONTRACT.md](backend/app/services/legal_object_persistence/LEGAL_OBJECT_PERSISTENCE_INTEGRITY_CONTRACT.md) | Legal object persistence integrity & immutability enforcement (TASK-003E) |
| [LEGAL_OBJECT_RETRIEVAL_CONTRACT.md](backend/app/services/retrieval/LEGAL_OBJECT_RETRIEVAL_CONTRACT.md) | Legal object retrieval contract — deterministic retrieval (TASK-004A) |
| [EFFECTIVE_DATE_RESOLVER_CONTRACT.md](backend/app/services/effective_date/EFFECTIVE_DATE_RESOLVER_CONTRACT.md) | Effective-date resolver contract — time-aware version resolution (TASK-004B) |
| [CITATION_CANDIDATE_CONTRACT.md](backend/app/services/citation_candidate/CITATION_CANDIDATE_CONTRACT.md) | Citation candidate contract — citation-ready DTO preparation (TASK-004C) |
| [CITATION_ASSEMBLY_CONTRACT.md](backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md) | Citation assembly contract — deterministic source-backed citations (TASK-004D) |
| [TEMPORAL_VERSIONING_ARCHITECTURE.md](TEMPORAL_VERSIONING_ARCHITECTURE.md) | Temporal & versioning architecture — authoritative time/version spec (TASK-005A-SPEC) |
| [SOURCE_MONITORING_AGENT_CONTRACT.md](SOURCE_MONITORING_AGENT_CONTRACT.md) | Monitoring-agent governance contract (TASK-006C; contract-only) |
| [TASKS/TASK-006C-SOURCE-MONITORING-AGENT-CONTRACT.md](TASKS/TASK-006C-SOURCE-MONITORING-AGENT-CONTRACT.md) | TASK-006C contract record |
| [CONTROLLED_SOURCE_FETCH_CONTRACT.md](CONTROLLED_SOURCE_FETCH_CONTRACT.md) | Controlled fetch governance contract (TASK-006F; contract-only) |
| [TASKS/TASK-006F-CONTROLLED-SOURCE-FETCH-CONTRACT.md](TASKS/TASK-006F-CONTROLLED-SOURCE-FETCH-CONTRACT.md) | TASK-006F contract record |
| [SOURCE_CHANGE_DETECTION_ENGINE_CONTRACT.md](SOURCE_CHANGE_DETECTION_ENGINE_CONTRACT.md) | Source change-detection governance contract (TASK-006G; contract-only) |
| [TASKS/TASK-006G-SOURCE-CHANGE-DETECTION-ENGINE-CONTRACT.md](TASKS/TASK-006G-SOURCE-CHANGE-DETECTION-ENGINE-CONTRACT.md) | TASK-006G contract record |
| `backend/app/services/fetch/` | TASK-006H controlled fetch implementation (dry-run + local fixture mode only) |

## Governance

- No direct database schema changes outside Alembic.
- No unbounded AI-driven architecture changes.
- Implementation follows bounded tasks with explicit acceptance criteria.
