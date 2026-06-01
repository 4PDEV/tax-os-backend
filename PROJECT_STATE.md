# PROJECT_STATE.md

## PROJECT

Source-Referenced Business & Tax Research Platform

---

# CURRENT PLATFORM STATUS

## STATUS

FOUNDATION PHASE ACTIVE

The platform has successfully established the initial deterministic backend foundation required for:

* source registry
* versioned legal source storage
* migration governance
* CRUD administration APIs
* deterministic storage abstraction
* checksum verification
* operational governance
* documentation discipline
* testing discipline

The platform is currently operating as:

* development environment
* internal staging environment

No public production deployment exists yet.

---

# CURRENT ARCHITECTURE STATUS

## BACKEND FOUNDATION

STATUS: VERIFIED

Implemented:

* FastAPI runtime foundation
* SQLAlchemy integration
* Alembic migration governance
* PostgreSQL integration
* deterministic configuration loading
* environment-based configuration
* Dockerized infrastructure foundation

---

## DATABASE FOUNDATION

STATUS: VERIFIED

Implemented:

* countries
* tax_types
* source_documents
* source_versions
* audit_log
* source_retrieval_log

Migration governance established.

Rules enforced:

* no direct DB modification
* version-controlled migrations only
* downgrade verification required
* rebuild verification required

---

## API FOUNDATION

STATUS: VERIFIED

Implemented:

* CRUD APIs
* internal admin routes
* validation schemas
* soft-delete behavior
* immutable source version enforcement
* Swagger/OpenAPI support

No authentication implemented yet.

---

## STORAGE FOUNDATION

STATUS: VERIFIED

Implemented:

* deterministic storage abstraction
* local filesystem backend
* SHA-256 checksum utilities
* path traversal protection
* overwrite protection
* storage metadata handling
* isolated storage tests

Current storage backend:

* local filesystem only

Deferred:

* AWS S3
* Azure Blob
* MinIO

Tag:
v0.1.2-storage-foundation

---

## INGESTION / PROCESSING FOUNDATION

STATUS: VERIFIED

Implemented:

* source upload internal API (`POST /source-versions/{id}/upload`)
* source attachment workflow + state (`file_attached`, `attachment_status`)
* governed `ingestion_status` state machine
* `source_processing_jobs` queue table + service
* enqueue / list / get / status-transition APIs
* claim/lock API (`claim-next`, `FOR UPDATE SKIP LOCKED`)
* result/completion APIs (`/complete`, `/fail`, ingestion sync)
* worker contract + `NoopProcessor` + `run_next_job_once` one-shot harness

No autonomous background daemon. No parsing/OCR/AI.

---

## EXTRACTION FOUNDATION

STATUS: VERIFIED (no DB persistence)

Implemented (TASK-002A):

* deterministic source text extraction contract (`backend/app/services/extraction/`)
* `ExtractionResult` / `ExtractionMetadata` Pydantic models (non-interpretive)
* `ExtractionStatus` enum (`pending` / `success` / `failed` / `partial`)
* SHA-256 text hashing for integrity / reproducibility
* `BaseExtractor` interface with mandatory `name` / `version`
* fully implemented `TxtExtractor` (faithful, deterministic)
* skeleton `PdfExtractor` / `HtmlExtractor` (raise `NotImplementedError`)

Strictly: SOURCE FILE → RAW EXTRACTED TEXT. No interpretation, summarization,
or legal parsing. Extracted text is not persisted to the database yet.

Tag:
v0.2.0-task-002a

---

## SEGMENTATION FOUNDATION

STATUS: VERIFIED (no DB persistence)

Implemented (TASK-002B):

* deterministic structural segmentation contract (`backend/app/services/segmentation/`)
* `Segment` / `SegmentationResult` Pydantic models (strict, non-interpretive)
* `SegmentType` (structural labels only) and `SegmentationStatus` enums
* `BaseSegmenter` interface with mandatory `name` / `version`
* fully implemented deterministic `GenericSegmenter` (offset tracking + parent/child hierarchy)
* skeleton `LegislativeSegmenter` (raises `NotImplementedError`)

