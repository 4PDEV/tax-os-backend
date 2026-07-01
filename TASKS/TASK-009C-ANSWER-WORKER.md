# TASK-009C — Answer Worker Pre-Authorization

## Status

**TASK-009C-PREAUTH** — **ACCEPTED** — DEC-017.

| Phase | Status |
|-------|--------|
| TASK-009A answer assembly | **COMPLETE** / **ACCEPTED** — `v0.1.8-answer-assembly` |
| TASK-009B answer persistence | **COMPLETE** / **ACCEPTED** — `v0.1.9-answer-persistence` |
| Answer persistence review (009B+) | **ACCEPTED WITH REMEDIATION** |
| TASK-009C-PREAUTH (this document) | **ACCEPTED** — DEC-017 |
| TASK-009C-IMPL-AUTH | **ACCEPTED** — DEC-018 — [`TASK-009C-IMPLEMENTATION-AUTHORIZATION.md`](TASK-009C-IMPLEMENTATION-AUTHORIZATION.md) |
| TASK-009C answer worker code | **AUTHORIZED FOR LIMITED IMPLEMENTATION** |

## Prerequisite chain

```text
009A assembly → 009B persistence → 009B+ review (accepted with remediation)
  → 009C-PREAUTH (accepted)
  → 009C-IMPL-AUTH (complete)
  → [Claude review — pending]
  → 009C worker skeleton — NOT AUTHORIZED
```

## Important

- **Does NOT implement** worker code, queues, migrations, APIs, or tests
- **Does NOT modify** `answer_persistence` or `answer_assembly` services
- **Does NOT authorize** response runtime, public APIs, or AI generation

## Objective

Establish the governed answer worker contract — single-process orchestration over `persist_answer_for_ranking_request` — preserving DEC-010 through DEC-016 and OD-021.

## Canonical artifacts

| Artifact | Path |
|----------|------|
| Primary contract | [`ANSWER_WORKER_CONTRACT.md`](../ANSWER_WORKER_CONTRACT.md) |
| Answer persistence (downstream delegate) | [`ANSWER_PERSISTENCE_CONTRACT.md`](../ANSWER_PERSISTENCE_CONTRACT.md) |
| Answer assembly (indirect via 009B) | [`ANSWER_ASSEMBLY_CONTRACT.md`](../ANSWER_ASSEMBLY_CONTRACT.md) |
| Persistence review | [`TASKS/ANSWER-PERSISTENCE-REVIEW.md`](ANSWER-PERSISTENCE-REVIEW.md) |
| Decision locks | [`DECISION_LOG.md`](../DECISION_LOG.md) — DEC-017 |

## Governance decisions delivered

### 1. Worker boundary

Orchestration only — validate envelope, call `persist_answer_for_ranking_request`, return `AnswerWorkerOutcome`. No assembly, ranking, retrieval, citation creation, AI, or response rendering.

### 2. Entry point

`backend/app/workers/answer_runtime/` · `run_answer_worker(db, request)` — design frozen; no code in this task.

### 3. DTOs

`AnswerWorkerRequest` and `AnswerWorkerOutcome` — field lists locked in contract §3.

### 4. Lifecycle

Documented only: `accepted` → `running` → `completed` | `failed`. No queue infrastructure.

### 5. Delegation rule

**Single write path:** `persist_answer_for_ranking_request`. Prohibited: all `create_answer_*`, `assemble_answer_package`, `resolve_ranking_assembly_inputs`.

### 6. OD-021

Process-local mutex required; concurrent/distributed workers and queue brokers prohibited.

### 7. Failure mapping

Persistence terminal statuses mapped to worker outcome; reuse 009A/009B error categories only.

### 8. Import guards

Frozen prohibited import list — mirrors U-01 pattern with answer-specific boundaries.

### 9. Test plan

Design-only matrix in contract §9 — `test_answer_worker_skeleton.py` when implemented.

### 10. Response runtime boundary

Worker ≠ response runtime — no HTTP, no public payloads, no narrative rendering.

### 11. Readiness criteria

IMPL-AUTH and implementation checklists in contract §11.

## Pattern reference

| Layer | Worker pattern |
|-------|----------------|
| Ranking (U-01) | `run_ranking_worker` → `execute_controlled_ranking` |
| **Answer (009C)** | `run_answer_worker` → `persist_answer_for_ranking_request` |

## Explicit prohibitions

| Prohibited | |
|------------|--|
| Worker implementation | This task |
| Queue infrastructure | Celery, Redis, RabbitMQ, Kafka |
| APIs / FastAPI | Not authorized |
| Response runtime | Not authorized |
| Concurrent workers | OD-021 |
| AI / semantic / vector | Not authorized |
| `CitationAssembler` | Not authorized |
| `answer_text` / legal conclusions | Not authorized |

## Next gate

**Claude review** of 009C-IMPL-AUTH → explicit TASK-009C implementation authorization.

---

END OF TASK-009C PRE-AUTHORIZATION (implementation NOT AUTHORIZED)
