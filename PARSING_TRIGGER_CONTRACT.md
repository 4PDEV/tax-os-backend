# Parsing Trigger Contract

## Purpose

Define governed boundaries for triggering structural parsing from canonical `extracted_text` records.

This contract is governance-only. It does not authorize parsing execution, `parsed_structure` creation, legal-object creation, citation generation, or answer generation.

## Core principle

A parsing trigger means:

**“This extracted_text is approved for structural parsing processing.”**

It does **not** mean:

- parsing succeeded
- legal structure is correct
- legal objects are valid
- the law has been interpreted
- the source is answer-ready

**`parsed_structure` ≠ legal meaning**

Parsing may identify sections, articles, headings, schedules, and structure. Parsing must not interpret law, infer tax effect, infer applicability, infer legal consequence, infer temporal applicability, or infer amendment meaning.

## Trigger role

Parsing trigger is responsible for:

- validating `extracted_text` eligibility
- recording who requested parsing and why
- producing auditable trigger state transitions
- enforcing idempotency and duplicate controls
- defining rerun vs force-reparse doctrine
- defining handoff semantics to the parsing pipeline
- preserving provenance and failure auditability

Parsing trigger must not:

- interpret legal meaning
- infer temporal applicability or amendment meaning
- create legal objects, citations, or answers
- mark a source as legally interpreted or answer-ready
- silently auto-materialize downstream outcomes

## Eligibility rules

An `extracted_text` is parsing-trigger eligible only when:

- `extracted_text` exists
- parent extraction completed successfully (linked `extraction_run` in a success terminal state with text persisted)
- `extracted_text` is canonical and preserved (immutable evidence row; not deleted or superseded by policy)
- `extracted_text` is not explicitly quarantined or rejected when such status exists on the record or related governance flags
- parsing has not already completed successfully for this `extracted_text` unless `force_reparse=True` authorizes replay
- actor type and trigger reason are recorded

Eligibility is evaluated against the **canonical parsing target** (`extracted_text_id`), not mutable request wording.

## ParsingTriggerRequest contract (future)

Required fields:

- `parsing_trigger_request_id`
- `extracted_text_id`
- `requested_by_actor_type`
- `requested_by_actor_identifier` (nullable)
- `trigger_reason`
- `requested_at`
- `rerun_allowed`
- `force_reparse`
- `notes` (nullable)

Optional future fields (implementation tasks only, not required for 006Q):

- `source_version_id` (denormalized lineage convenience; must match `extracted_text.source_version_id` when present)

## ParsingTriggerResult contract (future)

Required fields:

- `parsing_trigger_request_id`
- `extracted_text_id`
- `trigger_status`
- `parser_run_id` (nullable)
- `queued_at` (nullable)
- `started_at` (nullable)
- `completed_at` (nullable)
- `error_category` (nullable)
- `error_message` (nullable)
- `trigger_hash` (nullable)
- `notes` (nullable)

## Trigger status values

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

`completed` means the trigger lifecycle reached a terminal handoff outcome for the request. It does **not** imply `parsed_structure` exists, parsing succeeded, or legal meaning is known.

## Trigger error categories

Allowed `error_category` values only:

- `extracted_text_missing`
- `extracted_text_not_eligible`
- `extraction_not_completed`
- `parsing_already_completed`
- `unsupported_content_type`
- `parsing_pipeline_unavailable`
- `invalid_request`
- `unknown_failure`

## Idempotency doctrine

Parsing trigger is idempotent by default.

**Default canonical identity:** `extracted_text_id` only.

Do **not** include in default idempotency identity:

- `trigger_reason`
- `requested_by_actor_type` / actor identifier
- `rerun_allowed`
- `requested_at`
- database IDs generated at write time
- `notes`

The same `extracted_text` must not receive uncontrolled duplicate default triggers. Changing request metadata must not cause repeat parsing.

If parsing already completed successfully for the `extracted_text`, reject, skip, or return `duplicate_rejected` unless `force_reparse=True`.

Future implementation should enforce idempotency at **application**, **worker**, and **database** layers (mirroring TASK-006P1 extraction hardening). Recommended DB pattern: partial unique index on `extracted_text_id` WHERE `force_reparse = false`.

Optional future extension: include `parser_mode` or `parser_provider` in canonical identity only when multiple default parser pipelines per `extracted_text` are explicitly approved by architecture.

## Rerun and force-reparse doctrine

`rerun_allowed`:

- governance and policy metadata only
- records permission/intent for operators or downstream policy engines
- does **not** bypass idempotency or duplicate protection alone

`force_reparse`:

- explicit replay bypass for intentional reparse
- requires actor and reason
- must remain auditable (new append-only request/result rows)
- required to intentionally reparse after successful parsing

**Clarification:** `rerun_allowed=true` without `force_reparse=true` must not create a new default parsing trigger or parsing execution.

## Trigger hash doctrine

Future `trigger_hash` is derived from stable canonical identity only.

**Default (`force_reparse=false`):**

- `extracted_text_id`

**Force replay (`force_reparse=true`):**

- unique per governed replay request (e.g. `extracted_text_id` + force flag + replay nonce) to preserve append-only audit history

Do **not** include in default hash:

- `trigger_reason`
- actor fields
- `rerun_allowed`
- timestamps
- `notes`

## Handoff boundary

Parsing trigger may hand off to the parsing pipeline by creating or referencing `parser_run`.

This contract does **not** implement:

- parser workers
- parsing execution
- `parsed_structure` persistence
- queues or schedulers

Handoff creates or links execution evidence only; structural output materialization is a separate governed task.

## Governance rules

Parsing trigger must not automatically:

- run parsing logic beyond governed handoff references
- create `parsed_structures`
- create legal objects
- create citations
- generate answers
- infer effective/applicability/repeal dates
- infer legal meaning, tax effect, or amendment meaning
- mark source as answer-ready or legally interpreted

## Temporal governance alignment

Parsing trigger must preserve:

- explicit `extracted_text_id` and available `source_version_id` lineage as-is
- source-version temporal metadata without mutation
- no silent temporal inference
- no assumption that latest `source_version` equals applicable law

## Provenance requirements

Every parsing trigger record must preserve:

- `extracted_text_id`
- `source_version` lineage where available via `extracted_text`
- actor type and identifier
- reason and request timestamp
- `rerun_allowed` and `force_reparse` flags
- status, error category/message, and related `parser_run_id` when created

## Failure handling

Failures must be:

- persisted in append-only trigger results
- queryable by operators and auditors
- not silently retried without explicit policy
- non-destructive to canonical `extracted_text` and prior parsing history

## Concurrency doctrine (OD-021)

Today’s orchestration may be single-worker. Future concurrent parsing workers must mitigate:

- execution-time replay race (read-check-then-act between workers)
- duplicate parsing execution for the same `extracted_text`

Recommended future mitigations (implementation in TASK-006R or dedicated hardening task, not 006Q):

- row-level locking on trigger or run rows
- PostgreSQL advisory locks keyed by `extracted_text_id`
- execution-level uniqueness guards and partial unique indexes aligned with idempotency doctrine

TASK-006Q defines doctrine only; no concurrency implementation is required here.

## Non-implementation clause

TASK-006Q authorizes governance only, not parsing execution, persistence tables, or parser workers.

## Final principle

Parsing trigger says: **“Process this extracted_text for structural parsing.”**

It does not say: **“The legal meaning is known.”**