Strictly: RAW EXTRACTED TEXT → STRUCTURED TEXT SEGMENTS. No interpretation,
summarization, or legal inference. Every segment preserves exact source offsets
(`raw_text == source[start:end]`). Segments are not persisted to the database yet.

Tag:
v0.2.1-task-002b

---

## LEGAL OBJECT FOUNDATION

STATUS: VERIFIED (no DB persistence)

Implemented (TASK-002C):

* deterministic legal object extraction contract (`backend/app/services/legal_objects/`)
* `LegalObjectCandidate` / `LegalObjectExtractionResult` Pydantic models (strict, non-interpretive)
* `LegalObjectType` (canonical structural labels only) and `ExtractionStatus` enums
* `BaseLegalObjectExtractor` interface with mandatory `name` / `version`
* fully implemented deterministic `GenericLegalObjectExtractor` (segment→object surface mapping)
* skeleton `LegislativeLegalObjectExtractor` (raises `NotImplementedError`)

Strictly: STRUCTURED TEXT SEGMENTS → CANONICAL LEGAL OBJECT CANDIDATES. No legal
interpretation, summarization, topic classification, authority ranking, or
legal-effect determination. Each candidate is segment-backed and preserves
`source_segment_id`, `raw_text`, offsets, sequencing, and hierarchy. Legal
objects are not persisted to the database yet.

Tag:
v0.2.3-task-002c

---

## CITATION ANCHOR FOUNDATION

STATUS: VERIFIED (no DB persistence)

Implemented (TASK-002D):

* deterministic canonical citation anchor contract (`backend/app/services/citation_anchors/`)
* `CanonicalCitationAnchor` / `CitationAnchorGenerationResult` Pydantic models (strict, non-interpretive)
* `CitationAnchorType` (structural labels only) and `GenerationStatus` enums
* `BaseCitationAnchorGenerator` interface with mandatory `name` / `version`
* fully implemented deterministic `GenericCitationAnchorGenerator` (structure-based anchors, ancestor lineage, SHA-256 identity, missing-parent degradation)
* skeleton `LegislativeCitationAnchorGenerator` (raises `NotImplementedError`)

Strictly: LEGAL OBJECT CANDIDATES → CANONICAL CITATION ANCHORS. Anchors derive
only from stable structural inputs (no DB IDs, UUID randomness, timestamps, AI,
or raw-text hashing as primary anchor). Full traceability chain preserved
(`source_version_id`, `legal_object_id`, `source_segment_id`, `raw_text`,
offsets). Anchors are not persisted to the database yet.

Tag:
v0.2.4-task-002d

This completes the governed deterministic lineage chain:
Source File → Extracted Text → Structural Segments → Legal Object Candidates →
Canonical Citation Anchors.

---

## CROSS-REFERENCE DETECTION FOUNDATION

STATUS: VERIFIED (no DB persistence)

Implemented (TASK-002E):

* deterministic cross-reference detection contract (`backend/app/services/cross_reference/`)
* `CrossReferenceResult` Pydantic model (strict, non-interpretive)
* `ReferenceType` and deterministic `ReferenceConfidence` enums
* `CrossReferenceDetector` with regex-only `detect()` (Section/Article/Regulation/Schedule/Part/Chapter + ranges + vague phrases)
* surface `target_candidate` extraction from ``of the X Act`` phrases (no resolution)

Strictly: identify, record, link — NOT interpret, prioritize, or reason. Every
result requires `source_version_id`. Cross-references are not persisted and are
not resolved to registry entities yet.

Tags:
task-002e-complete, task-002e-merged (on main)

---

## STRUCTURAL PARSER FOUNDATION

STATUS: VERIFIED (no DB persistence; merged to main)

Implemented (TASK-002F):

* deterministic structural section parser contract (`backend/app/services/structure_parser/`)
* `StructuralUnit` Pydantic model (strict, non-interpretive)
* `StructuralUnitType` enum and line-start regex heading detection
* `StructuralParser.parse()` with deterministic hierarchy assignment, heading label/title extraction, offset and raw-text preservation

Strictly: Extracted Text → Structural Units. Document structure detection only —
NOT legal meaning extraction. Structural units are not persisted yet.

