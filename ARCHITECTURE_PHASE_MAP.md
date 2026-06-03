# Architecture Phase Map

**High-level architecture evolution** for onboarding (TASK-DOC-001).  
Describes **phase order and intent**, not every task ID. Historical tasks remain in [PROJECT_STATE.md](PROJECT_STATE.md) and [TASK_REGISTRY.md](TASK_REGISTRY.md).

**Last realigned:** 2026-06-02

---

## Phase sequence

```text
FOUNDATION
  → EXTRACTION CONTRACTS
  → LEGAL OBJECT GOVERNANCE
  → CITATION GOVERNANCE
  → TEMPORAL GOVERNANCE
  → INGESTION PERSISTENCE
  → TEST HARDENING          ← current approved focus
  → AGENT LAYER
  → RETRIEVAL LAYER
  → ANSWER ASSEMBLY
```

---

## Phase reference

### 1. FOUNDATION — **COMPLETE**

**Intent:** Deterministic platform base — registry, versions, migrations, admin APIs, storage, audit hooks, processing queue skeleton.

**Representative tasks:** TASK-001*

**Key artifacts:** `source_documents`, `source_versions`, `source_processing_jobs`, FastAPI CRUD, Alembic discipline, local storage abstraction.

---

### 2. EXTRACTION CONTRACTS — **COMPLETE**

**Intent:** Faithful, non-interpretive contracts for text extraction, segmentation, structural parsing, cross-references — **in memory / Pydantic**, not yet durable ingestion store.

**Representative tasks:** TASK-002A–002F, 002E

**Key packages:** `extraction/`, `segmentation/`, `structure_parser/`, `cross_reference/`

---

### 3. LEGAL OBJECT GOVERNANCE — **COMPLETE**

**Intent:** Canonical legal memory — identity, convergence, schema, persistence, immutability.

**Representative tasks:** TASK-002G–002I, 003A–003E

**Key artifacts:** `legal_objects`, `legal_object_versions`, integrity services, `ConvergedLegalObjectCandidate` write path.

**Boundary:** Legal objects are **not** written directly from raw extraction/segmentation; convergence governs input.

---

### 4. CITATION GOVERNANCE — **COMPLETE**

**Intent:** Deterministic retrieval, effective-date resolution, citation candidates, assembled citations with version-pinned identity.

**Representative tasks:** TASK-004A–004D, 004D-AMENDMENT-A

**Key packages:** `retrieval/`, `effective_date/`, `citation_candidate/`, `citation/`

**Known deferred code gap:** TASK-004E (assembler temporal compliance vs Addendum V6).

---

### 5. TEMPORAL GOVERNANCE — **COMPLETE**

**Intent:** Platform-wide time/version doctrine — no silent inference, explicit pins, ambiguity preservation, derived temporal status, transaction vs knowledge dates.

**Representative tasks:** TASK-005A-SPEC, 005B, 005C (cleanup)

**Key artifacts:**

* [TEMPORAL_VERSIONING_ARCHITECTURE.md](TEMPORAL_VERSIONING_ARCHITECTURE.md)
* Addendum V6 (`tax-os-architecture`)
* [MERGE_SUMMARY_TASK-005A.md](MERGE_SUMMARY_TASK-005A.md)

**Milestone:** Major architecture gate — downstream tasks must align with this doctrine.

---

### 6. INGESTION PERSISTENCE — **COMPLETE**

**Intent:** First **durable** layer for ingestion artifacts — extracted text and parsed structures, append-only, auditable, version-aware.

**Representative task:** TASK-006A

**Key artifacts:** `extraction_runs`, `extracted_texts`, `parser_runs`, `parsed_structures`, `ingestion_state_transitions`; `services/ingestion/`.

**Distinction:** `source_versions.ingestion_status` = worker queue workflow; `ingestion_state_transitions` = pipeline artifact progression.

**Not included:** Workers, APIs, legal-object auto-materialization from artifacts.

---

### 7. TEST HARDENING — **COMPLETE**

**Intent:** Restore trustworthy full-suite execution on PostgreSQL VM before expanding pipeline or agents.

