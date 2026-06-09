# PROJECT_STATE.md

**Canonical handoff summary** for new ChatGPT chats, Cursor sessions, Claude reviews, and team onboarding.

> **Also read:** [CURRENT_STATUS.md](CURRENT_STATUS.md) · [TASK_REGISTRY.md](TASK_REGISTRY.md) · [DECISION_LOG.md](DECISION_LOG.md) · [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) · [OPEN_DECISIONS.md](OPEN_DECISIONS.md)

**Last handoff realigned:** 2026-06-02 · **Branch:** `main` · **Checkpoint:** `checkpoint-task-008b-ranking-runtime-contract`

---

## 1. Project Identity

| Item | Value |
|------|--------|
| **Platform name** | TAX-OS |
| **Product** | Source-Referenced Business & Tax Research Platform |
| **Positioning** | Deterministic, version-aware legal memory and evidence pipeline — not probabilistic tax advice |
| **First jurisdiction** | Rwanda |
| **Initial tax domains** | VAT, PAYE/PIT, WHT, corporate tax, capital gains, customs & excise (registry phase) |
| **Long-term scope** | Multi-jurisdiction expansion; governed ingestion → legal objects → citations → retrieval → ranking → answer assembly (each layer separately authorized) |
| **Environments** | Development and internal staging only — no public production deployment |

---

## 2. Core Governance Principles

- **AI is not source of truth** — models may assist; canonical law lives in versioned sources and persisted legal memory.
- **Source-referenced only** — every output must trace to `source_version` lineage.
- **Deterministic-first** — reproducible behavior; explicit sort keys; no silent defaults.
- **Version-aware** — `legal_object_version` pins; no inference from `legal_object_id` alone.
- **Effective-date-aware** — temporal modes explicit; legal-object dates govern applicability.
- **No silent overwrite** — append-only lifecycles; `force_replay` is audit-only.
- **Ambiguity/conflict must be surfaced** — no silent winner selection; overlaps returned or failed explicitly.
- **Ranking is not answer generation** — ranking permutes presentation order only.
- **Answer is not legal conclusion** — answer assembly (not yet authorized) must not imply legal force.
- **Provenance must live once only** — evidence pins authoritative in retrieval; ranking holds pointers + order.
- **Git/docs are source of truth, not chats** — commit governance artifacts; chat history is not authoritative.

---

## 3. Architecture Doctrine

Governed pipeline (layers close independently; downstream requires upstream review):

```text
Source Registry → Source Versions → Extraction → Parsing → Legal Objects
  → Citations → Temporal/Versioning → Retrieval Evidence → Ranking → Answer Assembly (later)
```

| Layer | Status (summary) |
|-------|------------------|
| Source Registry & Versions | **COMPLETE** (TASK-001*) |
| Extraction / Parsing contracts | **COMPLETE** (TASK-002*) |
| Legal Object persistence | **COMPLETE** (TASK-003*) |
| Citation governance & execution | **COMPLETE** (006Y–006AD) |
| Temporal governance | **COMPLETE** (005A-SPEC) |
| Retrieval layer | **COMPLETE** (007A–007E) |
| Ranking contract | **COMPLETE** (008B-v2) — 008C-REMEDIATION **complete** |
| Answer assembly | **NOT AUTHORIZED** (009A+) |

**Foundational rule:** No AI legal reasoning in ingestion, legal-object, citation, retrieval, or ranking layers.

**Evidence chain:**

```text
source_version → extracted_text → parsed_structure → legal_object → legal_object_version → citation
  → retrieval_evidence_reference → ranked_evidence_reference (pointer only)
```

---

## 4. Completed Tasks (verified subset)

> **Note:** Status must be verified against Git commit history before final release tagging. See [TASK_REGISTRY.md](TASK_REGISTRY.md) for full registry.

| Task | Title | Status |
|------|-------|--------|
| TASK-001A | Runtime foundation | Complete |
| TASK-001D | CRUD + Internal Admin APIs | Complete |
| TASK-001E | Alembic Migration Discipline | Complete |
| TASK-001F | Baseline API Tests | Complete |
| TASK-001G | Documentation + Operational Runbook | Complete |
| TASK-002A | Source Text Extraction Contract | Complete |
| TASK-002E | Cross-Reference Detection Contract | Complete |
| TASK-003E | Legal Object Persistence Integrity & Immutability | Complete |
| TASK-004D | Citation Assembly Contract | Complete |
| TASK-005A-SPEC | Temporal & Versioning Architecture | Complete |