Tags:
task-002f-complete, task-002f-merged (on main)

---

## STRUCTURAL LEGAL OBJECT EXTRACTION FOUNDATION

STATUS: VERIFIED (no DB persistence; merged to main)

Implemented (TASK-002G):

* deterministic structural legal object extraction contract (`backend/app/services/legal_object_extraction/`)
* `LegalObjectCandidate` Pydantic model (strict, non-interpretive) with deterministic `legal_object_id`, `canonical_path`, `parent_legal_object_id`, `structural_unit_id`, offsets, `raw_text`, SHA-256 `text_hash`
* `LegalObjectType` and `LegalObjectExtractionStatus` enums
* `LegalObjectExtractor.extract()` — one candidate per `StructuralUnit`, structural lineage paths, parent resolution, `PARTIAL` on missing structural parent

Strictly: Structural Units → Legal Object Candidates. First proto-legal-intelligence
boundary. No legal interpretation, topic classification, authority ranking,
conflict resolution, citation generation, or persistence.

Tags:
task-002g-complete, task-002g-merged (on main)

---

## LEGAL OBJECT CONVERGENCE FOUNDATION

STATUS: VERIFIED (no DB persistence; merged to main)

Implemented (TASK-002H):

* legal object candidate convergence contract (`backend/app/services/legal_object_convergence/`)
* `ConvergedLegalObjectCandidate` wrapping canonical `legal_object_extraction.models.LegalObjectCandidate`
* `ConvergenceSource` and `ConvergenceStatus` enums
* `LegalObjectCandidateMapper` — structural pass-through (`CANONICAL`), segment mapping (`MAPPED`/`PARTIAL`), explicit `REJECTED`
* `LegalObjectCandidateValidator` — identity, hash, offset, and duplicate-ID checks
* canonical identity centralized on `generate_legal_object_id`

Resolves **OD-010 at contract level**. Two upstream pipelines may coexist; all
candidates must converge before persistence planning. Segment path (`legal_objects/`)
is legacy for identity purposes.

Tags:
task-002h-complete, task-002h-merged (on main)

---

## LEGAL OBJECT PERSISTENCE PLANNING

STATUS: VERIFIED (planning only; merged to main)

Implemented (TASK-002I):

* legal object persistence planning contract (`backend/app/services/legal_object_persistence_planning/`)
* `PlannedLegalObjectPersistenceModel` — Pydantic planning model only; no DB bindings
* canonical persistence input rule — only `ConvergedLegalObjectCandidate`
* `rules.py` — NEVER / ALWAYS persistence rules
* `duplicate_strategy.py`, `lineage_strategy.py`, `migration_plan.py`, `risks.py`
* phased migration sequence (tables → lineage → effective dates → citation anchors)

Strictly: **Persistence Governance** — NOT Persistence Implementation.

Tags:
task-002i-complete, task-002i-merged (on main)

---

## LEGAL OBJECT PERSISTENCE SCHEMA CONTRACT

STATUS: VERIFIED (schema planning only; merged to main)

Implemented (TASK-003A):

* canonical legal object persistence schema contract (`backend/app/services/legal_object_schema_contract/`)
* proposed tables: `legal_objects`, `legal_object_versions`, `legal_object_lineage`, `legal_object_duplicates`
* `schema_definition.py` — field-level contract definitions
* `constraints.py`, `indexes.py`, `immutability.py`, `lineage.py`

Tags:
task-003a-complete, task-003a-merged (on main)

---

## LEGAL OBJECT SQLALCHEMY MODELS

STATUS: VERIFIED (ORM definitions only; merged to main)

Implemented (TASK-003B):

* SQLAlchemy ORM models in `backend/app/models/`
* aligned with TASK-003A schema contract
* `legal_object_id` externally supplied — no random ID generation on identity PK

Tags:
task-003b-complete, task-003b-merged (on main)

---

## LEGAL OBJECT ALEMBIC MIGRATION

STATUS: VERIFIED (merged to main)

Implemented (TASK-003C):

* Alembic revision `f7c2d9e41a83` — four legal object persistence tables
* Alembic head: `f7c2d9e41a83`

Tags:
task-003c-complete, task-003c-merged (on main)

