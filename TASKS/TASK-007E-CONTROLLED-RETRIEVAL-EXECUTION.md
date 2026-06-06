# TASK-007E — Controlled Retrieval Execution

## Status

**Authorized for implementation** — controlled execution scope per [`RETRIEVAL_EXECUTION_007D1_ACCEPTANCE_REVIEW.md`](../RETRIEVAL_EXECUTION_007D1_ACCEPTANCE_REVIEW.md).

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
  → retrieval execution
  → retrieval_evidence_references
  → retrieval_result (completed, result_count=N)
```

Zero-result: `completed`, `result_count=0`. Failure: `accepted` → `failed`.

## Mandatory constraints

- `AS_OF_DATE` — legal-object `effective_from` / `effective_to` window only
- `EXACT_VERSION` — pin `legal_object_version_id`
- `LATEST_VERSION` — explicit mode only; no silent fallback
- AS_OF_DATE ambiguity (default) — return all matches; no silent winner
- Citation read-only attach; citation-less evidence valid
- Deterministic ordering → `deterministic_order_index`
- Append-only persistence; metadata whitelist
- RW-05 import/schema/execution leakage guards
- OD-021 single-worker only

## Explicit prohibitions

- Ranking, relevance, confidence, semantic scores
- Vector / AI / semantic search
- Answer generation, legal/tax reasoning
- Citation creation, `CitationAssembler` invocation
- Concurrent workers
- Modification of 007D dry-run behavior (additive only)

## Not yet delivered

Awaiting implementation prompt.

## Next

Retrieval layer review — after 007E acceptance.

---

END OF TASK-007E
