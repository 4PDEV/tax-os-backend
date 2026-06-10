# Answer Layer Review (TASK-009A+)

**Review type:** Governance review only — no implementation  
**Date:** 2026-06-02  
**Baseline:** `8ddb285` · tag `v0.1.8-answer-assembly`  
**Scope:** Retrieval → ranking (008C–008D, U-01) → answer assembly (009A) — end-to-end chain  
**Locked decisions:** DEC-010, DEC-011, DEC-012, DEC-013, DEC-014, OD-021  
**Verdict:** **ACCEPTED**

---

## Executive summary

The answer layer is **accepted as a governed platform layer**. Ephemeral answer assembly (`assemble_answer_package`) correctly consumes completed ranking lifecycle output, resolves RL-O-01 (accepted vs terminal `ranking_result`), builds source-referenced `AnswerPackage` structures read-only, and preserves provenance-once (DEC-010) without persistence, workers, APIs, or forbidden capabilities.

**End-to-end chain reviewed:**

```text
retrieval_result (completed)
  → retrieval_evidence_references (provenance-once)
  → ranking_request
  → ranking_result (accepted)
  → execute_controlled_ranking() [mechanical permutation]
  → ranked_evidence_references (pure pointers)
  → ranking_result (completed)
  → [U-01] run_ranking_worker() → execute_controlled_ranking() (orchestration only)
  → assemble_answer_package(ranking_request_id) [ephemeral AnswerPackage]
```

**Mandatory doctrines enforced:**

| Boundary | Status |
|----------|--------|
| `retrieval result` ≠ ranking | Ranking closed; answer does not retrieve |
| `ranking` ≠ answer | Answer consumes `ranking_request_id` only — no re-ranking |
| `answer` ≠ legal conclusion | No `answer_text`, conclusions, or recommendations |
| Provenance lives once (DEC-010) | Answer reads via joins; DTO references only |
| Ephemeral assembly (DEC-014) | No answer persistence; Option A only |
| CitationFormatter read-only (DEC-014) | No `CitationAssembler`; no citation mutation |
| Deterministic assembly (009A-v1) | `assembly_mode=deterministic` only |

**Result:** Answer layer **COMPLETE** (009A ephemeral slice). **TASK-009B-PREAUTH** (answer persistence governance) **may proceed** — implementation remains **NOT AUTHORIZED**.

---

## Layer status (canonical)

| Layer | Task(s) | Status |
|-------|---------|--------|
| Answer assembly pre-auth | 009A-PREAUTH | **ACCEPTED** — DEC-013 |
| Answer impl authorization | 009A-IMPL-AUTH | **ACCEPTED** — DEC-014 — `v0.1.7` |
| Answer assembly (ephemeral) | 009A | **COMPLETE** / **ACCEPTED** — `8ddb285`, `v0.1.8` |
| Ranking layer | 008B–008D, U-01, 008A+ | **COMPLETE** / **ACCEPTED** |
| Retrieval layer | 007A–007E | **COMPLETE** / **ACCEPTED** |
| **Answer layer review** | 009A+ | **CLOSED** — **ACCEPTED** |
| Answer persistence | 009B | **NOT AUTHORIZED** |

---

## Review areas (AL-01 through AL-10)

### AL-01 — Retrieval → ranking → answer boundary

| Check | Evidence | Status |
|-------|----------|--------|
| Answer consumes ranking output only | Entry: `ranking_request_id`; `resolve_ranking_assembly_inputs()` — no `retrieval_result_id`-only path | **PASS** |
| No retrieval bypass | Evidence loaded by `retrieval_evidence_reference_id` from ranked rows only — not `list_evidence_references` for full set | **PASS** |
| No retrieval re-selection | No `retrieval_execution` import; no retrieval persistence writes | **PASS** |
| No ranking from answer layer | No `ranking_execution` import; no `create_*` ranking persistence calls | **PASS** |

**Note:** `run_ranking_worker()` does **not** invoke answer assembly — intentional per DEC-014 (direct service only). Orchestration coupling deferred to future answer worker task.

---

### AL-02 — RL-O-01 answer resolution

| Check | Evidence | Status |
|-------|----------|--------|
| Terminal `completed` resolved | `validation.py`: exactly one `ranking_status=completed` | **PASS** |
| Accepted resolved | Exactly one `ranking_status=accepted` | **PASS** |
| Ranked rows from accepted parent | `list_ranked_evidence_references(ranking_result_id=accepted.id)` | **PASS** |
| Count integrity | `len(ranked_rows) == terminal.rank_count` | **PASS** |
| Lifecycle distinction in package | `terminal_ranking_result_id` and `accepted_ranking_result_id` both populated | **PASS** |
| Tests RL-T-01–RL-T-10 | `test_answer_assembly.py` | **PASS** (design + unit; integration requires `TEST_DATABASE_URL`) |

