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

**Deferred to TASK-003E (explicit — not in TASK-003D scope):**

* `legal_object_lineage` table writes — candidate `parent_legal_object_id` preserved on version rows only; lineage table population deferred
* `legal_object_duplicates` table writes — duplicate detection returns `DUPLICATE_DETECTED` with warnings; no duplicate-resolution or auto-merge records yet

Strictly: **Controlled Write Path** — NOT CRUD APIs, ingestion wiring, or UI.

Tags:
task-003d-complete, task-003d-merged (on main)

Merge commit: `82e2e79`

---

# TESTING STATUS

## STATUS

VERIFIED

Latest suite result (main, post TASK-003D merge):

213 passed
80 skipped (integration tests without PostgreSQL)

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
| TASK-003E | Legal object persistence integrity & immutability enforcement — **APPROVED, not started** |

---

# CURRENT BRANCH STATUS

## ACTIVE BRANCH

main (no feature branch in progress)

## MAIN BRANCH

main (at `82e2e79` — TASK-003D merged)

TASK-002A through TASK-003D are merged into main.
Persistence stack: 003A schema contract → 003B ORM → 003C migration → 003D controlled write path.

**Current boundary:** persistence write path exists; automatic ingestion wiring, CRUD APIs, and
lineage/duplicate table writes do not (lineage/duplicate writes targeted by TASK-003E).

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

---

# NEXT APPROVED TASKS

## TASK-003E

Legal Object Persistence Integrity & Immutability Enforcement

STATUS: APPROVED — not started

Focus:

* immutability enforcement on version rows
* transaction safety and rollback behavior
* `legal_object_lineage` table writes
* `legal_object_duplicates` table writes
* stronger repository tests

Out of scope:

* CRUD APIs
* ingestion orchestration
* UI
* answer engine

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

**OD-010 (governed through TASK-003D; integrity work in TASK-003E):** Convergence → schema →
ORM → migration → **repository write path** (`LegalObjectPersistenceService`). CRUD APIs and
ingestion wiring remain blocked. **`legal_object_lineage` and `legal_object_duplicates` table
writes remain deferred on main** — duplicate detection is lookup-only; lineage/duplicate
persistence is the primary scope of TASK-003E.

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
