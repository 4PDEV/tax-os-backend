# Current Status

**Canonical high-level platform status** (TASK-DOC-001).  
For detailed historical sections, see [PROJECT_STATE.md](PROJECT_STATE.md). For task-level tracking, see [TASK_REGISTRY.md](TASK_REGISTRY.md).

**Last realigned:** 2026-06-02  
**Branch:** `main`  
**Alembic head:** `b3d7a9f1c204` (extraction trigger persistence tables)

---

## Current Architecture Phase

**Governed engineering platform — monitoring agent contract gated**

The platform is materially beyond early foundation. Core registry, processing queue, extraction/parser **contracts**, legal-object **persistence**, citation **governance**, temporal **governance**, and ingestion **artifact persistence** are in place on `main`.

**Active gate:** controlled local extraction is now implemented (TASK-006P); PDF/network parsing, legal-object automation, and answer generation remain prohibited.

**Environments:** development and internal staging only. No public production deployment.

---

## Completed Major Milestones

| Layer | Milestone | Tasks / artifacts |
|-------|-----------|-------------------|
| Foundation | Source registry, versioning, migrations, CRUD, storage, upload, processing queue | TASK-001* |
| Extraction contracts | Deterministic text extraction (no AI) | TASK-002A |
| Segmentation / parser contracts | Structural segmentation, section parser, cross-refs | TASK-002B–F, 002E |
| Legal object governance | Extraction, convergence, schema, ORM, migration, repository, integrity | TASK-002G–I, 003A–E |
| Citation governance | Retrieval, effective-date resolver, candidates, assembly + identity hardening | TASK-004A–D, 004D-AMENDMENT-A |
| Temporal governance | Architecture spec, resolution amendments, pre-merge cleanup | TASK-005A-SPEC, 005B, 005C |
| Ingestion persistence | Append-only extraction/parser tables and services | TASK-006A |
| Test hardening | Full-suite stability and fixture isolation discipline | TASK-006B |
| Monitoring governance | Source monitoring agent contract and boundary controls | TASK-006C |
| Fetch governance | Controlled source fetch contract and boundary controls | TASK-006F |
| Change-detection governance | Source change detection engine contract boundaries | TASK-006G |
| Controlled fetch implementation | Dry-run/local-fixture fetchers with safety guards and fixture tests | TASK-006H |
| Controlled fetch persistence | Append-only fetch requests/results with lifecycle metadata persistence | TASK-006I |
| Change-detection persistence | Append-only change-detection requests/results with review doctrine enforcement | TASK-006J |
| Change-detection engine skeleton | Checksum-only persisted-fetch comparison with bounded classifications | TASK-006K |
| Controlled source promotion | Review-gated source version promotion workflow with append-only promotion history | TASK-006L |
| Extraction trigger governance | Source-version extraction trigger contract boundaries | TASK-006M |
| Extraction trigger persistence | Append-only trigger request/result persistence with deterministic hash and idempotency controls | TASK-006N |
| Extraction worker skeleton | Dry-run orchestration from trigger requests to extraction_run lifecycle records | TASK-006O |
| Controlled extraction execution | Local controlled text extraction into extraction_runs and extracted_texts | TASK-006P |

**Checkpoint tags (selected):** `checkpoint-task-003e` … `checkpoint-task-005a-spec`

---

## Temporal Governance Milestone (TASK-005A / 005B / 005C)

**Status:** MERGED / CLOSED on `main` (merge `43c6ad0`, tag `checkpoint-task-005a-spec`)

| Item | Location |
|------|----------|
| Authoritative temporal architecture | [TEMPORAL_VERSIONING_ARCHITECTURE.md](TEMPORAL_VERSIONING_ARCHITECTURE.md) (v1.1.1) |
| Task specs | [TASKS/TASK-005A-*.md](TASKS/), [TASKS/TASK-005B-*.md](TASKS/) |
| Addendum V6 | `tax-os-architecture/ADDENDUMS/ADDENDUM_V6_TEMPORAL_RESOLUTION_AND_VERSION_PINNING.md` |
| Merge record | [MERGE_SUMMARY_TASK-005A.md](MERGE_SUMMARY_TASK-005A.md) |

**Doctrine now canonical:**

* No silent temporal inference
* Explicit version pinning (never assume latest)
* Ambiguity preservation (no silent resolution)
* Derived temporal status (not stored as mutable truth)
* Transaction/applicability date vs knowledge date distinction
* Citation temporal rules at governance level (Addendum V6; C1 resolved in docs)

**TASK-005C:** Pre-merge consistency cleanup (IMP-1–3, IMP-5) — status vocabulary, derived-status matrix, terminology — merged with 005A branch, not a separate implementation track.

---