**Representative task:** TASK-006B (replaces superseded “Source Monitoring Agent” draft for id 006B)

**Driver:** TEST-GAP-001 — resolved in TASK-006B with full-suite repeatability.

---

### 8. AGENT GOVERNANCE CONTRACT — **COMPLETE**

**Intent:** Define safe monitoring boundaries before live automation.

**Representative task:** TASK-006C (contract-only)

**Key artifacts:**

* [SOURCE_MONITORING_AGENT_CONTRACT.md](SOURCE_MONITORING_AGENT_CONTRACT.md)
* [TASKS/TASK-006C-SOURCE-MONITORING-AGENT-CONTRACT.md](TASKS/TASK-006C-SOURCE-MONITORING-AGENT-CONTRACT.md)

**Boundaries:** no live scraping, no schedulers, no crawlers, no direct production publishing, no temporal/legal inference by monitoring agents.

---

### 9. MONITORING CANDIDATE PERSISTENCE — **COMPLETE**

**Intent:** Persist monitoring contract artifacts deterministically before any live automation.

**Representative task:** TASK-006D (persistence-only)

**Key artifacts:** allowlist entries, monitoring attempts/events/candidates, candidate state transition history.

**Boundaries:** no live monitoring, no scraping, no scheduler, no worker loop, no source publication.

---

### 10. MONITORING WORKER SKELETON — **COMPLETE**

**Intent:** Validate monitoring execution lifecycle safely before any real-world acquisition.

**Representative task:** TASK-006E (dry-run only)

**Key artifacts:** `workers/monitoring/` with dry-run provider, worker orchestration, and runner summary.

**Boundaries:** no live external HTTP, crawling, scraping, scheduling, or automatic ingestion.

---

### 11. CONTROLLED SOURCE FETCH CONTRACT — **COMPLETE**

**Intent:** Define fetch governance boundaries before real external acquisition.

**Representative task:** TASK-006F (contract-only)

**Key artifacts:**

* [CONTROLLED_SOURCE_FETCH_CONTRACT.md](CONTROLLED_SOURCE_FETCH_CONTRACT.md)
* [TASKS/TASK-006F-CONTROLLED-SOURCE-FETCH-CONTRACT.md](TASKS/TASK-006F-CONTROLLED-SOURCE-FETCH-CONTRACT.md)

**Boundaries:** no live fetch implementation, no HTTP requests, no crawling/scraping, no automated ingestion.

---

### 12. SOURCE CHANGE DETECTION CONTRACT — **COMPLETE**

**Intent:** Define safe change-classification governance before any diff engine implementation.

**Representative task:** TASK-006G (contract-only)

**Key artifacts:**

* [SOURCE_CHANGE_DETECTION_ENGINE_CONTRACT.md](SOURCE_CHANGE_DETECTION_ENGINE_CONTRACT.md)
* [TASKS/TASK-006G-SOURCE-CHANGE-DETECTION-ENGINE-CONTRACT.md](TASKS/TASK-006G-SOURCE-CHANGE-DETECTION-ENGINE-CONTRACT.md)

**Boundaries:** no diff engine implementation, no amendment inference, no legal/temporal interpretation, no automatic source-version creation.

---

### 13. CONTROLLED FETCH IMPLEMENTATION — **COMPLETE**

**Intent:** Prove fetch lifecycle mechanics safely using deterministic synthetic content and local fixtures only.

**Representative task:** TASK-006H

**Key artifacts:** `backend/app/services/fetch/` (`DryRunFetcher`, `LocalFixtureFetcher`, request/result contracts, checksum/content-type/safety utilities) and fixture-based tests under `backend/tests/`.

**Boundaries:** no live HTTP/HTTPS, no crawling/scraping, no source-version creation, no legal-object creation, no ingestion approval automation.

---

### 14. CONTROLLED FETCH PERSISTENCE — **COMPLETE**

**Intent:** Persist controlled fetch lifecycle artifacts as append-only records without introducing external acquisition behavior.

**Representative task:** TASK-006I

**Key artifacts:** `fetch_requests` and `fetch_results` tables, fetch persistence service (`backend/app/services/fetch/persistence.py`), and migration/integration tests.

