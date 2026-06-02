# TASK-006M — Source Version Extraction Trigger Contract

## Status

APPROVED FOR IMPLEMENTATION

## Objective

Define bounded governance for triggering extraction from canonical `source_versions` without implementing extraction execution.

This task is contract-only and governance-only.

## Canonical Contract

Primary specification:

- `SOURCE_VERSION_EXTRACTION_TRIGGER_CONTRACT.md`

Task record:

- `TASKS/TASK-006M-SOURCE-VERSION-EXTRACTION-TRIGGER-CONTRACT.md`

## Scope Summary

Define:

- extraction trigger role and responsibilities
- source version eligibility rules
- extraction trigger request/result contract shapes
- trigger statuses and failure taxonomy
- idempotency and duplicate protection doctrine
- rerun vs force-reprocess doctrine
- trigger hash doctrine
- handoff boundary to extraction pipeline
- temporal no-inference alignment
- auditability and failure handling expectations

## Explicit Prohibitions

- no extraction execution implementation
- no worker/queue/scheduler implementation
- no parsing/legal-object/citation/answer generation
- no legal or temporal interpretation
- no automatic publication
- no Rwanda-specific onboarding logic

## Acceptance

TASK-006M is complete when:

- contract artifacts exist
- bounded values/doctrines are explicit
- idempotency and rerun/force governance are explicit
- handoff boundary is explicit
- docs are realigned without implementation scope creep

## Final Principle

Extraction trigger means "process this source_version for extraction." It does not mean extraction succeeded or legal meaning is known.
