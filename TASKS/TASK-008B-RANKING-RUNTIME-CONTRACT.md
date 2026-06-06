# TASK-008B — Ranking Runtime Contract

## Status

**Complete** — governance-only contract delivered; persistence and execution **not authorized**.

## Authorization basis

| Gate | Status |
|------|--------|
| TASK-008A | **COMPLETE** — APPROVED WITH REQUIRED REMEDIATION BEFORE 008B |
| TASK-008A1 | **COMPLETE** |
| TASK-008A1 acceptance | **CLOSED** — TASK-008B **AUTHORIZED WITH CONDITIONS** |

## Important

- **Does NOT implement** ranking persistence (008C), workers (008D), or runtime execution
- **Does NOT authorize** answer runtime (009A), AI/semantic ranking, or concurrent workers
- **Does NOT modify** retrieval layer (007A–007E)

## Objective

Establish the governed ranking runtime contract — mechanical presentation permutations over completed retrieval evidence — preserving `retrieval result ≠ ranking` and `ranking ≠ answer`.

## Canonical artifacts

| Artifact | Path |
|----------|------|
| Primary contract | [`RANKING_RUNTIME_CONTRACT.md`](../RANKING_RUNTIME_CONTRACT.md) |
| Remediation spec | [`RANKING_RUNTIME_REMEDIATION_008A1.md`](../RANKING_RUNTIME_REMEDIATION_008A1.md) |
| Acceptance review | [`RANKING_RUNTIME_008A1_ACCEPTANCE_REVIEW.md`](../RANKING_RUNTIME_008A1_ACCEPTANCE_REVIEW.md) |
| Upstream retrieval contract | [`RETRIEVAL_RUNTIME_CONTRACT.md`](../RETRIEVAL_RUNTIME_CONTRACT.md) |
| Task record | `TASKS/TASK-008B-RANKING-RUNTIME-CONTRACT.md` |

## Scope delivered

1. Layer definition — `retrieval_result` → `ranking_request` → `ranking_result` → `ranked_evidence_reference`
2. Core doctrines (`retrieval result` ≠ ranking ≠ answer)
3. `ranking_request_hash` identity formula
4. Closed profile enum — `CANONICAL`, `EFFECTIVE_DATE_DESC`, `GROUP_BY_SOURCE`, `GROUP_BY_DOCUMENT`
5. Completed `retrieval_result` prerequisite
6. Permutation invariant (no adds/drops/filter/top-N)
7. Read-only provenance — no citation lookup/creation
8. Deterministic ordering per profile including **inter-group ordering**
9. `presentation_order_index` naming standard
10. Binding persistence constraints for 008C (partial unique, CHECK enums, unique per result)
11. Prohibited score/answer fields
12. Import guard requirements (RK-10)
13. OD-021 single-worker carry-forward
14. 008A1 forward conditions 1–4 resolved

## Explicit prohibitions

- no migrations, ORM, workers, APIs
- no semantic/vector/AI ranking
- no answer generation or legal conclusions
- no runtime-created ranking profiles
- no modification of retrieval layer

## Acceptance criteria

- [x] Contract document exists
- [x] RK-01 through RK-11 invariants encoded
- [x] Forward conditions 1–4 resolved
- [x] 008C binding persistence constraints defined
- [x] Answer / AI boundaries documented
- [x] 008C / 008D registered as future gates
- [x] No implementation introduced

## Next gates (not authorized)

| Task | Scope |
|------|--------|
| **TASK-008C** | Ranking persistence (append-only; implement contract constraints) |
| **TASK-008D** | Ranking worker / controlled execution |
| **Ranking layer review** | End-to-end gate after 008D |
| **TASK-009A** | Answer assembly pre-auth (after ranking layer review) |

---

END OF TASK-008B
