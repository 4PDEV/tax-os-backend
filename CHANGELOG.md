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

## [0.2.4-task-002d] - 2026-05-30

### Added

- TASK-002D: canonical citation anchor contract. New `backend/app/services/citation_anchors/` package with:
  - `CanonicalCitationAnchor` / `CitationAnchorGenerationResult` / `CitationAnchorMetadata` / `CitationAnchorGenerationMetadata` strict Pydantic models (`extra="forbid"`).
  - `CitationAnchorType` enum (structural only) and `GenerationStatus` enum (`pending` / `success` / `failed` / `partial`).
  - `BaseCitationAnchorGenerator` interface (`can_handle`, `generate`) with mandatory `name` / `version`.
  - Fully implemented deterministic `GenericCitationAnchorGenerator`: structure-based canonical anchors (`<TYPE>:<normalized>` joined by `/` along ancestor lineage), SHA-256 `citation_anchor_id` over `source_version_id|legal_object_id|canonical_anchor|start_offset|end_offset`, deterministic `display_label`, and missing-parent fallback with observational warnings.
  - Skeleton `LegislativeCitationAnchorGenerator` raising `NotImplementedError`.
  - `CITATION_ANCHOR_CONTRACT.md` documentation.
- Anchors derive only from stable structural inputs (no DB IDs, UUID randomness, timestamps, AI, or raw-text hashing as primary anchor).
- No database persistence, migrations, or registry storage introduced (contract + deterministic generation only).

## [task-002e-complete] - 2026-05-30

### Added

- TASK-002E: cross-reference detection contract. New `backend/app/services/cross_reference/` package with:
  - `CrossReferenceResult` strict Pydantic model (`extra="forbid"`) with `source_version_id`, `source_location`, `reference_text`, `reference_type`, `target_candidate`, `confidence`, `detected_at`, `detector_version`.
  - `ReferenceType` enum (`section`, `article`, `regulation`, `schedule`, `part`, `chapter`, `act`, `law`, `guidance`, `case`, `treaty`, `unknown`) and deterministic `ReferenceConfidence` (`high`, `medium`, `low`).
  - `CrossReferenceDetector` with regex-based `detect()` — Section/Article/Regulation/Schedule/Part/Chapter patterns, range patterns (medium confidence), vague phrase patterns (low confidence), and surface `target_candidate` extraction from ``of the X Act`` phrases.
  - `CROSS_REFERENCE_CONTRACT.md` documentation.
- No database persistence, graph storage, or interpretation layer introduced (identify/record/link only).

## [task-002f-complete] - 2026-05-30

### Added

- TASK-002F: structural section parser contract. New `backend/app/services/structure_parser/` package with:
  - `StructuralUnit` strict Pydantic model (`extra="forbid"`) with hierarchy, offsets, heading fields, and `parser_version`.
  - `StructuralUnitType` enum (`act`, `law`, `title`, `part`, `chapter`, `section`, `article`, `regulation`, `schedule`, `paragraph`, `subparagraph`, `unknown`).
  - `StructuralParser.parse()` — regex-based line-start detection (Roman/Arabic numerals, lettered schedules), deterministic parent/child hierarchy, heading label/title split, offset and raw-text preservation.
  - `STRUCTURE_PARSER_CONTRACT.md` documentation.
- No database persistence or semantic interpretation introduced (document structure detection only).

## [task-002g-complete] - 2026-05-30

### Added

- TASK-002G: structural legal object extraction contract (proto-legal intelligence boundary). New `backend/app/services/legal_object_extraction/` package with:
  - `LegalObjectCandidate` strict Pydantic model (`extra="forbid"`) with `source_version_id`, deterministic `legal_object_id`, `canonical_path`, `parent_legal_object_id`, `structural_unit_id`, offsets, `raw_text`, SHA-256 `text_hash`, and extraction metadata.
  - `LegalObjectType` enum (`act`, `law`, `title`, `part`, `chapter`, `section`, `article`, `regulation`, `schedule`, `paragraph`, `subparagraph`, `definition`, `unknown`) and `LegalObjectExtractionStatus` enum (`success`, `partial`, `failed`, `unknown`).
  - `LegalObjectExtractor.extract()` — one candidate per `StructuralUnit`, deterministic type mapping, canonical path from structural lineage (` > ` separator), SHA-256 identity (`lo_<32-hex>`), parent resolution via prior candidates, `PARTIAL` on missing structural parent.
  - `LEGAL_OBJECT_EXTRACTION_CONTRACT.md` documentation.
- Consumes `StructuralUnit` from `structure_parser` only; no interpretation, persistence, or AI.
- Merged to main — tag `task-002g-merged`.

## [task-002h-complete] - 2026-05-30

### Added