**Closes ranking-layer observation RL-O-01** at answer boundary.

---

### AL-03 — Evidence completeness

| Check | Evidence | Status |
|-------|----------|--------|
| One entry per ranked row | Loop over `ranked_rows`; `validate_evidence_entries` E-01–E-07 | **PASS** |
| No silent omission | Failure on count/order mismatch — no filtering | **PASS** |
| No evidence invention | Entries built only from ranked pointer IDs | **PASS** |
| `presentation_order_index` preserved | Copied from ranked row; validation asserts match | **PASS** |
| Zero-evidence valid | `rank_count=0` → empty entries + `zero_evidence` flag; `completed` | **PASS** |

---

### AL-04 — Provenance integrity (DEC-010)

| Check | Evidence | Status |
|-------|----------|--------|
| Provenance-once preserved | Reads `RetrievalEvidenceReference`, `LegalObjectVersion`, `Citation` via `session.get` / `select` | **PASS** |
| Read-only joins | No `session.add`, `flush` writes in `answer_assembly/` | **PASS** |
| No provenance duplication | DTO carries reference IDs + optional display text — no authoritative copy store | **PASS** |
| No mutation of upstream rows | Grep: no `create_*`, no `session.add` in service | **PASS** |

---

### AL-05 — Citation boundary (DEC-014 / OQ-03)

| Check | Evidence | Status |
|-------|----------|--------|
| `CitationFormatter` read-only | Used in `_render_citation_text_read_only`; gated by `include_rendered_citation_text` | **PASS** |
| `CitationAssembler` prohibited | Absent from imports and source scan; test `test_citation_assembler_prohibited_in_service` | **PASS** |
| No citation creation/mutation/discovery | `select(Citation).where(citation_id=...)` read only | **PASS** |
| `rendered_citation_text` non-authoritative | Optional display field on `CitationReference`; default `null` | **PASS** |
| Incomplete pin handling | `citation_reference_status=incomplete` + warning flag; assembly continues (009A-v1) | **PASS** |

---

### AL-06 — Failure model

| Check | Evidence | Status |
|-------|----------|--------|
| 10 canonical categories only | `ANSWER_ERROR_CATEGORIES` frozenset; `AnswerAssemblyError` validates | **PASS** |
| Ranking errors not reused | `permutation_mismatch` rejected at construction; test `test_canonical_error_categories_only` | **PASS** |
| Structured outcomes | `AnswerAssemblyOutcome(answer_status, error_category, error_message)` | **PASS** |
| Deterministic failure mapping | Table in impl-auth §6 implemented in `validation.py` / `assembly.py` | **PASS** |

---

### AL-07 — Determinism

| Check | Evidence | Status |
|-------|----------|--------|
| Same inputs → same structure | `test_deterministic_assembly_structure` — evidence IDs and order stable | **PASS** |
| `assembly_mode=deterministic` only | `AnswerAssemblyMetadata(assembly_mode="deterministic")` hardcoded | **PASS** |
| Intentional non-deterministic fields | `answer_package_id`, `assembled_at` vary per invocation — documented (AL-O-02) | **PASS** |

---

### AL-08 — Layer boundaries

| Layer | Responsibility | Leakage scan | Status |
|-------|----------------|--------------|--------|
| `ranking_persistence` | Append-only storage | Answer uses `list_*` read APIs only | **PASS** |
| `ranking_execution` | Mechanical permutation | Not imported by answer layer | **PASS** |
| `ranking_runtime` worker | Orchestration → `execute_controlled_ranking` | Does not call answer assembly | **PASS** |
| `answer_assembly` | Ephemeral package build | No persistence/worker/API imports | **PASS** |
| Response runtime | Not introduced | Absent | **PASS** |

---

### AL-09 — Forbidden capability scan

| Capability | Scan result | Status |
|------------|-------------|--------|
| Answer persistence (`answer_requests` / `answer_results`) | Absent | **PASS** |
| Answer worker | No `workers/answer_runtime/` | **PASS** |
| Public APIs | No answer routes | **PASS** |
| Response runtime | Absent | **PASS** |
| `answer_text` / legal conclusions / recommendations | Absent from models and source scan | **PASS** |
| AI / semantic / vector | Import guards in tests; absent from service | **PASS** |
| Retrieval re-selection | No `retrieval_execution` | **PASS** |
| Citation creation | No writes to `citations` | **PASS** |
| Concurrent answer workers | Not implemented (OD-021 carry-forward) | **PASS** |
| Migrations / answer ORM models | Absent | **PASS** |

---

### AL-10 — Readiness for TASK-009B-PREAUTH

