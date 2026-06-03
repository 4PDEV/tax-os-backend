# Legal Object Promotion Contract

## Purpose

Define governed boundaries for promoting canonical `parsed_structure` evidence into canonical `legal_object` legal memory.

This contract is governance-only. It does not authorize promotion execution, new legal-object table design beyond existing 003x contracts, citation generation, or answer generation.

## Core principle

**`parsed_structure` ≠ legal object**

| Layer | Role |
|-------|------|
| `parsed_structure` | Structural evidence from parsing (sections, articles, headings, schedules, clauses, units) |
| `legal_object` | Governed canonical legal memory unit — uniquely identified, provenance-linked, temporally anchored, citation-ready in future phases |

A parsed structure is structural evidence. A legal object is canonical legal memory.

**Promotion is a governed decision, not an automatic parsing outcome.**

Structural detection alone does not create legal memory.

## Promotion role

Legal object promotion is responsible for:

- validating `parsed_structure` eligibility for promotion review
- recording who requested promotion and why
- producing auditable promotion state transitions
- enforcing idempotency and duplicate controls
- defining `force_repromotion` replay doctrine
- defining handoff semantics to legal-object materialization (future tasks)
- preserving full provenance chain integrity

Legal object promotion must not:

- represent legal advice, tax advice, applicability, legal conclusion, or legal consequence
- infer legal meaning from structure labels alone
- auto-create legal objects as a side effect of parsing
- create citations or answers
- mutate temporal fields on `source_version` or infer legal force

## Promotion boundary

```text
parsed_structure → promotion review → legal_object
```

Promotion is a governed transition. Completing parsing does **not** imply promotion approval or legal memory creation.

## Eligibility rules

A `parsed_structure` is promotion-eligible only when:

- `parsed_structure` exists and is canonical/preserved
- parent `parser_run` completed successfully (`success` or governed `partial` where policy allows)
- `structure_hash` is present and valid
- `source_version_id` lineage exists and is traceable
- provenance chain is complete:

```text
source_version → extraction_run → extracted_text → parser_run → parsed_structure
```

- `parsed_structure` is not explicitly quarantined or rejected when such status exists
- default promotion has not already succeeded for this `parsed_structure` unless `force_repromotion=True`

Eligibility is evaluated against the **canonical promotion target** (`parsed_structure_id`), not mutable request metadata.

## LegalObjectPromotionRequest contract (future)

Required fields:

- `legal_object_promotion_request_id`
- `parsed_structure_id`
- `source_version_id`
- `promotion_reason`
- `requested_by_actor_type`
- `requested_by_actor_identifier` (nullable)
- `requested_at`
- `force_repromotion`
- `notes` (nullable)

Allowed `requested_by_actor_type` values (future implementation):

- `user`
- `system`
- `worker`
- `admin`
- `test`

`promotion_reason` records governance intent. It does **not** bypass idempotency.

## LegalObjectPromotionResult contract (future)

Required fields:

- `legal_object_promotion_request_id`
- `parsed_structure_id`
- `promotion_status`
- `legal_object_id` (nullable)
- `promoted_at` (nullable)
- `error_category` (nullable)
- `error_message` (nullable)
- `promotion_hash` (nullable)
- `notes` (nullable)

## Promotion status values

Allowed `promotion_status` values only:

- `pending`
- `accepted`
- `rejected`
- `promoted`
- `failed`
- `skipped`
- `duplicate_rejected`

`promoted` means the promotion lifecycle reached a terminal success handoff for the request. It does **not** imply legal meaning is correct, tax effect is known, or citations/answers are ready.

## Promotion error categories

Allowed `error_category` values only:

- `parsed_structure_missing`
- `parser_run_incomplete`
- `provenance_incomplete`
- `duplicate_promotion`
- `invalid_request`
- `promotion_pipeline_unavailable`
- `unknown_failure`

## Idempotency doctrine

Legal object promotion is idempotent by default.

**Default canonical identity:** `parsed_structure_id` only.

Do **not** include in default idempotency identity:

- `promotion_reason`
- `requested_by_actor_type` / actor identifier
- `requested_at`
- database IDs generated at write time
- `notes`

The same `parsed_structure` must not receive uncontrolled duplicate default promotions. Changing `promotion_reason` must not create additional default legal objects.

If promotion already succeeded for the `parsed_structure`, reject, skip, or return `duplicate_rejected` unless `force_repromotion=True`.