## Ingestion Persistence Milestone (TASK-006A)

**Status:** IMPLEMENTED / ACCEPTED FOR TARGETED REVIEW (commit `acc32e4`)

* Tables: `extraction_runs`, `extracted_texts`, `parser_runs`, `parsed_structures`, `ingestion_state_transitions`
* Services: `backend/app/services/ingestion/`
* Append-only, failed-run preservation, SHA-256 hashes
* Pipeline artifact states **separate** from `source_versions.ingestion_status` (worker queue)

**Not yet wired:** autonomous workers, ingestion APIs, artifact → legal-object automation.

**Validation:** ingestion tests 12/12 (PostgreSQL VM).

---

## Monitoring Candidate Persistence Milestone (TASK-006D)

**Status:** IMPLEMENTED (commit pending merge on `main`)

* Tables: `source_allowlist_entries`, `monitoring_attempts`, `monitoring_events`, `monitoring_candidates`, `monitoring_candidate_state_transitions`
* Services: `backend/app/services/monitoring/`
* Enforced contracts: allowlist status, attempt status, change type, candidate state, confidence, error categories
* Candidate-state history is append-only with actor/timestamp metadata

**Not implemented:** live monitoring, scraping, schedulers, workers, external traffic, ingestion auto-approval.

---

## Current Approved Task

| Task | Title | Why now |
|------|-------|---------|
| **TASK-006P** | Controlled Extraction Execution | **Completed (controlled local only)** — extracts raw text from approved local artifacts for supported formats; persists extraction_runs and extracted_texts; no PDF/network/parsing/legal automation |

See [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) for full sequencing.

### TASK-006B resequencing (completed)

An earlier roadmap draft labeled **TASK-006B** as *Source Monitoring Agent Contract*. That sequencing is **superseded**.

After TASK-006A, migration and persistence complexity exposed **test instability risk**. **Test stabilization now correctly precedes agent expansion.** TASK-006B is completed and closes TEST-GAP-001.

### TASK-006C boundary

TASK-006C is governance-only:

- allowed: source boundary definitions, allowlist contract, monitoring event contract, candidate-state model, failure model, temporal no-inference alignment
- prohibited: live agents, crawlers, schedulers, scraping, external traffic, automatic production updates

### TASK-006F boundary

TASK-006F is governance-only:

- allowed: fetch request/result contract definitions, status/error taxonomy, content-type/checksum/redirect/security discipline, robots/terms doctrine
- prohibited: live HTTP requests, crawler/scraper implementation, storage implementation, automated source version creation, ingestion automation

### TASK-006G boundary

TASK-006G is governance-only:

- allowed: change-detection request/result contracts, status/change/confidence taxonomy, checksum/metadata/structural diff doctrine, review-required policy
- prohibited: diff engine implementation, legal amendment inference, temporal inference, automatic source version creation

### TASK-006H boundary

TASK-006H implements bounded fetch execution only:

- allowed: `DryRunFetcher`, `LocalFixtureFetcher`, local fixture path safety, checksum/content-type utilities, max-size guard, dry-run/local-mode guard
- prohibited: live HTTP/HTTPS fetching, crawling/scraping, source discovery, source-version creation, legal-object creation, ingestion approval automation

### TASK-006I boundary

TASK-006I implements bounded fetch persistence only:

- allowed: append-only `fetch_requests`/`fetch_results` persistence, enum validation, FK integrity to monitoring candidate/allowlist, latest-result retrieval
- prohibited: source version creation, extracted text creation, legal object creation, monitoring candidate auto-approval/state transition, live external fetching

### TASK-006J boundary

TASK-006J implements bounded change-detection persistence only:

- allowed: append-only `change_detection_requests`/`change_detection_results` persistence, enum validation, FK integrity to candidate/fetch/source entities, review-required doctrine validation
- prohibited: change-detection engine algorithms, amendment/legal/temporal inference, source-version creation, candidate auto-transition/approval, live external fetching

### TASK-006K boundary

TASK-006K implements bounded checksum-only detection execution:

- allowed: persisted `fetch_results` checksum comparison, bounded outcomes (`new_artifact`, `no_change`, `checksum_changed`, `unknown`), persistence via TASK-006J services
- prohibited: textual/metadata/structural diff engines, amendment/legal/temporal inference, source-version creation, legal-object creation, candidate auto-transition/approval, live external fetching

### TASK-006L boundary

TASK-006L implements bounded source-version promotion workflow:

- allowed: explicit workflow validation, duplicate protection, canonical `source_versions` creation from reviewed artifacts, append-only `source_version_promotions` history
- prohibited: automatic ingestion/extraction/parsing/legal-object/citation creation, amendment/legal/temporal inference, autonomous approval/publication

### TASK-006P boundary

