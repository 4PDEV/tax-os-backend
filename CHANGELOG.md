# Changelog

All notable changes to `tax-os-backend` are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions align with git tags where applicable.

## [Unreleased]

### Added

- TASK-001G: operational and governance documentation set (README, runbooks, workflows, project state).
- TASK-001F: pytest foundation, integration marker, skip guard, baseline API tests for registry CRUD and `source_versions` immutability.

### Changed

- README consolidated and linked to documentation index.

### Pending

- TASK-001F: final merge acceptance pending VM integration test execution (`pytest -q` with reachable test DB).

## [0.1.1-crud-foundation] - 2026-05-27

### Added

- Internal admin CRUD APIs: `countries`, `tax-types`, `source-documents`, `source-versions`.
- Pydantic schemas and SQLAlchemy models for source registry entities.
- `source_versions` governance: create/list/retrieve only; PUT/DELETE return 405.

## [0.1.0] - 2026-05-27 (foundation)

### Added

- FastAPI application skeleton and health endpoint.
- PostgreSQL models and Alembic migration `fd6be8e34b7b` (source registry tables).
- Alembic migration infrastructure and discipline.
