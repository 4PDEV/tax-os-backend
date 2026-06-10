# Ranking Layer Review (TASK-008A+)

**Review type:** Governance review only — no implementation  
**Date:** 2026-06-02  
**Baseline:** `b417746` · tag `v0.1.5-ranking-worker-skeleton`  
**Scope:** Retrieval result → retrieval evidence references → ranking persistence (008C) → controlled ranking execution (008D) → ranking worker skeleton (U-01)  
**Locked decisions:** DEC-010, DEC-011, DEC-012, OD-021  
**Verdict:** **ACCEPTED**

---

## Executive summary

The ranking layer is **accepted as a governed platform layer**. The pipeline from completed retrieval through append-only ranking persistence, mechanical controlled execution, and single-worker orchestration is **architecturally sound, contract-aligned, and boundary-bounded**.

**Ranking chain delivered:**

```text
retrieval_result (completed, result_count=N)
  → retrieval_evidence_references (provenance-once, deterministic_order_index)
  → ranking_request (ranking_request_hash idempotency)
  → ranking_result (accepted)
  → [mechanical permutation by ranking_profile]
  → ranked_evidence_references (pure-pointer, presentation_order_index)
  → ranking_result (completed | failed)
  → [U-01] run_ranking_worker → execute_controlled_ranking (delegation only)
```

**Mandatory doctrines enforced:**

| Boundary | Status |
|----------|--------|
| `retrieval result` ≠ ranking | Ranking reads completed retrieval only; never mutates retrieval rows |
| `ranking` ≠ answer | No answer text, citation synthesis, or legal conclusions |
| Provenance lives once (DEC-010) | Ranked rows are pure pointers; sort-time reads are in-memory only |
| Mechanical permutation only (DEC-012) | Four closed profiles; no scores or AI/semantic/vector ranking |
| Single-worker (OD-021) | Worker mutex + in-flight accepted guard |

**Result:** Ranking layer **COMPLETE**. TASK-009A **pre-authorization may proceed** (governance review only — implementation remains **NOT AUTHORIZED** until explicit 009A authorization).

---

## Layer status (canonical)

| Layer | Task(s) | Status |
|-------|---------|--------|
| Ranking runtime contract | 008B | **COMPLETE** |
| Ranking persistence remediation | 008C-REMEDIATION | **COMPLETE** |
| Ranking persistence | 008C | **COMPLETE** / **ACCEPTED** — `a8c1e4f92b37`, `v0.1.3` |
| Ranking execution pre-auth | 008D-PREAUTH | **COMPLETE** / **ACCEPTED** — DEC-012 |
| Ranking execution authorization | 008D-IMPL-AUTH | **COMPLETE** |
| Controlled ranking execution | 008D | **COMPLETE** / **ACCEPTED** — `v0.1.4` |
| Ranking worker skeleton | U-01 | **COMPLETE** / **ACCEPTED** — `v0.1.5` |
| **Ranking layer review** | 008A+ | **CLOSED** — **ACCEPTED** |

---

## Review areas (RL-01 through RL-10)

### RL-01 — Retrieval → ranking boundary

| Check | Evidence | Status |
|-------|----------|--------|
| Ranking never changes retrieval results | `execute_controlled_ranking` reads via `get_result` / `list_evidence_references` only; no retrieval persistence imports for writes | **PASS** |
| Ranking never changes evidence membership | Permutation validation (P-01–P-09) enforces identical multiset of `retrieval_evidence_reference_id` | **PASS** |
| Ranking consumes completed retrieval only | V-02 `retrieval_status=completed`; V-03 `result_count` non-null; V-04 evidence count match | **PASS** |

**Files:** `ranking_execution/validation.py` (V-01–V-08), `retrieval_persistence/persistence.py` (read APIs only from ranking path).

---

### RL-02 — Provenance integrity (DEC-010)

| Check | Evidence | Status |
|-------|----------|--------|
| Provenance stored once | Full provenance on `retrieval_evidence_references` only | **PASS** |
| No provenance copied onto ranked rows | `RankedEvidenceReference` ORM: 5 pointer columns + `created_at`; `PROHIBITED_TABLE_COLUMNS` in validation; migration has no interpretive columns | **PASS** |
| Ranking reads provenance only | `RankingEvidenceRow` is in-memory sort input (`models.py` docstring); `load_evidence_rows` reads retrieval + `LegalObjectVersion.effective_from` for sort keys only | **PASS** |

**Structural enforcement:** composite FK `fk_ranked_evidence_composite_membership` on `(retrieval_result_id, retrieval_evidence_reference_id)`.

---

### RL-03 — Permutation integrity

| Check | Evidence | Status |
|-------|----------|--------|
| Input evidence set == output evidence set | `validate_permutation` P-03 multiset, P-04 set, P-05/P-06 membership | **PASS** |
| `rank_count` consistency | `rank_count=n` on completed; zero-evidence → `rank_count=0`; tests assert ranked row count | **PASS** |
| No evidence loss / duplication | P-07 contiguous indices 1..N; P-08/P-09 slot and duplicate rank guards; DB `uq_ranked_evidence_result_evidence` | **PASS** |

