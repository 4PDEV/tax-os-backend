# TASK-007B — Retrieval Runtime Contract

## Status

**Complete** — governance-only contract delivered; persistence and execution **not authorized**.

## Authorization basis

| Gate | Status |
|------|--------|
| TASK-007A | **CLOSED** — APPROVED WITH REQUIRED REMEDIATION BEFORE 007B |
| TASK-007A1 | **COMPLETE** |
| TASK-007A1 acceptance | **CLOSED** — TASK-007B **AUTHORIZED WITH CONDITIONS** |

## Important

- **Does NOT implement** retrieval persistence (007C), workers (007D), or runtime execution
- **Does NOT authorize** ranking, answers, AI retrieval, or concurrent workers
- **Does NOT modify** TASK-004A on `main`

## Objective

Establish the governed retrieval runtime contract — evidence references from legal memory and citations — preserving `retrieval result ≠ answer`.

## Canonical artifacts

| Artifact | Path |
|----------|------|
| Primary contract | [`RETRIEVAL_RUNTIME_CONTRACT.md`](../RETRIEVAL_RUNTIME_CONTRACT.md) |
| Remediation spec | [`RETRIEVAL_RUNTIME_REMEDIATION_007A1.md`](../RETRIEVAL_RUNTIME_REMEDIATION_007A1.md) |
| Acceptance review | [`RETRIEVAL_RUNTIME_007A1_ACCEPTANCE_REVIEW.md`](../RETRIEVAL_RUNTIME_007A1_ACCEPTANCE_REVIEW.md) |
| 004A baseline | [`backend/app/services/retrieval/LEGAL_OBJECT_RETRIEVAL_CONTRACT.md`](../backend/app/services/retrieval/LEGAL_OBJECT_RETRIEVAL_CONTRACT.md) |
| Task record | `TASKS/TASK-007B-RETRIEVAL-RUNTIME-CONTRACT.md` |

## Scope delivered

1. Core doctrines (`citation` ≠ retrieval result ≠ answer)
2. Temporal modes — `AS_OF_DATE`, `EXACT_VERSION`, `LATEST_VERSION` (explicit only)
3. Version-pinned evidence requirements
4. Default evidence reference envelope (no answer content)
5. Citation read-only lookup path + provenance chain
6. Deterministic ordering doctrine (`ordering ≠ ranking`)
7. Planned persistence shape (007C) — doctrine only
8. `request_hash` lifecycle identity
9. OD-021 single-worker carry-forward
10. Governed pipeline 007B → 007C → 007D → layer review

## Explicit prohibitions

- no migrations, ORM, workers, APIs
- no semantic/vector/AI search
- no ranking or answer generation
- no citation creation or re-assembly

## Acceptance criteria

- [x] Contract document exists
- [x] R-01 through R-06 invariants encoded
- [x] Ranking / answer / AI boundaries documented
- [x] 007C / 007D registered as future gates
- [x] No implementation introduced

## Next gates (not authorized)

| Task | Scope |
|------|--------|
| **TASK-007C** | Retrieval persistence (append-only requests/results) |
| **TASK-007D** | Retrieval worker / controlled execution |
| **Retrieval layer review** | End-to-end gate after 007D |

---

END OF TASK-007B