- TASK-002H: legal object candidate convergence contract (OD-010 contract-level resolution). New `backend/app/services/legal_object_convergence/` package with:
  - `ConvergedLegalObjectCandidate` strict Pydantic model wrapping canonical `legal_object_extraction.models.LegalObjectCandidate`.
  - `ConvergenceSource` enum (`structural_unit`, `segment`, `legacy`, `unknown`) and `ConvergenceStatus` enum (`canonical`, `mapped`, `partial`, `rejected`).
  - `LegalObjectCandidateMapper` — structural pass-through as `CANONICAL`; segment/legacy mapping with canonical identity regeneration via `generate_legal_object_id`; explicit `REJECTED` for unmappable inputs.
  - `LegalObjectCandidateValidator` — required-field, text-hash, identity, offset, and duplicate-ID checks.
  - `LEGAL_OBJECT_CONVERGENCE_CONTRACT.md` documentation.
- Establishes persistence gate: all future legal object candidates must converge to one canonical shape before persistence planning.
- No database persistence, migrations, or CRUD introduced.
- Merged to main — tag `task-002h-merged`.

## [task-002i-complete] - 2026-05-30

### Added

- TASK-002I: legal object persistence planning contract (architecture governance only). New `backend/app/services/legal_object_persistence_planning/` package with:
  - `PlannedLegalObjectPersistenceModel` — Pydantic planning model (`extra="forbid"`); no DB bindings.
  - `contract.py` — canonical input rule: only `ConvergedLegalObjectCandidate`; blocked direct sources documented.
  - `rules.py` — explicit NEVER / ALWAYS persistence rules.
  - `duplicate_strategy.py`, `lineage_strategy.py`, `migration_plan.py`, `risks.py` — planning-only strategies, phased migration sequence, risk register, blocked assumptions.
  - `LEGAL_OBJECT_PERSISTENCE_PLANNING_CONTRACT.md` documentation.
- Establishes persistence governance boundary; **no tables, migrations, repositories, or CRUD**.
- Persistence implementation may not proceed until planning contract is architecturally approved.
- Merged to main — tag `task-002i-merged`.

## [task-003a-complete] - 2026-05-30

### Added

- TASK-003A: canonical legal object persistence schema contract (planning only). New `backend/app/services/legal_object_schema_contract/` package with:
  - Proposed table contracts: `legal_objects`, `legal_object_versions`, `legal_object_lineage`, `legal_object_duplicates`.
  - `schema_definition.py` — field-level Pydantic contract definitions (`extra="forbid"`).
  - `constraints.py`, `indexes.py`, `immutability.py`, `lineage.py` — intended DB constraints, indexes, immutability rules, lineage and duplicate assumptions, migration expectations.
  - `LEGAL_OBJECT_SCHEMA_CONTRACT.md` documentation.
- Input remains `ConvergedLegalObjectCandidate` only; **no SQLAlchemy, Alembic, repositories, or CRUD**.
- Merged to main — tag `task-003a-merged`.

## [task-003b-complete] - 2026-05-30

### Added

- TASK-003B: canonical legal object SQLAlchemy ORM models (definitions only). New `backend/app/models/` files:
  - `LegalObject`, `LegalObjectVersion`, `LegalObjectLineage`, `LegalObjectDuplicate`
  - Aligned with TASK-003A schema contract; `legal_object_id` externally supplied (no random PK default)
  - Models registered in `backend/app/models/__init__.py` for future Alembic discovery
- **No Alembic migrations**, repositories, CRUD APIs, or persistence services introduced.
- Merged to main — tag `task-003b-merged`.

## [task-003c-complete] - 2026-05-30

### Added

- TASK-003C: canonical legal object Alembic migration (`f7c2d9e41a83`). Creates PostgreSQL tables:
  - `legal_objects`, `legal_object_versions`, `legal_object_lineage`, `legal_object_duplicates`
  - Indexes per TASK-003A schema contract; `ck_legal_object_versions_offsets` check constraint
  - Circular FK (`current_version_id`) resolved via deferred FK after versions table creation
  - Downgrade drops tables in reverse dependency order
  - Legal object models imported in `backend/migrations/env.py`
  - `backend/tests/test_legal_object_alembic_migration.py` — migration structure and integration verification
- **No repositories, CRUD APIs, persistence services, or ingestion wiring.**
- Merged to main — tag `task-003c-merged`.

## [task-003d-complete] - 2026-05-30

### Added

- TASK-003D: legal object persistence repository contract. New `backend/app/services/legal_object_persistence/` package with:
  - `LegalObjectPersistenceService.persist()` — controlled write path from `ConvergedLegalObjectCandidate` only
  - `LegalObjectPersistenceRepository` — SQLAlchemy session pattern; creates `legal_objects` and `legal_object_versions` rows
  - `LegalObjectPersistenceResult` and `PersistenceStatus` enum (`created`, `version_created`, `duplicate_detected`, `rejected`, `failed`)
  - Duplicate detection by `legal_object_id` + `text_hash`; no auto-merge; immutable version fields preserved
  - `current_version_id` updated only after new version creation
  - `LEGAL_OBJECT_PERSISTENCE_REPOSITORY_CONTRACT.md` documentation
- **No CRUD APIs, ingestion wiring, batch jobs, or UI.**

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