**Boundaries:** no source version creation, no extracted text/legal-object creation, no candidate auto-approval/state transition, no live external fetching.

---

### 15. SOURCE CHANGE DETECTION PERSISTENCE — **COMPLETE**

**Intent:** Persist change-detection comparison requests/results as append-only evidence records before any detection engine implementation.

**Representative task:** TASK-006J

**Key artifacts:** `change_detection_requests` and `change_detection_results` tables, persistence services in `backend/app/services/change_detection/`, and migration/integration tests.

**Boundaries:** no diff engine, no amendment/legal/temporal inference, no source-version creation, no candidate auto-transition, no live external fetching.

---

### 16. SOURCE CHANGE DETECTION ENGINE SKELETON — **COMPLETE**

**Intent:** Execute bounded acquisition-level change classification using checksum-only comparison over persisted fetch results.

**Representative task:** TASK-006K

**Key artifacts:** `backend/app/services/change_detection/engine.py`, `checksum_engine.py`, `result.py`, and engine integration tests.

**Boundaries:** no textual/metadata/structural diff engine logic, no amendment/legal/temporal inference, no source-version creation, no candidate auto-transition, no live external fetching.

---

### 17. CONTROLLED SOURCE VERSION PROMOTION WORKFLOW — **COMPLETE**

**Intent:** Establish the first governed bridge from reviewed acquisition artifacts into canonical source memory.

**Representative task:** TASK-006L

**Key artifacts:** `backend/app/services/source_promotion/` workflow/request/result/validation modules and append-only `source_version_promotions` persistence.

**Boundaries:** promotion is explicit and review-gated only; no automatic ingestion/extraction/parsing/legal-object/citation creation and no legal/temporal inference.

---

### 18. SOURCE VERSION EXTRACTION TRIGGER CONTRACT — **COMPLETE**

**Intent:** Define governed extraction-trigger boundary between canonical source memory and extraction execution requests.

**Representative task:** TASK-006M (contract-only)

**Key artifacts:** `SOURCE_VERSION_EXTRACTION_TRIGGER_CONTRACT.md` and task contract record in `TASKS/`.

**Boundaries:** no extraction execution, no worker/queue implementation, no parsing/legal-object/citation/answer creation, no legal/temporal inference.

---

### 19. EXTRACTION TRIGGER PERSISTENCE — **COMPLETE**

**Intent:** Materialize extraction-trigger governance as durable, append-only evidence records before worker orchestration or extraction execution.

**Representative task:** TASK-006N

**Key artifacts:** `extraction_trigger_requests`, `extraction_trigger_results`, and `backend/app/services/extraction_trigger/`.

**Boundaries:** no extraction execution, no worker/queue implementation, no parsed/legal/citation/answer artifact creation.

---

### 20. EXTRACTION WORKER SKELETON — **COMPLETE**

**Intent:** Prove safe extraction lifecycle orchestration from trigger records to `extraction_runs` without executing real extractors.

**Representative task:** TASK-006O (dry-run only)

**Key artifacts:** `backend/app/workers/extraction/` with `ExtractionWorker`, `DryRunExtractionProvider`, and `run_extraction_dry_run()`.

**Boundaries:** no real extraction, no source parsing, no extracted_text/legal/citation/answer creation, no network IO.

---

### 21. CONTROLLED EXTRACTION EXECUTION — **COMPLETE**

**Intent:** Execute bounded local text extraction from approved artifacts into raw `extracted_text` evidence without legal interpretation.

**Representative task:** TASK-006P

**Key artifacts:** `ControlledLocalExtractionProvider`, `run_controlled_local_extraction()`, extraction safety/content helpers.

**Boundaries:** supported text formats only; no PDF/OCR/network/browser/AI; no parsed_structure/legal_object/citation/answer automation.

---

### 22. PARSING TRIGGER CONTRACT — **COMPLETE**

**Intent:** Define governed parsing-trigger boundary between canonical `extracted_text` evidence and structural parsing requests.

**Representative task:** TASK-006Q (contract-only)

**Key artifacts:** `PARSING_TRIGGER_CONTRACT.md` and task contract record in `TASKS/`.