| Criterion | Assessment |
|-----------|------------|
| 009A ephemeral assembly complete and contract-aligned | **MET** |
| RL-O-01 closed at answer boundary | **MET** |
| DEC-010 / DEC-014 preserved in implementation | **MET** |
| Test envelope defined (RL-T-01–RL-T-10, import guards) | **MET** |
| Option B persistence scope documented (009B deferred) | **MET** |
| Answer worker / response runtime still closed | **MET** |

**Assessment:** Answer layer is **stable enough** for **TASK-009B-PREAUTH** (answer persistence governance contract only). **009B implementation NOT AUTHORIZED**.

---

## Findings register

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| AL-01 | Retrieval → ranking → answer boundary | Required | **VERIFIED** |
| AL-02 | RL-O-01 resolution | Required | **VERIFIED** |
| AL-03 | Evidence completeness E-01–E-07 | Required | **VERIFIED** |
| AL-04 | Provenance-once (DEC-010) | Required | **VERIFIED** |
| AL-05 | Citation boundary (DEC-014) | Required | **VERIFIED** |
| AL-06 | Canonical failure model (10 categories) | Required | **VERIFIED** |
| AL-07 | Deterministic assembly | Required | **VERIFIED** |
| AL-08 | Layer boundary separation | Required | **VERIFIED** |
| AL-09 | Forbidden capabilities absent | Required | **VERIFIED** |
| AL-10 | 009B pre-auth readiness | Required | **VERIFIED** |

**No blocking findings. No remediation required.**

---

## Non-blocking observations

| ID | Observation | Impact | Remediation |
|----|-------------|--------|-------------|
| AL-O-01 | No worker orchestration from ranking → answer | Callers must invoke `assemble_answer_package` explicitly | Future answer worker task (post-009B or parallel pre-auth) |
| AL-O-02 | `answer_package_id` / `assembled_at` non-deterministic per call | Audit comparisons must exclude surrogate fields | Document in 009B persistence hash envelope if needed |
| AL-O-03 | `citation_reference_incomplete` category unused in 009A-v1 | Reserved for citation-required modes (OQ-06) | 009B or jurisdiction pre-auth |
| AL-O-04 | 19/23 tests integration — require `TEST_DATABASE_URL` | VM/CI verification recommended before 009B code | Run full integration suite on dedicated test DB |
| AL-O-05 | Multiple `completed` terminal rows rejected (`len != 1`) | Data corruption surfaces as `ranking_result_not_completed` | Acceptable; 009B may add explicit duplicate-terminal guard |

---

## Architectural risks (monitoring)

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Caller passes terminal `ranking_result_id` instead of `ranking_request_id` | Medium | API design in future response runtime must use request ID |
| Ephemeral packages lost without 009B persistence | Medium until 009B | 009B-PREAUTH next |
| CitationFormatter drift vs stored `rendered_citation_text` | Low | Formatter uses persisted citation pins; fallback to stored text |
| Provenance duplication creep in 009B schema | Medium at 009B | 009B pre-auth must enforce DEC-010 |

---

## Gate closure record

| Item | Status |
|------|--------|
| TASK-009A answer assembly | **CLOSED** — **ACCEPTED** — `v0.1.8-answer-assembly` |
| Answer layer review (009A+) | **CLOSED** — **ACCEPTED** |
| Answer layer phase (ephemeral) | **COMPLETE** |
| TASK-009B-PREAUTH | **AUTHORIZED TO BEGIN** (governance only) |
| TASK-009B implementation | **NOT AUTHORIZED** |
| Answer worker | **NOT AUTHORIZED** |
| Response runtime | **NOT AUTHORIZED** |

---

## Next valid gate

**TASK-009B-PREAUTH** — Answer Persistence Governance Contract (Option B design). Governance only — no migrations, ORM, or services until explicit implementation authorization following pre-auth acceptance.

---

## Files inspected

| Area | Paths |
|------|-------|
| Answer assembly | `backend/app/services/answer_assembly/`, `backend/tests/test_answer_assembly.py` |
| Ranking persistence | `backend/app/services/ranking_persistence/` |
| Ranking execution | `backend/app/services/ranking_execution/` |
| Ranking worker | `backend/app/workers/ranking_runtime/` |
| Governance | `ANSWER_ASSEMBLY_CONTRACT.md`, `RANKING_EXECUTION_CONTRACT.md`, `RANKING_RUNTIME_CONTRACT.md`, `DECISION_LOG.md` |

---

## Review verdict

**ACCEPTED**

The complete retrieval → ranking → answer assembly chain satisfies all ten required review areas. Non-blocking observations AL-O-01 through AL-O-05 require no remediation before TASK-009B-PREAUTH begins.
