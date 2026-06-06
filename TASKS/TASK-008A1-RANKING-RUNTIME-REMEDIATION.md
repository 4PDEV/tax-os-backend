# TASK-008A1 — Ranking Runtime Remediation Package

## Status

**Complete** — acceptance review **CLOSED** — TASK-008B **AUTHORIZED WITH CONDITIONS** ([`RANKING_RUNTIME_008A1_ACCEPTANCE_REVIEW.md`](../RANKING_RUNTIME_008A1_ACCEPTANCE_REVIEW.md)).

## Important

- **Does NOT implement TASK-008B**
- **Does NOT implement ranking persistence, workers, or execution**
- **Does NOT modify retrieval layer code** (007A–007E closed)
- No migrations, models, APIs, answers, or AI search

## Objective

Close blocking **008A** pre-authorization findings **RK-01 through RK-11** at the governance level.

Primary objective: resolve **RK-01** — whether ranking is a distinct governed layer vs retrieval ordering profiles.

## Recommendation (RK-01)

**Option A — separate ranking layer** — **SELECTED**

```text
retrieval_result (completed)
  → ranking_request
  → ranking_result
  → ranked_evidence_reference
```

**Option B — retrieval ordering profiles** — **REJECTED**

Rationale: preserves architecture chain (Evidence → Ranking → Answer Assembly), `retrieval result ≠ ranking`, permutation auditability, and lower relevance/AI creep risk. See [`RANKING_RUNTIME_REMEDIATION_008A1.md`](../RANKING_RUNTIME_REMEDIATION_008A1.md) §RK-01.

## Source review

TASK-008A Ranking Runtime Pre-Authorization Review — **APPROVED WITH REQUIRED REMEDIATION BEFORE 008B**

| Finding | Status after 008A1 |
|---------|-------------------|
| RK-01 HIGH — layer boundary ambiguity | **Remediated (spec)** — Option A |
| RK-02 HIGH — `ranking_request_hash` | **Remediated (spec)** |
| RK-03 HIGH — completed retrieval prerequisite | **Remediated (spec)** |
| RK-04 HIGH — permutation invariant | **Remediated (spec)** |
| RK-05 HIGH — read-only provenance | **Remediated (spec)** |
| RK-06 HIGH — append-only persistence | **Remediated (spec)** |
| RK-07 HIGH — no score columns | **Remediated (spec)** |
| RK-08 HIGH — no relevance/semantic/AI inputs | **Remediated (spec)** |
| RK-09 HIGH — no answer generation | **Remediated (spec)** |
| RK-10 MEDIUM — leakage guards | **Remediated (spec)** |
| RK-11 INFO — OD-021 | **Carried forward (spec)** |

## Canonical artifacts

| Artifact | Path |
|----------|------|
| Remediation specification | [`RANKING_RUNTIME_REMEDIATION_008A1.md`](../RANKING_RUNTIME_REMEDIATION_008A1.md) |
| Retrieval layer (upstream, closed) | [`CLAUDE_REVIEW_RETRIEVAL_PIPELINE_007A-007E.md`](../CLAUDE_REVIEW_RETRIEVAL_PIPELINE_007A-007E.md) |
| Task record | `TASKS/TASK-008A1-RANKING-RUNTIME-REMEDIATION.md` |

## Explicit prohibitions

- No ranking implementation
- No retrieval layer modifications
- No answer runtime (009A)
- No relevance scoring, semantic search, or AI ranking
- No concurrent ranking workers (OD-021)

## Acceptance criteria

- [x] Remediation package exists
- [x] RK-01 resolved with explicit Option A recommendation
- [x] RK-02 through RK-11 addressed
- [x] OD-021 carried forward
- [x] Planned 008B flow documented
- [x] Governance docs updated
- [x] No implementation introduced
- [x] TASK-008A1 acceptance review **CLOSED** — TASK-008B authorized with conditions

## Next gate

**TASK-008B** — Ranking Runtime Contract (governance only).

**Not authorized:** 008C persistence, 008D execution, answer runtime (009A).

---

END OF TASK-008A1