**Boundaries:** no parsing execution, no parser worker/queue implementation, no `parsed_structure`/legal-object/citation/answer creation, no legal/temporal/amendment inference. `parsed_structure` ≠ legal meaning.

---

### 23. PARSING TRIGGER PERSISTENCE — **COMPLETE**

**Intent:** Materialize parsing-trigger governance as durable, append-only evidence records before parser worker orchestration or parsing execution.

**Representative task:** TASK-006R

**Key artifacts:** `parsing_trigger_requests`, `parsing_trigger_results`, and `backend/app/services/parsing_trigger/`.

**Boundaries:** no parsing execution, no parser worker/queue implementation, no `parsed_structure`/legal-object/citation/answer creation.

---

### 24. PARSING WORKER SKELETON — **COMPLETE**

**Intent:** Prove safe parsing lifecycle orchestration from trigger records to `parser_runs` without executing real parsers.

**Representative task:** TASK-006S (dry-run only)

**Key artifacts:** `backend/app/workers/parsing/` with `ParsingWorker`, `DryRunParsingProvider`, and `run_parsing_dry_run()`.

**Boundaries:** no real parsing, no `parsed_structure`/legal-object/citation/answer creation.

---

### 25. CONTROLLED PARSING EXECUTION — **COMPLETE**

**Intent:** Execute bounded structural parsing from `extracted_text` into `parsed_structures` without legal interpretation.

**Representative task:** TASK-006T

**Key artifacts:** `ControlledStructuralParsingProvider`, `structural.py`, `run_controlled_structural_parsing()`.

**Boundaries:** structural evidence only; `parsed_structure` ≠ legal meaning; no legal-object/citation/answer automation.

---

### 26. PARSED STRUCTURE IDENTITY HARDENING — **COMPLETE**

**Representative task:** TASK-006T1A

**Key artifacts:** `UNIQUE(parsed_structures.parser_run_id)`; P-01/P-02 closed.

---

### 27. LEGAL OBJECT PROMOTION CONTRACT — **COMPLETE**

**Intent:** Define governed promotion boundary from structural evidence to canonical legal memory.

**Representative task:** TASK-006U (contract-only)

**Key artifacts:** `LEGAL_OBJECT_PROMOTION_CONTRACT.md` and task record in `TASKS/`.

**Boundaries:** `parsed_structure` ≠ legal object; no promotion persistence/execution; no citation/answer automation.

---

### 28. AGENT LAYER — **FUTURE**

**Intent:** Autonomous or semi-autonomous ingestion/monitoring agents operating on governed contracts and persistence.

**Prerequisites:** TASK-006B, TASK-006C contract boundaries, ingestion worker wiring, stable CI/VM tests.

**Note:** Former draft “TASK-006B Source Monitoring Agent” belongs here, **not** in current 006B slot.

---

### 29. RETRIEVAL LAYER — **FUTURE**

**Intent:** Research-grade retrieval beyond 004A contract (ranking, multi-source assembly, operational APIs as governed).

**Prerequisites:** Temporal governance, citation baseline, stable legal memory.

---

### 30. ANSWER ASSEMBLY — **FUTURE**

**Intent:** Source-referenced answers with mandatory disclosure, ambiguity surfacing, no silent legal inference.

**Prerequisites:** Retrieval layer, temporal compliance (incl. TASK-004E when required), citation integrity.

**Explicitly excluded from near-term roadmap:** probabilistic/AI answer generation without governance tasks.

---

## Current position (one line)

**Phases 1–31 complete on `main`.** Canonical Source, Structural, Canonical Legal Memory, and Citation governance persistence **complete** (006Z). No citation execution, retrieval, or answer runtime.

---

## Related documents

| Document | Role |
|----------|------|
| [CURRENT_STATUS.md](CURRENT_STATUS.md) | Canonical status snapshot |
| [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) | Task-level COMPLETE / NEXT / DEFERRED |
| [TEMPORAL_VERSIONING_ARCHITECTURE.md](TEMPORAL_VERSIONING_ARCHITECTURE.md) | Temporal doctrine |
| [architecture-references/README.md](architecture-references/README.md) | Links to `tax-os-architecture` |