**Also complete on `main` (not exhaustive):** ingestion persistence (006A), parsing/legal-object promotion (006Q–006X), citation pipeline (006Y–006AD), retrieval pipeline (007A–007E), ranking contract (008B). See detailed history below and [TASK_REGISTRY.md](TASK_REGISTRY.md).

---

## 5. Current Active Architecture Issue

### TASK-008C-REMEDIATION — Ranking Contract Reconciliation

**Status:** **COMPLETE** (2026-06-02) — [`RANKING_PERSISTENCE_REMEDIATION_008C-REMEDIATION.md`](RANKING_PERSISTENCE_REMEDIATION_008C-REMEDIATION.md).

**Ruling (locked — provenance-once doctrine):**

Ranking stores **order only**. Provenance lives **once** in `retrieval_evidence_references`.

**`ranked_evidence_references` pure-pointer shape (008B-v2):**

- `retrieval_result_id`
- `retrieval_evidence_reference_id` — composite FK to scoped evidence row
- `presentation_order_index`

**Prohibited on ranked rows:** `legal_object_id`, `legal_object_version_id`, `source_version_id`, `citation_id`, `citation_hash`, `authority_weight`, `importance_flag`, `preference_score`.

**TASK-008C migration/models:** **NOT AUTHORIZED** — next gate after 008C pre-auth / persistence task prompt.

---

## 6. Ranking Doctrine

| Doctrine | Rule |
|----------|------|
| `retrieval result` ≠ ranking | Retrieval selects evidence; ranking permutes only |
| `ranking` ≠ answer | No answer text at ranking boundary |
| `answer` ≠ legal conclusion | No applicability or legal force inference |
| Ranking stores order only | `presentation_order_index` — not relevance |
| Provenance lives once | Retrieval evidence rows own pins; ranking joins |
| No relevance scoring | Prohibited score columns |
| No AI / semantic ranking | Not authorized |
| No concurrent ranking workers | OD-021 — single-worker only |

**Architecture chain:** Evidence → Ranking → Answer Assembly → Response Runtime

---

## 7. 008C-REMEDIATION Items (complete)

