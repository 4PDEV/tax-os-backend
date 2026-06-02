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

### 9. AGENT LAYER — **FUTURE**

**Intent:** Autonomous or semi-autonomous ingestion/monitoring agents operating on governed contracts and persistence.

**Prerequisites:** TASK-006B, TASK-006C contract boundaries, ingestion worker wiring, stable CI/VM tests.

**Note:** Former draft “TASK-006B Source Monitoring Agent” belongs here, **not** in current 006B slot.

---

### 10. RETRIEVAL LAYER — **FUTURE**

**Intent:** Research-grade retrieval beyond 004A contract (ranking, multi-source assembly, operational APIs as governed).

**Prerequisites:** Temporal governance, citation baseline, stable legal memory.

---

### 11. ANSWER ASSEMBLY — **FUTURE**

**Intent:** Source-referenced answers with mandatory disclosure, ambiguity surfacing, no silent legal inference.

**Prerequisites:** Retrieval layer, temporal compliance (incl. TASK-004E when required), citation integrity.

**Explicitly excluded from near-term roadmap:** probabilistic/AI answer generation without governance tasks.

---

## Current position (one line)

**Phases 1–8 complete on `main`; next implementation work is post-contract agent/workflow execution under bounded governance.**

---

## Related documents

| Document | Role |
|----------|------|
| [CURRENT_STATUS.md](CURRENT_STATUS.md) | Canonical status snapshot |
| [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) | Task-level COMPLETE / NEXT / DEFERRED |
| [TEMPORAL_VERSIONING_ARCHITECTURE.md](TEMPORAL_VERSIONING_ARCHITECTURE.md) | Temporal doctrine |
| [architecture-references/README.md](architecture-references/README.md) | Links to `tax-os-architecture` |
