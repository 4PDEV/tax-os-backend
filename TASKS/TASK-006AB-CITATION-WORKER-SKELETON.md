# TASK-006AB — Citation Worker Skeleton

## Status

**Complete** — dry-run orchestration only

## Objective

Orchestrate citation assembly governance requests through a dry-run provider without citation rendering or execution.

```text
citation_assembly_governance_request
  → accepted
  → dry-run provider
  → skipped (citation_id null)
```

## Module

`backend/app/workers/citation_assembly_governance/`

| File | Role |
|------|------|
| `worker.py` | `CitationAssemblyGovernanceWorker` |
| `dry_run_provider.py` | `DryRunCitationAssemblyGovernanceProvider` |
| `runner.py` | `run_citation_assembly_governance_dry_run(dry_run=True)` |
| `result.py` | Provider + run summary dataclasses |

## Dry-run semantics

- Terminal status: **`skipped`** (not `assembled`)
- `citation_id` and `assembled_at` always **null**
- `skipped` = orchestration completed without execution — not request ignored

## Out of scope

- No `CitationAssembler` / TASK-004D
- No citation text, retrieval, answers, AI
- No controlled citation execution (future task + review gate)

## Tests

`backend/tests/test_citation_assembly_governance_worker_skeleton.py`

## Prerequisites

- TASK-006Z persistence
- TASK-006AA pre-auth review (`checkpoint-task-006aa-citation-worker-preauth-review`)
