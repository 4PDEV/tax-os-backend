# TASK-006Q–006T — Parsing Pipeline Reviewer Package

## Checkpoint

| Item | Value |
|------|-------|
| Tag | `checkpoint-task-006t-controlled-parsing-execution` |
| Commit | `9d39810` (006T) on `main` |
| Tests | 578 passed |

## Review artifact

| Document | Purpose |
|----------|---------|
| [`CLAUDE_REVIEW_PARSING_PIPELINE_006Q-T.md`](../CLAUDE_REVIEW_PARSING_PIPELINE_006Q-T.md) | Full architecture review for Claude acknowledgment |

## Prior related reviews

| Document | Scope |
|----------|-------|
| [`CLAUDE_REVIEW_EXTRACTION_PIPELINE_006M-P.md`](../CLAUDE_REVIEW_EXTRACTION_PIPELINE_006M-P.md) | Extraction pipeline 006M–006P |
| [`CLAUDE_VERIFICATION_EXTRACTION_REPLAY_006P1.md`](../CLAUDE_VERIFICATION_EXTRACTION_REPLAY_006P1.md) | 006P1 idempotency verification |

## Review focus areas

1. Parsing replay / idempotency (`extracted_text_id`, DB partial unique index, worker skip)
2. `parsed_structure` append-only guarantees
3. Structural parsing boundary (`parsed_structure` ≠ legal meaning)
4. No semantic / legal interpretation leakage
5. Provenance continuity
6. OD-021 concurrency (creation-time vs execution-time)
7. Hidden overwrite risks

## Gate

**TASK-006Q–006T gate:** **CLOSED** (2026-06-02). **Legal-object promotion gate OPEN** after [`CLAUDE_VERIFICATION_PARSED_STRUCTURE_IDENTITY_006T1A.md`](../CLAUDE_VERIFICATION_PARSED_STRUCTURE_IDENTITY_006T1A.md).

**Approved next:** TASK-006U — Legal Object Promotion Contract.

## Task records

- [`TASK-006Q-PARSING-TRIGGER-CONTRACT.md`](TASK-006Q-PARSING-TRIGGER-CONTRACT.md)
- [`TASK-006R-PARSING-TRIGGER-PERSISTENCE.md`](TASK-006R-PARSING-TRIGGER-PERSISTENCE.md)
- [`TASK-006S-PARSING-WORKER-SKELETON.md`](TASK-006S-PARSING-WORKER-SKELETON.md)
- [`TASK-006T-CONTROLLED-PARSING-EXECUTION.md`](TASK-006T-CONTROLLED-PARSING-EXECUTION.md)
- [`TASK-006T1A-PARSED-STRUCTURE-IDENTITY-HARDENING.md`](TASK-006T1A-PARSED-STRUCTURE-IDENTITY-HARDENING.md) (P-01 remediation)
- [`CLAUDE_VERIFICATION_PARSED_STRUCTURE_IDENTITY_006T1A.md`](../CLAUDE_VERIFICATION_PARSED_STRUCTURE_IDENTITY_006T1A.md) (006T1A verification only)
