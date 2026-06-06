# TASK-008A1 Acceptance Review — Ranking Runtime Remediation

**Review type:** Remediation acceptance — authorizes **TASK-008B** ranking runtime contract scope only  
**Date:** 2026-06-02  
**Closure date:** 2026-06-02  
**Authority:** [`RANKING_RUNTIME_REMEDIATION_008A1.md`](RANKING_RUNTIME_REMEDIATION_008A1.md), TASK-008A Ranking Runtime Pre-Authorization Review

**Verdict:** **CLOSED** — **ACCEPTED** — **TASK-008B AUTHORIZED WITH CONDITIONS**

---

## Findings closed

| ID | Finding | Status |
|----|---------|--------|
| RK-01 | Layer boundary — ranking vs retrieval ordering profiles | **CLOSED** — Option A selected |
| RK-02 | `ranking_request_hash` identity | **CLOSED** |
| RK-03 | Completed `retrieval_result` prerequisite | **CLOSED** |
| RK-04 | Permutation invariant | **CLOSED** |
| RK-05 | Read-only provenance | **CLOSED** |
| RK-06 | Append-only persistence doctrine | **CLOSED** |
| RK-07 | No score columns | **CLOSED** |
| RK-08 | No relevance / semantic / AI inputs | **CLOSED** |
| RK-09 | No answer generation | **CLOSED** |
| RK-10 | Mechanical leakage guards | **CLOSED** |
| RK-11 | OD-021 concurrent workers | **CLOSED** — carried forward |

---

## RK-01 decision (accepted)

### Option A — separate ranking layer — **SELECTED**

```text
retrieval_result (completed)
  → ranking_request
  → ranking_result
  → ranked_evidence_reference
```

### Option B — retrieval ordering profiles — **REJECTED**

Profiles such as `CANONICAL`, `EFFECTIVE_DATE_DESC`, `GROUP_BY_SOURCE`, `GROUP_BY_DOCUMENT` must **not** live inside retrieval execution. They are **mechanical ranking profiles** in a distinct governed layer.

### Rationale (accepted)

| Dimension | Rationale |
|-----------|-----------|
| **Doctrine preservation** | Architecture chain Evidence → Ranking → Answer Assembly requires a separable ranking lifecycle. `retrieval result ≠ ranking` is structurally enforceable only when retrieval output is immutable and ranking applies presentation permutations downstream. |
| **Provenance preservation** | `retrieval_evidence_references` remain immutable. `ranked_evidence_reference` rows reference source evidence by FK — no version re-resolution, no citation creation, no temporal re-filtering. |
| **Auditability** | Operators can distinguish “evidence set produced” (`retrieval_result` + `result_count`) from “presentation order applied” (`ranking_result` + `rank_count`). Separate `ranking_request_hash` namespace. |
| **Creep risk** | Option B invites relevance/AI features as “ordering profiles.” Option A makes scope expansion visible at ranking gates. |

Retrieval layer (007A–007E) remains **closed** and **unchanged**.

---

## Platform state after acceptance

| Layer / capability | Status |
|--------------------|--------|
| Extraction (006M–006P1) | **COMPLETE** |
| Parsing (006Q–006T1A) | **COMPLETE** |
| Legal object layer (006U–006X1) | **COMPLETE** |
| Citation layer (006Y–006AD) | **COMPLETE** |
| Retrieval layer (007A–007E) | **COMPLETE** |
| Ranking runtime design (008A1) | **COMPLETE** |
| **TASK-008B** ranking runtime contract | **AUTHORIZED WITH CONDITIONS** |
| TASK-008C persistence | **NOT AUTHORIZED** |
| TASK-008D worker / execution | **NOT AUTHORIZED** |
| Answer runtime (009A) | **NOT AUTHORIZED** |
| AI / semantic ranking | **NOT AUTHORIZED** |
| Concurrent ranking workers (OD-021) | **NOT AUTHORIZED** |

---

## Authorization envelope (TASK-008B — contract phase only)

**Authorized now:**

| Item | Scope |
|------|--------|
| Governance contract | Planned [`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md) (008B deliverable) |
| Mandatory invariants | RK-01 through RK-11 as documented in 008A1 |
| Pipeline registration | 008B → 008C → 008D → Ranking Layer Review |

**Conditions on TASK-008B authorization:**

1. Contract must encode all 008A1 mandatory invariants (permutation-only ranking, completed retrieval prerequisite, mechanical profiles, no scores, no answers).
2. Contract is **governance only** — no tables, migrations, workers, or APIs in 008B.
3. **008C** (persistence) requires separate authorization after contract acceptance.
4. **008D** (worker/execution) requires 008C completion + review gate.
5. Answer runtime (009A), AI/semantic ranking, and concurrent workers remain **not authorized**.

**Mandatory forward conditions (008B deliverable):**

| # | Condition | Requirement |
|---|-----------|-------------|
| 1 | Inter-group ordering | **Deterministic inter-group ordering** must be fully defined in 008B for profiles `GROUP_BY_SOURCE` and `GROUP_BY_DOCUMENT` (group key order + within-group tie-breakers). |
| 2 | Persistence binding | 008B must define **binding persistence constraints** that 008C must implement (table shapes, CHECK constraints, prohibited columns, FK rules). |
| 3 | `EFFECTIVE_DATE_DESC` | Remains a **pure sort order** — `effective_from DESC NULLS LAST` with declared mechanical tie-breakers only. Not relevance, not recency-as-importance inference. |
| 4 | Index naming | Standardize on **`presentation_order_index`** — not `relevance_rank`, not reuse of `deterministic_order_index`. |

**Explicitly not authorized beyond 008B contract:**

- Database migrations / ORM models
- Ranking workers or runtime execution
- HTTP/API routes
- Semantic / vector / AI ranking
- Answer generation or legal conclusions
- Modification of retrieval layer (007A–007E)

---

## Doctrine chain (unchanged)

```text
retrieval result ≠ ranking
ranking ≠ answer
answer ≠ legal conclusion
retrieval evidence ≠ ranking
presentation_order_index ≠ relevance rank
```

Ranking may permute evidence presentation order. It may not re-select evidence, score relevance, generate answers, or infer legal meaning.

---

## Governed pipeline (ranking layer)

```text
TASK-008A  Review
  → TASK-008A1 Remediation
  → TASK-008A1 Acceptance (this document)
  → TASK-008B  Ranking Runtime Contract  ← authorized now
  → TASK-008C  Persistence                 ← not authorized
  → TASK-008D  Worker / Execution          ← not authorized
  → Ranking Layer Review                   ← future gate
  → TASK-009A  Answer Assembly Pre-Auth    ← not authorized
```

Mirrors retrieval and citation governance sequencing.

---

## Next gate

**TASK-008B** — deliver and accept ranking runtime contract per this authorization envelope and forward conditions.

After contract acceptance: **TASK-008C** persistence gate (not yet open).

---

END OF TASK-008A1 ACCEPTANCE REVIEW
