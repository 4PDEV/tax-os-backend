# TASK-007E — Controlled Retrieval Execution

## Status

**Complete** — **ACCEPTED** — controlled retrieval execution implemented and accepted per [`RETRIEVAL_EXECUTION_007D1_ACCEPTANCE_REVIEW.md`](../RETRIEVAL_EXECUTION_007D1_ACCEPTANCE_REVIEW.md) and [`CLAUDE_REVIEW_RETRIEVAL_PIPELINE_007A-007E.md`](../CLAUDE_REVIEW_RETRIEVAL_PIPELINE_007A-007E.md).

## Prerequisite chain

```text
007B Contract → 007C Persistence → 007D Dry-Run Skeleton
  → 007D1 Remediation → 007D1 Acceptance
  → 007E Controlled Execution (this task)
```

## Objective

Implement controlled retrieval execution: select version-pinned evidence, persist `retrieval_evidence_references`, complete `retrieval_result` lifecycle.

## Authorized pipeline

```text
retrieval_request
  → retrieval_result (accepted)
  → controlled retrieval execution
  → retrieval_evidence_references
  → retrieval_result (completed, result_count=N)
```

Zero-result: `completed`, `result_count=0`. Failure: `accepted` → `failed`.

## Delivered

| Area | Artifact |
|------|----------|
| Execution service | `backend/app/services/retrieval_execution/` — selection, ordering, citation lookup, execution |
| Controlled provider | `backend/app/workers/retrieval_runtime/controlled_provider.py` |
| Runner | `run_controlled_retrieval_execution(controlled_execution=True)` — mandatory flag |
| Worker mode | `EXECUTION_MODE_CONTROLLED_EXECUTION` — `accepted` → `completed` / `failed` |
| Dry-run unchanged | `run_retrieval_runtime_dry_run()` — `accepted` → `skipped` |
| Tests | `backend/tests/test_controlled_retrieval_execution.py` |
| Full suite | 777 tests passing |

## Mandatory constraints (implemented)

- `AS_OF_DATE` — legal-object `effective_from` / `effective_to` window only; return all matches
- `EXACT_VERSION` — pin `legal_object_version_id`; no fallback
- `LATEST_VERSION` — explicit mode only; uses `current_version_id`; no silent fallback
- Citation read-only attach; citation-less evidence valid; no `CitationAssembler`
- Deterministic ordering → `deterministic_order_index` (not rank)
- Append-only persistence; metadata whitelist
- RW-05 import/schema/execution leakage guards
- OD-021 single-worker only; `request_hash`-keyed lock documented for future concurrency

## Explicit prohibitions (unchanged)

- Ranking, relevance, confidence, semantic scores
- Vector / AI / semantic search
- Answer generation, legal/tax reasoning
- Citation creation, `CitationAssembler` invocation
- Concurrent workers
- `fail_on_overlap` / `temporal_ambiguity` (optional — not implemented)

## Acceptance criteria

- [x] Controlled retrieval provider exists
- [x] Controlled runner exists
- [x] AS_OF_DATE execution works
- [x] EXACT_VERSION execution works
- [x] Explicit LATEST_VERSION works
- [x] No silent latest fallback
- [x] Citation attachment read-only works
- [x] Citation-less evidence valid
- [x] Deterministic ordering works
- [x] Evidence references persisted
- [x] result_count correct
- [x] Append-only behavior preserved
- [x] Import/leakage guards pass
- [x] Tests pass
- [x] Docs updated
- [x] No ranking/answer/AI scope introduced

## Next

Retrieval layer review **CLOSED** — see [`TASK-007A-007E-RETRIEVAL-PIPELINE-REVIEWER-PACKAGE.md`](TASK-007A-007E-RETRIEVAL-PIPELINE-REVIEWER-PACKAGE.md). Next gate: **TASK-008A** ranking pre-auth (not authorized).

---

END OF TASK-007E