---

## LEGAL OBJECT PERSISTENCE REPOSITORY

STATUS: **MERGED / CLOSED** (TASK-003D on `main`)

Implemented (TASK-003D):

* legal object persistence repository contract (`backend/app/services/legal_object_persistence/`)
* `LegalObjectPersistenceService.persist()` — only `ConvergedLegalObjectCandidate` input
* creates `legal_objects` and `legal_object_versions` rows; duplicate detection without auto-merge
* immutable version fields; `current_version_id` updated after new version only

**Implemented in TASK-003E (merged):** lineage and duplicate table writes, integrity enforcement.

Strictly: **Controlled Write Path** — NOT CRUD APIs, ingestion wiring, or UI.

Tags:
task-003d-complete, task-003d-merged (on main)

Merge commit: `82e2e79`

---

## LEGAL OBJECT PERSISTENCE INTEGRITY

STATUS: **MERGED / CLOSED** — Legal Object Persistence Integrity baseline **frozen**

Merge commit: `0213fb1`
Checkpoint tag: `checkpoint-task-003e` (on `main`)

Implemented (TASK-003E):

* integrity & immutability enforcement (`backend/app/services/legal_object_persistence/`)
* deterministic content integrity hashing (`integrity_hash.py`) — stable fields only; volatile fields excluded
* source traceability validation — requires resolvable `source_version_id` and `source_document`
* status discipline — `draft`, `active`, `superseded`, `archived`, `rejected` (app + DB CHECK constraints)
* `LegalObjectIntegrityService` — `archive_legal_object`, `supersede_legal_object`, guarded `update_legal_object`
* supersession integrity guards — requires `CREATED` persist; rejects self-referential supersession; rollback on rejection
* hard delete prohibited at repository layer; archive/supersede preserve historical rows
* `legal_object_lineage` writes — `parent_child`, `supersedes`, `superseded_by`
* `legal_object_duplicates` writes — cross-object hash collision recorded; no auto-merge
* transaction rollback on persistence failure
* `audit_log` writes for create, duplicate, archive, supersede lifecycle events
* Alembic `b8d4e1a92c05` — status CHECK constraints + `UNIQUE (legal_object_id, text_hash)`

Tests (main, post-merge): **225 passed, 91 skipped**

**Documented deferrals (acceptable at this phase):**

* direct SQL bypass risk (application-layer enforcement)
* audit `entity_id` UUID mismatch for string `legal_object_id`
* integrity hash not persisted as dedicated DB column
* secondary enum DB constraints (`extraction_status`, duplicate enums)
* duplicate resolution logic (records only)

**Out of scope (preserved):** CRUD APIs, ingestion orchestration, UI, answer engine

**VM snapshot gate:** complete — Docker, Postgres, and pgAdmin verified running post-snapshot.

---

## LEGAL OBJECT RETRIEVAL

STATUS: **MERGED / CLOSED** (TASK-004A on `main`)

Merge commit: `90357ff`
Checkpoint tag: `checkpoint-task-004a`

Implemented (TASK-004A):

* deterministic legal object retrieval contract (`backend/app/services/retrieval/`)
* `LegalObjectRetrievalService` — `retrieve()`, `retrieve_by_id()`, `retrieve_active()`, `retrieve_effective()`
* `LegalObjectRetrievalRequest` / `LegalObjectRetrievalResult` strict Pydantic models
* effective-date filtering — `effective_from <= effective_on AND (effective_to IS NULL OR effective_to >= effective_on)`
* status filtering — excludes `archived`/`rejected` by default; `superseded` unless `include_superseded=True`
* integrity verification on read — `text_hash` check + `integrity_hash` computation
* source traceability — every result carries `source_document_id`, `source_version_id`, hashes, identifiers
* deterministic ordering only — no semantic/AI ranking

Tests (main, post-merge): **230 passed, 104 skipped**

**Out of scope (preserved):** embeddings, pgvector, semantic search, RAG, AI retrieval, answer generation, citation assembly, CRUD APIs

**Deferred hardening:** apply deterministic ordering before `.first()` in `retrieve_by_id()` when `effective_on` is set and multiple version rows match.