Future implementation should enforce idempotency at **application**, **worker**, and **database** layers (mirroring TASK-006P1 / TASK-006R patterns). Recommended DB pattern: partial unique index on `parsed_structure_id` WHERE `force_repromotion = false`.

## Force-repromotion doctrine

`force_repromotion`:

- explicit replay bypass for intentional re-promotion
- requires actor and `promotion_reason`
- must remain auditable (new append-only request/result rows)
- required to intentionally promote again after a prior successful promotion

**Clarification:** `promotion_reason` alone must not bypass idempotency or duplicate protection.

There is no separate `rerun_allowed` flag in this contract; `force_repromotion` is the sole explicit bypass.

## Promotion hash doctrine

Future default `promotion_hash` is derived from stable canonical identity only.

**Default (`force_repromotion=false`):**

- `parsed_structure_id`

**Force replay (`force_repromotion=true`):**

- unique per governed replay request (e.g. `parsed_structure_id` + force flag + replay nonce) to preserve append-only audit history

Do **not** include in default hash:

- `promotion_reason`
- actor fields
- timestamps
- `notes`

Optional future extension: include promotion policy version or legal-object schema generation only when architecture explicitly requires multiple default promotion paths per `parsed_structure`.

## Handoff boundary

Promotion may hand off to legal-object materialization by creating or referencing `legal_object` records (per existing 003x governance where applicable).

This contract does **not** implement:

- promotion persistence tables
- promotion workers
- legal-object write execution
- citation or answer generation

## Legal meaning boundary

Legal object creation (when implemented) may:

- normalize canonical memory shape
- preserve structural units and identifiers from `parsed_structure`
- preserve lineage and hashes

Legal object creation must **not**:

- infer legal consequence
- infer tax effect
- infer taxpayer obligations
- infer applicability or temporal legal force
- generate advice or interpret law beyond structural normalization

**Parsing phase doctrine carries forward:** `parsed_structure` ≠ legal meaning. **Promotion phase doctrine:** `parsed_structure` ≠ legal object until governed promotion succeeds.

## Temporal governance alignment

Promotion must preserve:

- `source_version` identity and recorded temporal fields (`effective_from`, `effective_to`, `enforcement_date`, `publication_date`) as-is
- version lineage and `supersedes_version_id` where present
- no silent inference of effective/applicability/repeal dates
- no assumption that latest `source_version` equals applicable law

Promotion must **not** infer dates, applicability, legal force, or temporal status.

## Provenance requirements

Every promotion record and resulting legal object must preserve unbroken lineage:

```text
source_version
  → extraction_run
  → extracted_text
  → parser_run
  → parsed_structure
  → legal_object
```

No break in lineage is permitted. Promotion requests must record `parsed_structure_id` and `source_version_id` consistently with stored artifacts.

## Citation boundary

```text
legal_object ≠ citation
```

Citation assembly (TASK-004D and successors) remains separate governed work. Promotion does not create citation anchors, citation text, or answer-ready outputs.

## Relationship to prior legal-object contracts

Existing contracts (`LEGAL_OBJECT_CONTRACT.md`, 002G–003E persistence, 004A retrieval) govern legal-object shape, repository writes, and retrieval from **converged candidates** and related paths.

This contract governs **ingestion-pipeline promotion** from `parsed_structure` evidence. Implementations must not conflate automatic parsing output with governed promotion without an explicit promotion request and result trail.

## Failure handling

Failures must be:

- persisted in append-only promotion results (future)
- queryable by operators and auditors
- not silently retried without explicit policy
- non-destructive to canonical `parsed_structure` and prior promotion history

## Concurrency doctrine (OD-021)

Today's orchestration may be single-worker. Future concurrent legal-object promotion workers must mitigate:

- execution-time replay race (read-check-then-act between workers)
- duplicate promotion execution for the same `parsed_structure`

Recommended future mitigations (implementation in TASK-006V+ / worker hardening, not 006U):

- row-level locking on promotion or legal-object rows
- PostgreSQL advisory locks keyed by `parsed_structure_id`
- execution-level uniqueness guards aligned with idempotency doctrine

TASK-006U defines doctrine only; no concurrency implementation is required here.

## Non-implementation clause

TASK-006U authorizes governance only, not promotion persistence, workers, or legal-object execution.

## Final principle

A legal object is canonical legal memory.

Creating canonical legal memory is a **governed promotion decision**, not an automatic parsing outcome.
