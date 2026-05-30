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
| Core registry tables | Operational |
| Alembic migrations | Head `fd6be8e34b7b` |
| Admin CRUD APIs | Operational (countries, tax_types, source_documents, source_versions) |
| Baseline API tests (TASK-001F) | Implemented; **merge acceptance requires VM verification** against running PostgreSQL |
| Documentation / runbook (TASK-001G) | This task |

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
| [PROJECT_STATE.md](PROJECT_STATE.md) | Canonical current state |
| [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) | Known gaps |
| [OPEN_DECISIONS.md](OPEN_DECISIONS.md) | Pending decisions |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [TASK_REGISTRY.md](TASK_REGISTRY.md) | Task tracking |
| [SOURCE_ATTACHMENT_WORKFLOW.md](SOURCE_ATTACHMENT_WORKFLOW.md) | Source file attachment lifecycle |
| [SOURCE_PROCESSING_WORKFLOW.md](SOURCE_PROCESSING_WORKFLOW.md) | Processing queue and job finalization |
| [WORKER_CONTRACT.md](WORKER_CONTRACT.md) | Worker processor contract and no-op harness |
| [EXTRACTION_CONTRACT.md](EXTRACTION_CONTRACT.md) | Source text extraction contract and extractors |
| [SEGMENTATION_CONTRACT.md](SEGMENTATION_CONTRACT.md) | Structural source segmentation contract and segmenters |
| [LEGAL_OBJECT_CONTRACT.md](LEGAL_OBJECT_CONTRACT.md) | Legal object extraction contract and extractors |
| [CITATION_ANCHOR_CONTRACT.md](CITATION_ANCHOR_CONTRACT.md) | Canonical citation anchor contract and generators |

## Governance

- No direct database schema changes outside Alembic.
- No unbounded AI-driven architecture changes.
- Implementation follows bounded tasks with explicit acceptance criteria.