**VM snapshot:** not required before TASK-004B unless schema or persistence behavior changes.

---

## EFFECTIVE-DATE RESOLVER

STATUS: **MERGED / CLOSED** (TASK-004B on `main`)

Merge commit: `08efa3b`
Checkpoint tag: `checkpoint-task-004b`

Implemented (TASK-004B):

* effective-date resolver contract (`backend/app/services/effective_date/`)
* `EffectiveDateResolver` — `resolve()`, `resolve_by_legal_object_id()`
* `EffectiveDateResolutionRequest` / `EffectiveDateResolutionResult` strict Pydantic models
* `ResolutionStatus` — `applicable`, `not_applicable`, `ambiguous_overlap`, `missing_effective_date`, `integrity_failed`
* deterministic date rule (aligned with TASK-004A); ambiguous overlap flagged, not silently resolved
* missing effective dates flagged when both bounds are NULL
* integrity verification on read; reuses TASK-004A status filters

Tests (main, post-merge): **232 passed, 115 skipped**

**Out of scope (preserved):** AI, RAG, embeddings, pgvector, citation assembly, answer generation, API routes

**Deferred hardening:**

* overlap result metadata enrichment (conflicting version IDs in `AMBIGUOUS_OVERLAP` results)
* outer sort `created_at` parity hardening in resolver result ordering

**VM snapshot:** not required before next TASK-004 task unless schema or persistence behavior changes.

---

## CITATION CANDIDATE PREPARATION

STATUS: **MERGED / CLOSED** (TASK-004C on `main`)

Merge commit: `1349eb7`
Checkpoint tag: `checkpoint-task-004c`
Review verdict: **APPROVED FOR MERGE** (all seven confirmations; blocker scan: NONE)

Implemented (TASK-004C):

* citation candidate contract (`backend/app/services/citation_candidate/`)
* `CitationCandidateBuilder` — `build()`, `build_from_retrieval_result()`, `build_from_resolution_result()`
* `CitationCandidateRequest` / `CitationCandidate` strict Pydantic models
* `CandidateStatus` — `ready`, `source_traceability_failed`, `integrity_failed`, `date_ambiguous`, `date_not_applicable`, `missing_effective_date`
* resolution status mapping from TASK-004B (conservative; demote-only from `ready`; no silent promotion)
* source traceability from `source_documents`, `source_versions`, `countries`, `tax_types`
* integrity verification reused from TASK-004A (`verify_text_hash`)
* deterministic ordering inherited from retrieval/resolution — no ranking

Tests (post-merge VM): **11 citation candidate tests passed**; full suite **350 passed** (PostgreSQL)

**Out of scope (preserved):** final citation formatting, citation style rules, answer generation, authority weighting, legal interpretation, AI, RAG, embeddings, semantic retrieval, API routes, candidate persistence, database migrations

**Forward-governance notes (non-blocking; see KNOWN_LIMITATIONS.md):** `ready` without `effective_on` does not assert date applicability; `_resolve_version_id` uses `.first()` without explicit ordering; zero-UUID sentinel on traceability failure requires consumers to gate on `candidate_status`; unmapped `ResolutionStatus` fails loud via `KeyError`.

**VM snapshot:** not required — no schema or persistence behavior changes.

---

## STATUS

VERIFIED

Latest suite result (main, post TASK-004C merge):

350 passed (PostgreSQL VM)
115 skipped (integration tests without PostgreSQL)

Warnings:

* timezone-aware UTC cleanup still pending
* no failing tests currently known

Testing currently includes:

* CRUD API testing
* migration verification
* storage abstraction testing
* checksum testing
* validation testing
* immutability testing
* legal object retrieval testing (TASK-004A)
* effective-date resolver testing (TASK-004B)
* citation candidate builder testing (TASK-004C)

---

# DOCUMENTATION STATUS

## STATUS

ESTABLISHED

Implemented:

* README.md
* DEVELOPMENT_SETUP.md
* OPERATIONAL_RUNBOOK.md
* BACKUP_AND_RECOVERY.md
* MIGRATION_WORKFLOW.md
* DEVELOPMENT_WORKFLOW.md
* TASK_EXECUTION_STANDARD.md
* INCIDENT_RESPONSE.md
* RELEASE_CHECKLIST.md
* CHANGELOG.md
* KNOWN_LIMITATIONS.md
* OPEN_DECISIONS.md
* TASK_REGISTRY.md

