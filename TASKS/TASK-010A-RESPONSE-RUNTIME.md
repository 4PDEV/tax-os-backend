# TASK-010A — Response Runtime Pre-Authorization

## Status

**TASK-010A-PREAUTH** — **ACCEPTED** — DEC-019.

| Phase | Status |
|-------|--------|
| TASK-009A answer assembly | **COMPLETE** / **ACCEPTED** — `v0.1.8-answer-assembly` |
| TASK-009B answer persistence | **COMPLETE** / **ACCEPTED** — `v0.1.9-answer-persistence` |
| TASK-009C answer worker | **COMPLETE** / **ACCEPTED** — `v0.2.3-answer-worker-skeleton` |
| TASK-010A-PREAUTH (this document) | **ACCEPTED** — DEC-019 |
| TASK-010A-IMPL-AUTH | **COMPLETE** — DEC-020 — [`TASK-010A-IMPLEMENTATION-AUTHORIZATION.md`](TASK-010A-IMPLEMENTATION-AUTHORIZATION.md) |
| TASK-010A response runtime code | **COMPLETE** / **ACCEPTED WITH FINDINGS** — `v0.2.4-response-runtime` |
| TASK-010A+ layer review | **COMPLETE** / **ACCEPTED WITH FINDINGS** — `v0.2.6-response-runtime-layer-review` |

## Prerequisite chain

```text
009A assembly → 009B persistence → 009C worker (complete)
  → 010A-PREAUTH (accepted — Claude review)
  → 010A-IMPL-AUTH (complete)
  → 010A implementation (accepted with findings)
  → 010A+ layer review (accepted with findings)
```

## Important

- **Does NOT implement** runtime services, APIs, workers, migrations, ORM, or tests
- **Does NOT modify** answer persistence, assembly, or worker packages
- **Does NOT authorize** public HTTP APIs, queues, or AI generation

## Objective

Establish the governed response runtime contract — read-only delivery from completed answer persistence — preserving DEC-010 through DEC-018 and OD-021.

## Canonical artifacts

| Artifact | Path |
|----------|------|
| Primary contract | [`RESPONSE_RUNTIME_CONTRACT.md`](../RESPONSE_RUNTIME_CONTRACT.md) |
| Answer worker (upstream) | [`ANSWER_WORKER_CONTRACT.md`](../ANSWER_WORKER_CONTRACT.md) |
| Answer persistence (read source) | [`ANSWER_PERSISTENCE_CONTRACT.md`](../ANSWER_PERSISTENCE_CONTRACT.md) |
| Answer assembly (upstream, indirect) | [`ANSWER_ASSEMBLY_CONTRACT.md`](../ANSWER_ASSEMBLY_CONTRACT.md) |
| Decision locks | [`DECISION_LOG.md`](../DECISION_LOG.md) — DEC-019 |

## Governance decisions delivered

### G-01 Response runtime boundary

Read and render only — validate envelope, resolve `completed` terminal result, load accepted children, return `ResponsePackage`. No retrieve, rank, assemble, persist, workers, AI, or legal conclusions.

### G-02 Entry point

`backend/app/services/response_runtime/` · `build_response(db, request)` — design frozen; no code in this task.

### G-03 Inputs

`ResponseRequest`: `answer_request_id`, `contract_version` (`010A-v1`), `include_rendered_citation_text`, optional `answer_result_id` pin.

### G-04 Outputs

`ResponseOutcome` + `ResponsePackage` — delivery DTO only; no persistence metadata leakage; no ORM objects.

### G-05 Read model

`answer_results`, `answer_evidence_entries`, `answer_uncertainty_flags`, read-only provenance/citation joins; permitted `get_*` / `list_*` from answer persistence only.

### G-06 Rendering rules

Persisted `presentation_order_index` order only — no sort, filter, dedupe, or inference.

### G-07 Citation rules

`CitationFormatter` permitted read-only; `CitationAssembler` prohibited.

### G-08 Error model

Runtime-specific `error_category` vocabulary; persistence categories mapped — not reused directly.

### G-09 Import guards

Frozen prohibited import list — mirrors answer worker pattern with response-specific boundaries.

### G-10 Layer separation

Full chain documented through future API layer.

### G-11 Determinism

Same persisted answer × same rendering options = identical `ResponsePackage`; no timestamps in payload identity.

### G-12 Readiness checklist

Prerequisites met; implementation gates and Claude review documented.

## Pattern reference

| Layer | Delivery pattern |
|-------|------------------|
| Answer worker (009C) | `run_answer_worker` → `persist_answer_for_ranking_request` |
| **Response runtime (010A)** | `build_response` → read completed persistence → `ResponsePackage` |

## Explicit prohibitions

| Prohibited | |
|------------|--|
| Runtime implementation | This task |
| Public APIs / FastAPI | Not authorized |
| Workers / queues | Not authorized |
| Persistence writes | Not authorized |
| Assembly / retrieval / ranking | Not authorized |
| AI / semantic / vector | Not authorized |
| `CitationAssembler` | Not authorized |
| `answer_text` / legal conclusions | Not authorized in 010A-v1 |

## Open questions

OQ-R-01 through OQ-R-10 documented in contract — recommendations provided; no premature implementation locks.

## Architectural risks

Documented in contract — join re-implementation, metadata leakage, order mutation, API bypass.

## Next gate

**Post-layer governance.** API layer, public HTTP delivery, queues, and AI remain **NOT AUTHORIZED**. No API-layer implementation or pre-authorization is opened by TASK-010A+ acceptance.

---

END OF TASK-010A PRE-AUTHORIZATION
