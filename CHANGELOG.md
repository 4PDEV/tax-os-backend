# Changelog

All notable changes to `tax-os-backend` are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions align with git tags where applicable.

## [0.2.1-task-002b] - 2026-05-30

### Added

- TASK-002B: structural source segmentation contract. New `backend/app/services/segmentation/` package with:
  - `Segment` / `SegmentationResult` / `SegmentMetadata` / `SegmentationMetadata` strict Pydantic models (`extra="forbid"`).
  - `SegmentType` enum (`document`, `part`, `chapter`, `section`, `article`, `clause`, `subclause`, `paragraph`, `schedule`, `unknown`) and `SegmentationStatus` enum (`pending` / `success` / `failed` / `partial`).
  - `BaseSegmenter` interface (`can_handle`, `segment`) with mandatory `name` / `version`.
  - Fully implemented deterministic `GenericSegmenter` with offset tracking, structural typing, and parent/child hierarchy.
  - Skeleton `LegislativeSegmenter` raising `NotImplementedError`.
  - `SEGMENTATION_CONTRACT.md` documentation.
- No database persistence introduced (contract + segmentation behavior only).

## [0.2.0-task-002a] - 2026-05-30

### Added

- TASK-002A: source text extraction contract. New `backend/app/services/extraction/` package with:
  - `ExtractionResult` / `ExtractionMetadata` Pydantic models (`extra="forbid"`, non-interpretive).
  - `ExtractionStatus` enum restricted to `pending` / `success` / `failed` / `partial`.
  - `sha256_text` integrity hashing over raw extracted text.
  - `BaseExtractor` interface (`can_handle`, `extract`) with mandatory `name` / `version`.
  - Fully implemented `TxtExtractor` (faithful, deterministic; `PARTIAL` degrade on invalid UTF-8).
  - Skeleton `PdfExtractor` / `HtmlExtractor` raising `NotImplementedError`.
  - `EXTRACTION_CONTRACT.md` documentation.
- No database persistence introduced (contract + pipeline structure only).

## [0.2.3-task-002c] - 2026-05-30

### Added

- TASK-002C: legal object extraction contract. New `backend/app/services/legal_objects/` package with:
  - `LegalObjectCandidate` / `LegalObjectExtractionResult` / `LegalObjectMetadata` / `LegalObjectExtractionMetadata` strict Pydantic models (`extra="forbid"`).
  - `LegalObjectType` enum (structural only: `act`, `regulation`, `order`, `notice`, `judgment`, `treaty`, `part`, `chapter`, `section`, `article`, `clause`, `subclause`, `paragraph`, `schedule`, `definition`, `unknown`) and `ExtractionStatus` enum (`pending` / `success` / `failed` / `partial`).
  - `BaseLegalObjectExtractor` interface (`can_handle`, `extract`) with mandatory `name` / `version`.
  - Fully implemented deterministic `GenericLegalObjectExtractor` (segment→object surface mapping, preserving offsets, sequencing, and parent/child hierarchy).
  - Skeleton `LegislativeLegalObjectExtractor` raising `NotImplementedError`.
  - `LEGAL_OBJECT_CONTRACT.md` documentation.
- No database persistence, migrations, or registry storage introduced (contract + deterministic extraction only).

## [Unreleased]

### Added

- TASK-001L: `ingestion_status` on `source_versions`, governed transition service, `POST /source-versions/{id}/ingestion-status`, auto `queued` on upload, `superseded` on supersede.
- TASK-001M: `source_processing_jobs` table, queue service, internal enqueue/list/get/status APIs.
- TASK-001N: `POST /source-processing-jobs/claim-next`, lock metadata, concurrency-safe claim via `FOR UPDATE SKIP LOCKED`.
- TASK-001O: job complete/fail endpoints, `result_json`/`completed_by`/`failed_by`, ingestion status sync.
- TASK-001P: worker contract, `NoopProcessor`, `run_next_job_once` one-shot harness.

### Added (prior unreleased)

- TASK-001G: operational and governance documentation set (README, runbooks, workflows, project state).
- TASK-001F: pytest foundation, integration marker, skip guard, baseline API tests for registry CRUD and `source_versions` immutability.
- TASK-001H: storage abstraction, local filesystem backend, SHA-256 checksum utilities.
- TASK-001J: `POST /source-versions/{id}/upload` internal upload API.
- TASK-001K: attachment state helpers, `file_attached` / `attachment_status` on API responses, `SOURCE_ATTACHMENT_WORKFLOW.md`.

### Changed

- README consolidated and linked to documentation index.
- TASK-001I: `datetime.utcnow` replaced with timezone-aware `utc_now()`.
- Upload workflow enforces attachment state validation and rejects duplicate or inconsistent attachment.

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

## v0.1.2 — Storage Foundation

Added:
- storage abstraction layer
- local filesystem storage backend
- SHA-256 checksum utilities
- safe path normalization
- overwrite protection
- storage unit tests

Verified:
42 tests passing
0 skipped