Operational governance documentation established successfully.

---

# CURRENT INFRASTRUCTURE

## HOSTING

In-house VM

## OS

Ubuntu 26.04 LTS

## CONTAINERIZATION

Docker + Docker Compose

## DATABASE

PostgreSQL 16

## ADMIN TOOLING

pgAdmin

## REPOSITORY

GitHub

---

# COMPLETED TASKS

| Task      | Status                                              |
| --------- | --------------------------------------------------- |
| TASK-001A | Runtime foundation — VERIFIED                       |
| TASK-001D | CRUD + internal admin APIs — VERIFIED               |
| TASK-001E | Alembic migration discipline — VERIFIED             |
| TASK-001F | Baseline API tests — verified on VM                 |
| TASK-001G | Documentation + operational runbooks — VERIFIED     |
| TASK-001H | Storage abstraction + checksum utility — VERIFIED   |
| TASK-001I | Timezone-aware UTC timestamps — VERIFIED            |
| TASK-001J | Source upload internal API — VERIFIED               |
| TASK-001K | Source attachment workflow — VERIFIED               |
| TASK-001L | Source ingestion status state machine — VERIFIED    |
| TASK-001M | Source processing queue table — VERIFIED            |
| TASK-001N | Processing job claim / lock API — VERIFIED          |
| TASK-001O | Processing job result / completion API — VERIFIED   |
| TASK-001P | Worker contract + no-op harness — VERIFIED          |
| TASK-002A | Source text extraction contract — VERIFIED          |
| TASK-002B | Structural source segmentation contract — VERIFIED  |
| TASK-002C | Legal object extraction contract — VERIFIED         |
| TASK-002D | Canonical citation anchor contract — VERIFIED       |
| TASK-002E | Cross-reference detection contract — VERIFIED (merged to main) |
| TASK-002F | Structural section parser contract — VERIFIED (merged to main) |
| TASK-002G | Structural legal object extraction contract — VERIFIED (merged to main) |
| TASK-002H | Legal object candidate convergence contract — VERIFIED (merged to main) |
| TASK-002I | Legal object persistence planning contract — VERIFIED (merged to main) |
| TASK-003A | Canonical legal object persistence schema contract — VERIFIED (merged to main) |
| TASK-003B | Canonical legal object SQLAlchemy models — VERIFIED (merged to main) |
| TASK-003C | Canonical legal object Alembic migration — VERIFIED (merged to main) |
| TASK-003D | Legal object persistence repository contract — **MERGED / CLOSED** (tag `task-003d-merged`) |
| TASK-003E | Legal object persistence integrity & immutability enforcement — **MERGED / CLOSED** (tag `checkpoint-task-003e`) |
| TASK-004A | Legal object retrieval contract — **MERGED / CLOSED** (tag `checkpoint-task-004a`) |
| TASK-004B | Effective-date resolver contract — **MERGED / CLOSED** (tag `checkpoint-task-004b`) |
| TASK-004C | Citation candidate contract — **MERGED / CLOSED** (tag `checkpoint-task-004c`) |

---

# CURRENT BRANCH STATUS

## ACTIVE BRANCH

main (no feature branch in progress)

## MAIN BRANCH

main (at `1349eb7` — TASK-004C merged; tag `checkpoint-task-004c`)

Legal memory stack on `main`:

```text
003A → Schema Contract
003B → SQLAlchemy ORM Models
003C → Alembic Materialization
003D → Controlled Write Path
003E → Integrity & Immutability Enforcement
004A → Deterministic Legal Object Retrieval
004B → Effective-Date Resolver
004C → Citation Candidate Preparation
```

**Current boundary:** persistence, integrity, retrieval, effective-date resolution, and citation candidate DTO preparation active on `main`. No final citation formatting, no candidate persistence, no API routes.

**VM snapshot:** not required before TASK-004D unless schema or persistence behavior changes.

---

# CURRENT TAGS