TASK-006P is controlled local extraction only:

- allowed: approved artifact-root reads, supported text formats (plain/html/json/xml), extraction_run + extracted_text persistence, trigger lifecycle results, idempotency and force-reprocess paths, dry-run mode preserved
- prohibited: PDF/OCR, network fetch, browser automation, legal structure parsing, legal_object/citation/answer creation, temporal/amendment inference

---

## Deferred Tasks

| Task | Title | Status | Reason |
|------|-------|--------|--------|
| **TASK-004E** | Citation Temporal Compliance Remediation | **DEFERRED / TRACKED** | Known bounded gap: `CitationAssembler` date fallback vs Addendum V6. Not blocking ingestion pipeline. Spec: [TASKS/TASK-004E-CITATION-TEMPORAL-COMPLIANCE-REMEDIATION.md](TASKS/TASK-004E-CITATION-TEMPORAL-COMPLIANCE-REMEDIATION.md). Tracked as OD-016. |

Do not implement TASK-004E unless it blocks active work.

---

## Known Gaps

| ID | Gap | Impact | Owner task |
|----|-----|--------|------------|
| **TEST-GAP-001** | Full-suite instability in legal-object integrity / retrieval tests during 006A validation | **Resolved in TASK-006B** (root-cause isolated and fixed) | Closed |
| **OD-016** | Citation assembler temporal code vs governance | Citation output may not match Addendum V6 until TASK-004E | TASK-004E (deferred) |
| **OD-017 / OD-018** | 003E reconciliation, overlap disclosure | Non-blocking governance follow-ups | Future review |

Ingestion workers, live monitoring agents, live fetchers, change-detection engines, scraping, embeddings, answer engine, public ingestion APIs: **not started** (by design).

## Monitoring Worker Skeleton Milestone (TASK-006E)

**Status:** IMPLEMENTED (dry-run mode only)

* Worker modules: `backend/app/workers/monitoring/`
* Components: `SourceMonitoringWorker`, `MonitoringProvider` interface, `DryRunMonitoringProvider`, `run_monitoring_dry_run()`
* Lifecycle path: allowlist -> attempt -> synthetic event -> candidate -> transition history
* Safety guard: non-dry-run execution is rejected
* No external HTTP/crawler/scraper behavior introduced

---

## Governance Status

| Area | Status |
|------|--------|
| Architecture repo | Authoritative for addenda and cross-repo doctrine |
| Task specs | `TASKS/TASK-<ID>-*.md` required for review |
| Task tracking | [TASK_REGISTRY.md](TASK_REGISTRY.md) |
| Open decisions | [OPEN_DECISIONS.md](OPEN_DECISIONS.md) |
| Temporal architecture | [TEMPORAL_VERSIONING_ARCHITECTURE.md](TEMPORAL_VERSIONING_ARCHITECTURE.md) |
| Implementation sequencing | [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) |
| Phase evolution map | [ARCHITECTURE_PHASE_MAP.md](ARCHITECTURE_PHASE_MAP.md) |

---

## Merge Stability Status

| Item | Status |
|------|--------|
| `main` | TASK-006A + governance closeout pushed |
| Last major merge | TASK-005A temporal governance (`43c6ad0`, `--no-ff`) |
| Checkpoint tags | Through `checkpoint-task-005a-spec` |
| Test confidence | **Green (stabilized)** — full suite passed 3 consecutive runs (390/390) |

---

## Stabilization Priorities

1. Keep `TEST_DATABASE_URL` safety guard enabled for destructive integration workflows
2. Preserve nested-transaction isolation in `backend/tests/conftest.py`
3. Re-run full suite before migration-heavy tasks

---

## Next Major Architectural Goal

After TASK-006P controlled extraction execution: Claude architecture review checkpoint is now appropriate before further canonical-ingestion expansion.

Longer horizon (not approved for immediate implementation): agent layer → retrieval layer → answer assembly. See [ARCHITECTURE_PHASE_MAP.md](ARCHITECTURE_PHASE_MAP.md).

---

## Architectural Sequencing (summary)

```text
FOUNDATION → EXTRACTION CONTRACTS → LEGAL OBJECT GOVERNANCE → CITATION GOVERNANCE
→ TEMPORAL GOVERNANCE → INGESTION PERSISTENCE → [TEST HARDENING] → AGENT LAYER → …
```

**You are here:** ingestion persistence complete, test hardening complete, monitoring governance + persistence + dry-run worker skeleton + fetch governance + detection governance + controlled local fetch execution + fetch persistence + change-detection persistence + checksum-only detection engine skeleton + controlled source-version promotion + extraction-trigger governance + extraction-trigger persistence + extraction worker skeleton + controlled local extraction execution complete (TASK-006C–006P).
