# U-01 — Ranking Worker Skeleton

## Status

**COMPLETE** / **ACCEPTED** — skeleton orchestration envelope only (Claude 20/20).

## Authorization

Approved for **bounded governance + skeleton implementation** per U-01 follow-on from TASK-008D acceptance.

| Scope | Status |
|-------|--------|
| Ranking worker skeleton | **AUTHORIZED** — this task |
| Queue infrastructure | **NOT AUTHORIZED** |
| TASK-009A Answer Runtime | **NOT AUTHORIZED** |

## Baseline

| Item | Value |
|------|--------|
| HEAD | `f7a37ef` |
| Tag | `v0.1.4-ranking-execution` |
| TASK-008D | **COMPLETE** / **ACCEPTED** |
| DEC-010, DEC-011, DEC-012, OD-021 | **LOCKED** |

## Delivered

| Area | Artifact |
|------|----------|
| Worker package | `backend/app/workers/ranking_runtime/` |
| Entrypoint | `run_ranking_worker()` — single-worker only |
| Models | `RankingWorkerRequest`, `RankingWorkerOutcome` |
| Tests | `backend/tests/test_ranking_worker_skeleton.py` |

## Worker behavior

```text
RankingWorkerRequest (accepted envelope)
  → validate_request
  → running (in-worker lifecycle only)
  → execute_controlled_ranking(...)
  → RankingWorkerOutcome (completed | failed)
```

### Documented queue lifecycle (no implementation)

| State | Meaning |
|-------|---------|
| `accepted` | Valid worker request envelope |
| `running` | In-worker orchestration (no queue broker) |
| `completed` | Execution service returned `completed` |
| `failed` | Execution service returned `failed` or pre-validation error |

**No Celery, Redis, RabbitMQ, Kafka, or persistent queue storage.**

## Worker responsibilities

**May:**

- Receive ranking execution request
- Validate execution envelope
- Invoke `execute_controlled_ranking(...)`
- Return `RankingWorkerOutcome`

**Must NOT:**

- Rank evidence itself
- Generate answers, citations, or legal conclusions
- Perform retrieval, AI, semantic, or vector ranking
- Run concurrent worker instances (OD-021)

## Explicit prohibitions

- No migrations, ORM tables, queue storage
- No APIs
- No answer runtime (009A)
- No concurrent / distributed workers

## Next gate

**Ranking Layer Review** — after worker skeleton acceptance.

---

END OF U-01