* v0.1.0-task-001-foundation
* v0.1.1-crud-foundation
* v0.1.1-task-001-foundation-verified
* v0.1.2-storage-foundation
* v0.1.8-processing-job-claim-api
* v0.1.9-processing-job-result-api
* v0.1.10-worker-contract-noop
* v0.2.0-task-002a
* v0.2.1-task-002b
* v0.2.2-post-merge-stabilization
* v0.2.3-task-002c
* v0.2.4-task-002d
* task-002e-complete
* task-002e-merged
* task-002f-complete
* task-002f-merged
* task-002g-complete
* task-002g-merged
* task-002h-complete
* task-002h-merged
* task-002i-complete
* task-002i-merged
* task-003a-complete
* task-003a-merged
* task-003b-complete
* task-003b-merged
* task-003c-complete
* task-003c-merged
* task-003d-complete
* task-003d-merged
* checkpoint-task-003e
* checkpoint-task-004a
* checkpoint-task-004b
* checkpoint-task-004c

---

# NEXT APPROVED TASKS

*(None registered — awaiting TASK-004D spec)*

**VM snapshot:** not required unless next task changes schema or persistence behavior.

---

## TASK-001I

Replace utcnow with timezone-aware UTC timestamps

Purpose:

* eliminate SQLAlchemy deprecation warnings
* enforce timezone-safe UTC handling
* establish long-term timestamp governance

---

## TASK-001J

Source Upload Internal API

STATUS: COMPLETE

* `POST /source-versions/{id}/upload`
* checksum-verified write via `LocalFileStorage`
* no overwrite on duplicate upload

---

## TASK-001K

Source Version File Attachment Workflow

STATUS: COMPLETE

* `has_attached_file`, `validate_attachment_state`, `get_attachment_status`
* API fields: `file_attached`, `attachment_status` (`pending` | `attached` | `inconsistent`)
* see [SOURCE_ATTACHMENT_WORKFLOW.md](SOURCE_ATTACHMENT_WORKFLOW.md)

---

# DEFERRED WORK

Deferred intentionally:

* ingestion agents
* OCR
* semantic extraction
* embeddings
* vector DB
* retrieval ranking
* AI reasoning
* upload UI
* public APIs
* authentication/RBAC
* enterprise workflows

Reason:
foundation-first architecture discipline.

---

# OPEN DECISIONS

See [OPEN_DECISIONS.md](OPEN_DECISIONS.md) for the full decision register.

**OD-010 (governed through TASK-003E merged):** Convergence → schema → ORM → migration →
repository write path → **integrity enforcement** active on `main`. Lineage and duplicate table
writes active. CRUD APIs and ingestion wiring remain blocked. Documented deferrals: direct SQL bypass,
audit UUID mismatch, integrity hash not as DB column, secondary enum CHECKs.

## StorageService Interface Scope

Current implementation includes:

* save_bytes
* read_bytes

Deferred decision:

* exists()
* delete()

Decision deferred until:

* upload APIs
* ingestion workflows
* lifecycle management
* retention policies

Reason:
avoid premature abstraction expansion before real ingestion workflows exist.

---

# KNOWN LIMITATIONS

Current limitations:

* local storage only
* no authentication
* no object storage provider
* no upload APIs
* no ingestion automation
* no public deployment
* no source parsing yet
* no retrieval engine yet

These limitations are intentional at current phase.

---

# OPERATIONAL NOTES

## TEST EXECUTION

Integration tests require:

* TEST_POSTGRES_* environment variables

Shell-export consistency improvement still pending.

---

## DATABASE GOVERNANCE

All schema evolution must occur through:

* Alembic migrations only

Direct DB modification prohibited.

---

## STORAGE GOVERNANCE

Raw legal source files:

* stored outside PostgreSQL
* checksum verified
* immutable where required
* path-normalized
* deterministic

---

# CURRENT PRIORITY

Current engineering priority:

1. timestamp governance
2. controlled upload workflows
3. immutable source attachment workflows
4. ingestion infrastructure
5. ingestion orchestration
6. retrieval architecture

AI ingestion agents remain intentionally deferred until deterministic ingestion foundation is complete.

---

END OF PROJECT STATE