---

### RL-04 — Determinism (DEC-012)

| Check | Evidence | Status |
|-------|----------|--------|
| Same retrieval + profile + contract_version ⇒ same permutation | `test_determinism_same_inputs_same_order`; stable sort keys with explicit nulls-last tie-breakers | **PASS** |
| CANONICAL | `sort_canonical` by `deterministic_order_index` | **PASS** |
| EFFECTIVE_DATE_DESC | `_effective_date_desc_key` + within-group tie-breakers | **PASS** |
| GROUP_BY_SOURCE | `source_version_id` primary key + `_within_group_key` | **PASS** |
| GROUP_BY_DOCUMENT | `source_document_id` nulls-last + `_within_group_key` | **PASS** |

All four profiles covered by unit tests in `test_controlled_ranking_execution.py`.

---

### RL-05 — Replay / idempotency (DEC-011)

| Layer | Behaviour | Status |
|-------|-----------|--------|
| Persistence | `compute_ranking_request_hash`; partial unique `uq_ranking_requests_hash_default` WHERE `force_replay=false`; `force_replay` + `replay_nonce` entropy | **PASS** |
| Execution | Pre-check duplicate default hash; `force_replay` bypasses duplicate rejection; in-flight `accepted` guard | **PASS** |
| Worker | Passes `force_replay` / `replay_nonce`; requires nonce when `force_replay=true` | **PASS** |

Tests: `test_duplicate_default_request_rejected`, `test_force_replay_allows_second_execution`, `test_replay_hash_differs_with_nonce`, `test_in_flight_accepted_guard`.

---

### RL-06 — Failure model

| Layer | Vocabulary | Status |
|-------|------------|--------|
| Persistence | 9 canonical categories in `RANKING_ERROR_CATEGORIES`; 4 prohibited categories rejected; DB check constraints mirror validation | **PASS** |
| Execution | `RankingExecutionError(category, message)` maps to persisted `error_category`; zero-evidence uses `completed` not `evidence_set_empty` | **PASS** |
| Worker | Maps execution outcomes to `QUEUE_LIFECYCLE_COMPLETED` / `FAILED`; propagates `error_category` on failed outcomes | **PASS** |

**Note (RL-O-03):** Pre-validation failures raised through worker as `RankingWorkerError` embed category in message string; structured `error_category` on `RankingWorkerOutcome` applies to execution-returned failures only. Non-blocking for skeleton; 009A pre-auth should document consumer error handling.

---

### RL-07 — Single-worker doctrine (OD-021)

| Layer | Mechanism | Status |
|-------|-----------|--------|
| Execution | In-flight guard: duplicate default hash + existing `accepted` result → `duplicate_ranking` | **PASS** |
| Worker | `_execution_lock` non-blocking acquire; concurrent call raises OD-021 message | **PASS** |
| Persistence | Documented OD-021 assumption; no concurrent worker infrastructure | **PASS** |

**Note (RL-O-02):** Process-level mutex is worker-scoped only. Direct `execute_controlled_ranking` calls bypass the threading lock (hash/in-flight guards still apply). Acceptable for current skeleton; multi-process concurrency requires future governance gate.

---

### RL-08 — Layer boundaries

| Layer | Responsibility | Leakage scan | Status |
|-------|----------------|--------------|--------|
| `ranking_persistence` | Append-only storage (`create_*` only; no update/delete) | No execution, ordering, or worker logic | **PASS** |
| `ranking_execution` | Mechanical permutation + validation | Writes only via `ranking_persistence`; no worker/API imports | **PASS** |
| `ranking_runtime` worker | Orchestration envelope | Delegates to `execute_controlled_ranking`; forbidden token/import tests | **PASS** |

---

### RL-09 — Forbidden capability scan

| Capability | Scan result | Status |
|------------|-------------|--------|
| Answer generation | Absent across ranking persistence, execution, worker | **PASS** |
| Citation synthesis | No `CitationAssembler` imports; worker import guard | **PASS** |
| Legal conclusions | No prohibited columns or fields | **PASS** |
| AI / semantic / vector ranking | Absent; no score columns persisted | **PASS** |
| Retrieval re-selection | Read-only evidence load; no retrieval execution imports | **PASS** |
| Concurrent workers | Worker rejects; not implemented in broker layer | **PASS** |
| Queue infrastructure | Documented lifecycle constants only (U-01) | **PASS** |
| APIs | No ranking HTTP routes in scope | **PASS** |

---

### RL-10 — Readiness for TASK-009A pre-authorization

| Criterion | Assessment |
|-----------|------------|
| End-to-end chain complete | Retrieval → persistence → execution → worker verified |
| Contracts aligned with implementation | `RANKING_RUNTIME_CONTRACT.md`, `RANKING_EXECUTION_CONTRACT.md`, DEC-010/011/012 |
| Test coverage | Persistence, execution (unit + integration), worker skeleton tests; boundary/leakage guards |
| Stable extension surface | Pure-pointer ranked rows + `presentation_order_index` provide deterministic handoff to answer assembly |
| Open risks documented | RL-O-01 through RL-O-04 (non-blocking) |

