# Source Version Extraction Trigger Contract

## Purpose

Define governed boundaries for triggering extraction from canonical `source_versions`.

This contract is governance-only. It does not authorize extraction execution, parsing, legal-object creation, citation generation, or answer generation.

## Trigger Role

Extraction trigger is responsible for:

- validating source-version eligibility
- recording who requested extraction and why
- producing auditable trigger state transitions
- enforcing idempotency/duplicate controls
- defining handoff semantics to extraction pipeline

Extraction trigger must not:

- interpret legal meaning
- infer temporal applicability
- create legal objects/citations/answers
- silently auto-promote downstream outcomes

## Eligibility Rules

A source version is extraction-trigger eligible only when:

- `source_version` exists
- `source_version` is canonical/promoted and not archived/rejected
- required artifact/provenance exists
- extraction not already successfully completed unless rerun/force flags authorize it
- actor and reason are recorded

## ExtractionTriggerRequest Contract (future)

Required fields:

- `extraction_trigger_request_id`
- `source_version_id`
- `requested_by_actor_type`
- `requested_by_actor_identifier` (nullable)
- `trigger_reason`
- `requested_at`
- `rerun_allowed`
- `force_reprocess`
- `notes` (nullable)

## ExtractionTriggerResult Contract (future)

Required fields:

- `extraction_trigger_request_id`
- `source_version_id`
- `trigger_status`
- `extraction_run_id` (nullable)
- `queued_at` (nullable)
- `started_at` (nullable)
- `completed_at` (nullable)
- `error_category` (nullable)
- `error_message` (nullable)
- `trigger_hash` (nullable)
- `notes` (nullable)

## Trigger Status Values

Allowed `trigger_status` values only:

- `pending`
- `accepted`
- `rejected`
- `queued`
- `started`
- `completed`
- `failed`
- `skipped`
- `duplicate_rejected`

## Trigger Error Categories

Allowed `error_category` values only:

- `source_version_missing`
- `source_version_not_eligible`
- `provenance_missing`
- `extraction_already_completed`
- `unsupported_source_type`
- `extraction_pipeline_unavailable`
- `invalid_request`
- `unknown_failure`

## Idempotency Doctrine

Extraction trigger is idempotent by default.

Same:

- `source_version_id`
- `trigger_reason`
- `requested_by_actor_type`
- `force_reprocess=false`

must not create uncontrolled duplicate triggers.

If extraction already completed, reject or skip unless `rerun_allowed=true` or `force_reprocess=true`.

## Rerun and Force-Reprocess Doctrine

`rerun_allowed`:

- permits governed additional extraction attempt

`force_reprocess`:

- explicitly bypasses duplicate trigger protection
- requires actor + reason
- must remain auditable

## Trigger Hash Doctrine

**Implemented (TASK-006P1):** default `trigger_hash` derives from canonical target only:

- `source_version_id`

Do not include in default hash:

- `trigger_reason`
- `requested_by_actor_type`
- `rerun_allowed`
- `requested_at`
- database IDs/timestamps generated at write time

`force_reprocess=True` rows use a unique replay hash per request to preserve append-only audit history while allowing governed replays.

`rerun_allowed` records governance permission only; it does **not** bypass idempotency. `force_reprocess=True` is the explicit bypass.

## Handoff Boundary

Trigger may hand off to extraction pipeline by creating or referencing `extraction_run`.

This task does not implement extraction execution or trigger workers.

## Governance Rules

Trigger must not automatically:

- run extraction logic
- parse source text
- create legal objects
- create citations
- generate answers
- infer effective/applicability/repeal dates
- infer legal meaning
- mark source as answer-ready

## Temporal Governance Alignment

Trigger must preserve:

- explicit `source_version_id`
- source-version temporal metadata as-is
- no silent temporal inference
- no assumption that latest source is applicable law

## Auditability

Future trigger records must preserve:

- `source_version_id`
- actor type/identifier
- reason
- request timestamp
- rerun/force flags
- status/error fields
- related `extraction_run_id` when created

## Failure Handling

Failures must be:

- recorded
- queryable
- not silently retried without policy
- non-destructive to canonical memory

## Non-Implementation Clause

TASK-006M authorizes governance only, not extraction execution.

## Final Principle

Extraction trigger says: "Process this source_version for extraction."
It does not say: "The extracted legal meaning is known."
