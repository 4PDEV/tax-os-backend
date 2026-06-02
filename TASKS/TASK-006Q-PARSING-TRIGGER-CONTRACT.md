# TASK-006Q — Parsing Trigger Contract

## Status

**Complete** (contract-only; governance-only)

## Objective

Define the governed contract for triggering structural parsing from canonical `extracted_text` records.

This task establishes the boundary:

```text
extracted_text → parsing request
```

It does **not** implement parsing execution, `parsed_structure` creation, legal object creation, citation generation, or answer generation.

## Canonical contracts

| Artifact | Path |
|----------|------|
| Primary specification | [`PARSING_TRIGGER_CONTRACT.md`](../PARSING_TRIGGER_CONTRACT.md) |
| Task record | `TASKS/TASK-006Q-PARSING-TRIGGER-CONTRACT.md` |

## Prerequisites

- TASK-006P controlled extraction execution (`extracted_text` evidence)
- TASK-006P1 extraction replay/idempotency hardening (EXT-01 / OD-019)
- TASK-006A ingestion persistence (`parser_runs`, `parsed_structures` tables exist; not wired by this task)
- TASK-006M extraction trigger contract (parallel pattern)

## Scope delivered

1. Parsing trigger role and responsibilities
2. `extracted_text` eligibility rules
3. Future `ParsingTriggerRequest` / `ParsingTriggerResult` field contracts
4. Trigger status and error category taxonomies
5. Idempotency doctrine (`extracted_text_id` canonical identity)
6. `rerun_allowed` vs `force_reparse` doctrine
7. Trigger hash doctrine
8. Handoff boundary to `parser_run` (contract reference only)
9. Temporal no-inference alignment
10. Provenance and failure-handling requirements
11. OD-021 concurrency doctrine for future 006Q/006R design

## Explicit prohibitions

- no parser worker implementation
- no parsing execution
- no `parsed_structure` creation
- no legal object / citation / answer generation
- no legal or temporal interpretation
- no parsing queues, schedulers, or Rwanda-specific parsing logic
- no AI or semantic interpretation

## Doctrine (critical)

| Parsing may identify | Parsing must not |
|--------------------|------------------|
| sections, articles, headings, schedules, structure | interpret law, infer tax effect, applicability, legal consequence, temporal applicability, or amendment meaning |

**`parsed_structure` ≠ legal meaning**

## Acceptance criteria

| Criterion | Met |
|-----------|-----|
| Parsing trigger contract exists | Yes |
| Trigger role documented | Yes |
| Eligibility rules documented | Yes |
| Request/result contracts documented | Yes |
| Trigger statuses documented | Yes |
| Error categories documented | Yes |
| Idempotency doctrine documented | Yes |
| Rerun/force-reparse doctrine documented | Yes |
| Trigger hash doctrine documented | Yes |
| Handoff boundary documented | Yes |
| Temporal alignment documented | Yes |
| OD-021 concurrency note documented | Yes |
| Status/docs updated | Yes |
| No implementation scope creep | Yes |

## Follow-on tasks (not in 006Q)

| Task | Intent |
|------|--------|
| TASK-006R (or equivalent) | Parsing trigger persistence + DB idempotency hardening |
| Later | Parser worker skeleton, controlled parsing execution |

## Final principle

Parsing trigger means: **“Process this extracted_text for structural parsing.”**

It does not mean: **“The legal meaning is known.”**