**Assessment:** Ranking layer is **stable enough** for TASK-009A **pre-authorization review** to begin. TASK-009A **implementation** remains **NOT AUTHORIZED**.

---

## Findings register

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| RL-01 | Retrieval boundary — read-only consumption of completed retrieval | Required | **VERIFIED** |
| RL-02 | Provenance-once / pure-pointer ranked rows (DEC-010) | Required | **VERIFIED** |
| RL-03 | Permutation integrity P-01–P-09 | Required | **VERIFIED** |
| RL-04 | Determinism across four profiles (DEC-012) | Required | **VERIFIED** |
| RL-05 | Replay/idempotency consistency (DEC-011) | Required | **VERIFIED** |
| RL-06 | Canonical error vocabulary (9 categories) | Required | **VERIFIED** |
| RL-07 | OD-021 single-worker doctrine | Required | **VERIFIED** |
| RL-08 | Layer boundary separation | Required | **VERIFIED** |
| RL-09 | Forbidden capabilities absent | Required | **VERIFIED** |
| RL-10 | 009A pre-auth readiness | Required | **VERIFIED** |

**No blocking findings. No remediation required.**

---

## Non-blocking observations

| ID | Observation | Impact | Remediation |
|----|-------------|--------|-------------|
| RL-O-01 | Ranked evidence rows attach to `ranking_result` with `ranking_status=accepted`; terminal `completed`/`failed` row is a separate append-only lifecycle row. `RankingExecutionOutcome.ranking_result_id` and worker outcome return the **terminal** row ID. | Downstream consumers must resolve ranked rows via `ranking_request_id` → accepted result, or document lookup convention in 009A contract. | Document in TASK-009A pre-auth; no code change required |
| RL-O-02 | OD-021 threading lock is worker-only; direct execution entry bypasses mutex. | Multi-threaded direct calls could race before hash persistence. | Future concurrency gate; acceptable for skeleton |
| RL-O-03 | Worker exception path uses `RankingWorkerError` string messages for pre-validation failures. | Callers parsing exceptions vs outcomes differ. | 009A orchestration contract should specify outcome-first handling |
| RL-O-04 | Append-only lifecycle yields multiple `ranking_results` per request (`accepted` + terminal). | Consumers must not assume single result row per request. | Already in `RANKING_EXECUTION_CONTRACT.md` §6 |

---

## Architectural risks (monitoring)

| Risk | Likelihood | Mitigation in place |
|------|------------|---------------------|
| Answer layer reads wrong `ranking_result_id` | Medium at integration | RL-O-01; contract documents accepted-row attachment |
| Bypass worker OD-021 via direct execution | Low in governed deployments | Hash dedup + in-flight accepted guard |
| Profile drift vs contract | Low | Closed set in DB check constraints + validation |
| Provenance duplication creep | Low | `PROHIBITED_TABLE_COLUMNS` tests + pure-pointer ORM |

---

## Gate closure record

| Item | Status |
|------|--------|
| TASK-008C ranking persistence | **CLOSED** — **ACCEPTED** |
| TASK-008D controlled ranking execution | **CLOSED** — **ACCEPTED** |
| U-01 ranking worker skeleton | **CLOSED** — **ACCEPTED** |
| Ranking layer review (008A+) | **CLOSED** — **ACCEPTED** |
| Ranking layer phase | **COMPLETE** |
| TASK-009A pre-authorization | **AUTHORIZED TO BEGIN** (governance only) |
| TASK-009A implementation | **NOT AUTHORIZED** |
| AI / semantic / vector ranking | **NOT AUTHORIZED** |
| Concurrent ranking workers | **NOT AUTHORIZED** (OD-021) |
| Ranking APIs / queue infrastructure | **NOT AUTHORIZED** |

---

## Next valid gate

**TASK-009A — Answer Assembly Pre-Authorization Review** — governance review only. No answer runtime code, citation assembly implementation, APIs, or legal-conclusion logic until explicit implementation authorization following pre-auth acceptance.

---

## Files inspected

| Area | Paths |
|------|-------|
| Retrieval persistence | `backend/app/services/retrieval_persistence/`, `backend/app/models/retrieval_*.py` |
| Ranking persistence | `backend/app/services/ranking_persistence/`, `backend/app/models/ranking_*.py`, `backend/app/models/ranked_evidence_reference.py`, `backend/migrations/versions/a8c1e4f92b37_*.py` |
| Ranking execution | `backend/app/services/ranking_execution/` |
| Ranking worker | `backend/app/workers/ranking_runtime/` |
| Tests | `backend/tests/test_ranking_persistence.py`, `test_controlled_ranking_execution.py`, `test_ranking_worker_skeleton.py` |
| Governance | `RANKING_RUNTIME_CONTRACT.md`, `RANKING_EXECUTION_CONTRACT.md`, `DECISION_LOG.md` |

---

## Review verdict

**ACCEPTED**

The complete retrieval → persistence → execution → worker ranking chain satisfies all ten required review areas. Non-blocking observations RL-O-01 through RL-O-04 require no remediation before TASK-009A pre-authorization begins.