All items applied in [`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md) (008B-v2):

1. Pure-pointer `ranked_evidence_references` contract
2. Composite FK structural membership (`retrieval_result_id`, `id`)
3. Canonical error vocabulary (9 categories)
4. `evidence_set_empty` removed
5. Zero-result → `completed`, `rank_count=0`
6. Prohibited interpretive fields documented
7. **008C implementation** — still **not authorized**

---

## 8. Infrastructure State

| Item | Value |
|------|--------|
| Host | `ubuntu-246` |
| OS | Ubuntu 26.04 LTS |
| Runtime | Docker-based development |
| Database | PostgreSQL 16 (container) |
| Admin UI | pgAdmin (container) |
| Base path | `/opt/tax-os` |
| Backend repo | `/opt/tax-os/repos/tax-os-backend` |
| Infra repo | `/opt/tax-os/repos/tax-os-infra` |
| GitHub remote | `git@github.com:4PDEV/tax-os-backend.git` |
| Alembic head | `f9e4d2a87c10` (retrieval persistence — no ranking tables yet) |
| Test DB | `taxos_test` — see [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) |

---

## 9. Current Operating Model

| Role | Responsibility |
|------|----------------|
| **ChatGPT** | Architect / governance — task specs, doctrine, sequencing |
| **Cursor** | Implementation — bounded tasks only |
| **Claude** | Review / audit — pipeline closure, pre-auth |
| **GitHub** | Source of truth — commits, tags, checkpoints |

**Rules:**

- Tasks must be **bounded** with explicit acceptance criteria.
- **No implementation** without task specification.
- **No architecture changes** through ad hoc code.
- Locked decisions live in [DECISION_LOG.md](DECISION_LOG.md) and [OPEN_DECISIONS.md](OPEN_DECISIONS.md).

---

## 10. Next Recommended Steps

1. ~~Complete TASK-008C-REMEDIATION~~ — **done**
2. Review reconciliation with Claude (recommended).
3. Authorize **TASK-008C** ranking persistence (separate bounded task).
4. Start new ChatGPT chat using this document as primary context.

**Not authorized:** 008C implementation, 008D worker, 008D execution, 009A answer runtime, AI ranking.

---

## 11. New Chat Continuation Prompt

Copy into a new ChatGPT session:

```text
We are continuing TAX-OS, a Source-Referenced Business & Tax Research Platform. ChatGPT is Architect/Governance. Cursor is Developer. Claude is Reviewer. GitHub/docs are the source of truth, not chat history. Read and follow PROJECT_STATE.md, DECISION_LOG.md, TASK_REGISTRY.md, MASTER_SCOPE, and ADDENDUMS. Current active task is TASK-008C ranking persistence (not yet authorized) unless updated. Do not reopen locked decisions unless explicitly instructed.
```

---

# DETAILED MILESTONE HISTORY (Archive)

> The sections below retain historical milestone detail. For **current gate status**, prefer **Continuation State** above and [CURRENT_STATUS.md](CURRENT_STATUS.md).

---

# CURRENT PLATFORM STATUS

## STATUS

LEGAL MEMORY, TEMPORAL GOVERNANCE & INGESTION PERSISTENCE — TEST HARDENING GATE

(Former label “FOUNDATION PHASE ACTIVE” is stale; foundation is complete. See CURRENT_STATUS.md.)

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

## CITATION ASSEMBLY

STATUS: **MERGED / CLOSED** (TASK-004D + AMENDMENT-A on `main`)

Merge commit: `0588637`
Checkpoint tag: `checkpoint-task-004d`
Review verdict: **APPROVED FOR MERGE** (Claude architecture review)

Implemented (TASK-004D):

* citation assembly contract (`backend/app/services/citation/`)
* `CitationAssembler` — `assemble()`, `assemble_by_request()` with required `legal_object_version_id` pin
* `CitationFormatter` — display text only, separate from assembly
* `CitationResult` / `CitationAssemblyRequest` strict Pydantic models
* `AuthorityType` enum — statute, regulation, guidance, case, treaty, etc.
* location reference contract — identification only (Section, Article, Regulation, etc.)
* version awareness — never resolves implicit latest / `current_version_id`

Implemented (TASK-004D-AMENDMENT-A — Citation Identity Hardening):

* `CitationResult.legal_object_version_id` — mandatory on output (version-pinned citations, not only inputs)
* `citation_hash` — SHA-256(`source_version_id | legal_object_id | legal_object_version_id | location_reference`)
* `SourceDocumentMismatchError` — lineage enforcement when source version document ≠ legal object document
* same `legal_object_id` + different `legal_object_version_id` → different `citation_hash` / `citation_id`

Tests (post-merge VM): **20 citation assembly tests passed**

**Out of scope (preserved):** answer generation, citation ranking, authority weighting, legal reasoning, AI, semantic search, retrieval, API routes, citation persistence, database migrations

**Non-blocking follow-ups:** recorded in `OPEN_DECISIONS.md` (formatter locale, hash delimiter framing, shared hash utility, formatter version on `citation_text`, authority fallback)

**VM snapshot:** not required — no schema or persistence behavior changes.

---

## TEMPORAL & VERSIONING ARCHITECTURE

STATUS: **MERGED / CLOSED** (TASK-005A-SPEC + TASK-005B + pre-merge cleanup on `main`; tag `checkpoint-task-005a-spec`; merge `43c6ad0`)

**Architectural review:** APPROVED FOR MERGE (Claude — no CRITICAL findings; C1 resolved at governance level; CitationAssembler gap deferred to TASK-004E).

**Pre-merge cleanup (TASK-005C / IMP-1–3, IMP-5):** merged — status vocabulary reconciliation, total derived-status matrix, transaction/applicability date terminology, TASK-004E registered.

Authoritative document: `TEMPORAL_VERSIONING_ARCHITECTURE.md` (v1.1.1 post–cleanup)  
Task specs: `TASKS/TASK-005A-TEMPORAL-VERSIONING-ARCHITECTURE-SPEC.md`, `TASKS/TASK-005B-TEMPORAL-RESOLUTION-GOVERNANCE-AMENDMENT.md`  
Governance addendum: `ADDENDUM_V6_TEMPORAL_RESOLUTION_AND_VERSION_PINNING.md` (architecture repo)

**TASK-005B (merged into branch):** Claude review amendments — no silent temporal inheritance (C1), derived temporal status (C3/I5), transaction vs knowledge date (I1), answer disclosure (I2), `current_version_id` semantics (I3), citation contract C1 resolution at governance level.

Documented (TASK-005A-SPEC):

* temporal philosophy — past, present, future, unknown
* temporal axes — publication, effective from/to, retrieval, processing
* versioning philosophy — nothing overwritten; reproducible history
* source version governance — statuses, supersession chain
* legal object temporal model — effective dates + source_version_id
* amendment chain model — supersedes / superseded_by relationships
* future law support — published but not yet effective
* temporal query model — jurisdiction, tax type, question, **as-of date**
* answer-date resolution contract — `resolve_authorities_as_of()` (spec only; not implemented)
* temporal conflict handling — preserve ambiguity; never silently guess
* authority-type temporal extensions — court, guidance, treaty, accounting (specified, not implemented)
* version selection principle — never assume latest; date-aware explicit pins

**Out of scope (preserved):** answer engine, legal reasoning, authority ranking, temporal AI, effective-date inference, code changes

**Merge summary:** `MERGE_SUMMARY_TASK-005A.md`

**VM snapshot:** not required — specification only; no schema or code changes.

---

## SOURCE INGESTION PERSISTENCE (TASK-006A)

STATUS: **IMPLEMENTED — ACCEPTED FOR TARGETED REVIEW** (commit `acc32e4` on `main`; push allowed after TEST-GAP-001 recorded)

Implemented:

* append-only `extraction_runs` / `extracted_texts` / `parser_runs` / `parsed_structures`
* governed pipeline artifact states (`ingestion_state_transitions`) — separate from `source_versions.ingestion_status`
* deterministic SHA-256 hashing for text and parsed structures
* failed-run preservation; immutability discipline
* Alembic revision `c9a2f3b81d06`

**Validation:** ingestion tests 12/12 passed (PostgreSQL VM).

**Test gap (resolved):** **TEST-GAP-001** — isolated in TASK-006B and resolved via fixture transaction hardening + deterministic ordering/migration-test updates. See `OPEN_DECISIONS.md` and `TESTING_GUIDE.md`.

**Out of scope (preserved):** workers, orchestration, APIs, embeddings, legal-object wiring from ingestion artifacts

---

## STATUS

VERIFIED (ingestion + stability)

Latest TASK-006B validation (PostgreSQL VM, `TEST_DATABASE_URL`):

* ingestion persistence tests: 12 passed
* legal-object integrity + retrieval focused suite: 27 passed
* full suite run #1: 390 passed
* full suite run #2: 390 passed
* full suite run #3: 390 passed

Alembic test head verified: `c9a2f3b81d06`.

Warnings:

* timezone-aware UTC cleanup still pending

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
* citation assembly testing (TASK-004D)

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
| TASK-004D | Citation assembly contract — **MERGED / CLOSED** (tag `checkpoint-task-004d`) |
| TASK-005A-SPEC | Temporal & versioning architecture — **MERGED / CLOSED** (tag `checkpoint-task-005a-spec`) |
| TASK-005B | Temporal resolution governance amendment — **MERGED / CLOSED** (with 005A-SPEC) |
| TASK-006A | Source ingestion persistence layer — **IMPLEMENTED** (commit `acc32e4`; Alembic `c9a2f3b81d06`) |

---

# CURRENT BRANCH STATUS

## ACTIVE BRANCH

`main`

## MAIN BRANCH

main (TASK-006B stabilized `45214c8`; checkpoint `checkpoint-task-006b-test-stability`)

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
004D → Citation Assembly (+ AMENDMENT-A identity hardening)
005A-SPEC → Temporal & Versioning Architecture (governance)
005B → Temporal Resolution Governance (Addendum V6 alignment)
006A → Source Ingestion Persistence (extraction/parser artifacts)
```

**Current boundary:** persistence, integrity, retrieval, effective-date resolution, citation candidates, deterministic citation assembly, **controlled citation execution** (TASK-006AD), **canonical temporal/versioning governance**, and **ingestion artifact persistence** active on `main`. Citation identity is version-pinned per 004D provenance tuple (`UNIQUE(citation_hash)`). `CitationAssembler` temporal compliance aligned with Addendum V6 (**TASK-004E**). Dry-run governance worker unchanged. Retrieval / answers **not authorized**.

**VM snapshot:** not required before next task unless schema or persistence behavior changes.

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
* checkpoint-task-004d
* checkpoint-task-005a-spec

---

# NEXT APPROVED TASKS

TASK-006P1 — Extraction Replay & Idempotency Hardening (**verified**; EXT-01/OD-019 remediated).

TASK-006Q — Parsing Trigger Contract (**complete**; governance-only; no parsing execution).

TASK-006R — Parsing Trigger Persistence (**complete**; append-only requests/results; no parsing execution).

TASK-006S — Parsing Worker Skeleton (**complete**; dry-run orchestration only; no real parsing).

TASK-006T — Controlled Parsing Execution (**complete**; structural `parsed_structures` only; no legal interpretation).

TASK-006T1A — Parsed Structure Identity Hardening (**verified**; P-01/P-02 closed).

**Parsing phase (006Q–006T):** Claude review **closed**. **Legal-object promotion (006U–006X):** Claude review **CLOSED** — **APPROVED FOR CONTINUE** (2026-06-03). L-01, L-02, L-02b closed. Canonical Legal Memory phase **CLOSED**.

**Citation governance layer:** **COMPLETE** (006Y). **Citation persistence:** **COMPLETE** (TASK-006Z).

TASK-006U — Legal Object Promotion Contract (**complete**; governance-only).

TASK-006V — Legal Object Promotion Persistence (**complete**; append-only requests/results; no execution).

TASK-006W — Legal Object Promotion Worker Skeleton (**complete**; dry-run orchestration only).

TASK-006X — Controlled Legal Object Promotion Execution (**complete**).

TASK-006X1 — Legal Object Version Identity Hardening (**complete**; L-02b verified).

TASK-006Y — Citation Assembly Contract (**complete**; governance-only).

**006Z pre-auth review:** Complete — APPROVED WITH REQUIRED REMEDIATION ([`ARCHITECTURE_REVIEW_CITATION_PERSISTENCE_006Z-PREAUTH.md`](ARCHITECTURE_REVIEW_CITATION_PERSISTENCE_006Z-PREAUTH.md)).

TASK-006ZA — Citation Persistence Remediation Package (**complete**; [`CITATION_PERSISTENCE_REMEDIATION_006ZA.md`](CITATION_PERSISTENCE_REMEDIATION_006ZA.md)).

TASK-006ZA — Acceptance review **CLOSED** (2026-06-03).

TASK-006Z — Citation Persistence (**complete**; accepted `checkpoint-task-006z-citation-persistence`; 667 tests).

TASK-006AA — Citation Worker Skeleton Pre-Auth Review (**complete**; APPROVED FOR 006AB dry-run skeleton).

TASK-006AB — Citation Worker Skeleton (**complete**; accepted `checkpoint-task-006ab-citation-worker-skeleton`).

**Citation pipeline review (006Y–006AD):** **CLOSED** — APPROVED FOR CONTINUE ([`CLAUDE_REVIEW_CITATION_PIPELINE_006Y-006AD.md`](CLAUDE_REVIEW_CITATION_PIPELINE_006Y-006AD.md)). Checkpoint: `checkpoint-task-006y-006ad-citation-pipeline-review`.

**TASK-007A:** **CLOSED** — APPROVED WITH REQUIRED REMEDIATION BEFORE TASK-007B ([`ARCHITECTURE_REVIEW_RETRIEVAL_RUNTIME_007A-PREAUTH.md`](ARCHITECTURE_REVIEW_RETRIEVAL_RUNTIME_007A-PREAUTH.md)).

**TASK-007A1 acceptance:** **CLOSED** — [`RETRIEVAL_RUNTIME_007A1_ACCEPTANCE_REVIEW.md`](RETRIEVAL_RUNTIME_007A1_ACCEPTANCE_REVIEW.md).

**TASK-007B:** **COMPLETE** — [`RETRIEVAL_RUNTIME_CONTRACT.md`](RETRIEVAL_RUNTIME_CONTRACT.md). Retrieval runtime **authorized with conditions** (contract only).

**TASK-007C pre-auth:** **CLOSED** — APPROVED WITH REQUIRED REMEDIATION BEFORE TASK-007C ([`ARCHITECTURE_REVIEW_RETRIEVAL_PERSISTENCE_007C-PREAUTH.md`](ARCHITECTURE_REVIEW_RETRIEVAL_PERSISTENCE_007C-PREAUTH.md)).

**TASK-007C1:** **COMPLETE** — [`RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md`](RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md). RP-01 through RP-08 remediated.

**TASK-007C1 acceptance:** **CLOSED** — TASK-007C **AUTHORIZED WITH CONDITIONS** ([`RETRIEVAL_PERSISTENCE_007C1_ACCEPTANCE_REVIEW.md`](RETRIEVAL_PERSISTENCE_007C1_ACCEPTANCE_REVIEW.md)).

**TASK-007C:** **COMPLETE** — append-only retrieval persistence (`retrieval_requests`, `retrieval_results`, `retrieval_evidence_references`); 744 tests.

**TASK-007D:** **COMPLETE** — **ACCEPTED** — dry-run retrieval worker skeleton; 759 tests.

**TASK-007D1 acceptance:** **CLOSED** — TASK-007E **AUTHORIZED WITH CONDITIONS** ([`RETRIEVAL_EXECUTION_007D1_ACCEPTANCE_REVIEW.md`](RETRIEVAL_EXECUTION_007D1_ACCEPTANCE_REVIEW.md)).

**TASK-007E:** **COMPLETE** — **ACCEPTED** — controlled retrieval execution; evidence selection + `retrieval_evidence_references`; 777 tests ([`TASKS/TASK-007E-CONTROLLED-RETRIEVAL-EXECUTION.md`](TASKS/TASK-007E-CONTROLLED-RETRIEVAL-EXECUTION.md)).

**Retrieval layer review (007A–007E):** **CLOSED** — **APPROVED FOR CONTINUE** — RET-01–RET-09 verified ([`CLAUDE_REVIEW_RETRIEVAL_PIPELINE_007A-007E.md`](CLAUDE_REVIEW_RETRIEVAL_PIPELINE_007A-007E.md)). Checkpoint: `checkpoint-task-007a-007e-retrieval-pipeline-review`.

**Governed pipeline:** 007B contract → 007C persistence → 007D dry-run skeleton → 007D1 remediation → 007D1 acceptance → **007E controlled execution (accepted)** → **retrieval layer (complete)**.

**TASK-008A1 acceptance:** **CLOSED** — **ACCEPTED** — TASK-008B **AUTHORIZED WITH CONDITIONS** ([`RANKING_RUNTIME_008A1_ACCEPTANCE_REVIEW.md`](RANKING_RUNTIME_008A1_ACCEPTANCE_REVIEW.md)). Option A selected; RK-01–RK-11 closed.

**TASK-008B:** **COMPLETE** — ranking runtime contract ([`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md)). 008A1 forward conditions resolved. Persistence/execution **not authorized**.

**Not authorized:** ranking persistence/execution (008C+), answers (009A), AI/semantic ranking, concurrent workers, legal advice.

TASK-006P — Controlled Extraction Execution (**completed; controlled local text extraction into extraction_runs/extracted_texts; no PDF/network/parsing/legal automation**).

TASK-006O — Extraction Worker Skeleton (**completed; dry-run-only trigger-to-extraction_run orchestration; no real extraction execution**).

TASK-006N — Extraction Trigger Persistence (**completed; append-only trigger request/result persistence with idempotency and force-reprocess auditability; no extraction execution automation**).

TASK-004E — Citation Temporal Compliance Remediation (**complete** — AC-01 closed).

TASK-006AC1 — Controlled Citation Execution Remediation Package (**complete** — AC-02/AC-03 remediated at spec level; [`CITATION_EXECUTION_REMEDIATION_006AC1.md`](CITATION_EXECUTION_REMEDIATION_006AC1.md)).

Post-006P implementation tasks must remain bounded and align with monitoring/fetch/detection/promotion/trigger/worker/extraction governance constraints.

**VM snapshot:** run full-suite verification before migration-heavy work.

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
