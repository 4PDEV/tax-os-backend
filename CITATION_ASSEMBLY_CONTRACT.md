# Citation Assembly Contract

## Purpose

Define governed boundaries for assembling citations from canonical `legal_object` legal memory.

This contract is governance-only. It does not authorize citation persistence, citation workers, citation execution, retrieval runtime, or answer generation.

## Core principle

**A citation is a governed reference to canonical legal memory.**

A citation is **not**:

- legal meaning
- legal advice
- tax advice
- applicability determination
- answer generation
- legal conclusion

## Mandatory doctrines

| Doctrine | Rule |
|----------|------|
| `legal_object` ≠ citation | Citation assembly is a separate governed transition |
| `citation` ≠ answer | Citations may support future answers; they are not answers |
| `citation` ≠ legal meaning | Structural/authority references only — no interpretation |
| `citation` ≠ taxpayer applicability | No obligation or taxpayer-effect determination |
| `citation` ≠ legal conclusion | No consequence or legal-force inference |

## Citation role

Citation assembly is responsible for:

- validating `legal_object` / `legal_object_version` eligibility for citation assembly review
- recording who requested assembly and why
- producing auditable citation assembly state transitions
- enforcing idempotency and duplicate controls
- defining `force_reassembly` replay doctrine
- defining handoff semantics to citation materialization (future tasks)
- preserving full provenance chain integrity through citation outputs

Citation assembly must not:

- interpret law, authority, or relevance
- determine applicability, taxpayer obligations, or legal consequence
- generate advice, answers, or retrieval results
- infer temporal legal force or applicability windows
- mutate temporal fields on `source_version` or `legal_object_version`
- use AI/LLMs

## Citation boundary

```text
legal_object → citation assembly review → citation
```

Citation creation is a **governed process**. Citation creation is **not** answer generation.

Completing legal object promotion does **not** imply citation approval or citation existence.

## Relationship to TASK-004D citation assembler

Existing service governance at [`backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md`](backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md) (TASK-004A–004D) defines **deterministic citation text assembly** from version-pinned legal objects in the converged-candidate / retrieval path.

This contract governs **ingestion-pipeline citation assembly** from promoted canonical legal memory (006U–006X). Future implementations must:

- preserve both governance layers without conflating request/result lifecycle with formatter/assembler DTO rules
- align version-pinned identity (`legal_object_version_id`) across layers
- not bypass temporal or provenance doctrines defined here or in 004D/005B

## Eligibility rules

A `legal_object` / `legal_object_version` pair is citation-assembly-eligible only when:

- `legal_object` exists and is canonical/preserved
- `legal_object_version` exists for that `legal_object`
- version status is valid per legal-object persistence governance (003E)
- provenance chain is complete:

```text
source_version
  → extraction_run
  → extracted_text
  → parser_run
  → parsed_structure
  → legal_object
  → legal_object_version
```

- temporal lineage is traceable (`source_version_id`, recorded effective/enforcement/publication fields as stored — not inferred)
- default citation assembly has not already succeeded for this `legal_object_version` unless `force_reassembly=True`

Eligibility is evaluated against the **canonical assembly target** (`legal_object_version_id`), not mutable request metadata.

## CitationAssemblyRequest contract (future)

Required fields:

- `citation_assembly_request_id`
- `legal_object_id`
- `legal_object_version_id`
- `citation_reason`
- `requested_by_actor_type`
- `requested_by_actor_identifier` (nullable)
- `requested_at`
- `force_reassembly`
- `notes` (nullable)

Allowed `requested_by_actor_type` values (future implementation):

- `user`
- `system`
- `worker`
- `admin`
- `test`

`citation_reason` records governance intent. It does **not** bypass idempotency.

## CitationAssemblyResult contract (future)

Required fields:

- `citation_assembly_request_id`
- `legal_object_id`
- `legal_object_version_id`
- `citation_status`
- `citation_id` (nullable)
- `assembled_at` (nullable)
- `error_category` (nullable)
- `error_message` (nullable)
- `citation_hash` (nullable)
- `notes` (nullable)

## Citation status values

Allowed `citation_status` values only:

- `pending`
- `accepted`
- `rejected`
- `assembled`
- `failed`
- `skipped`
- `duplicate_rejected`

`assembled` means the citation assembly lifecycle reached a terminal success handoff for the request. It does **not** imply legal meaning is correct, tax effect is known, applicability is determined, or answers are ready.

**Dry-run worker (future skeleton task):** successful orchestration may record `accepted` then `skipped` with `citation_id` null. Here `skipped` means **orchestration completed without citation execution** — not that the request was ignored.

## Citation error categories

Allowed `error_category` values only:

- `legal_object_missing`
- `version_missing`
- `provenance_incomplete`
- `duplicate_citation`
- `invalid_request`
- `citation_pipeline_unavailable`
- `unknown_failure`

## Idempotency doctrine

Citation assembly is idempotent by default.

**Default canonical identity:** `legal_object_version_id` only.

Do **not** include in default idempotency identity:

- `citation_reason`
- `requested_by_actor_type` / actor identifier
- `requested_at`
- database IDs generated at write time
- `notes`

**One default citation per `legal_object_version`.** Changing `citation_reason` must not create additional default citations.

If citation assembly already succeeded for the `legal_object_version`, reject, skip, or return `duplicate_rejected` unless `force_reassembly=True`.

Future implementation should enforce idempotency at **application**, **worker**, and **database** layers (mirroring TASK-006P1 / TASK-006R / TASK-006V patterns). Recommended DB pattern: partial unique index on `legal_object_version_id` WHERE `force_reassembly = false`.

## Force-reassembly doctrine

`force_reassembly`:

- explicit replay bypass for intentional re-assembly
- requires actor and `citation_reason`
- must remain auditable (new append-only request/result rows)
- required to intentionally assemble again after a prior successful assembly

**Clarification:** `citation_reason` alone must not bypass idempotency or duplicate protection.

There is no separate `rerun_allowed` flag in this contract; `force_reassembly` is the **only** approved replay bypass.

## Citation hash doctrine

Future default `citation_hash` for ingestion-pipeline assembly identity is derived from stable canonical identity only.

**Default (`force_reassembly=false`):**

- `legal_object_version_id`

**Force replay (`force_reassembly=true`):**

- unique per governed replay request (e.g. `legal_object_version_id` + force flag + replay nonce) to preserve append-only audit history

Do **not** include in default hash:

- `citation_reason`
- actor fields
- timestamps
- `notes`

Optional future extension: include assembly policy version or citation schema generation only when architecture explicitly requires multiple default assembly paths per `legal_object_version`.

Rendered citation content hashes (TASK-004D assembler) remain governed separately and must continue to version-pin `legal_object_version_id` in output identity.

## Handoff boundary

Citation assembly may hand off to citation materialization by creating or referencing governed `citation` records (future persistence — TASK-006Z and successors).

**Planned persistence shape (006ZA):** See [`CITATION_PERSISTENCE_REMEDIATION_006ZA.md`](CITATION_PERSISTENCE_REMEDIATION_006ZA.md). Governance ORM: `CitationAssemblyGovernanceRequest` / `Result`; `request_hash` idempotency. **TASK-006Z authorized** for append-only persistence implementation ([`CITATION_PERSISTENCE_006ZA_ACCEPTANCE_REVIEW.md`](CITATION_PERSISTENCE_006ZA_ACCEPTANCE_REVIEW.md)). Citation execution not authorized.

This contract does **not** implement (by itself):

- citation persistence tables
- citation workers
- citation write execution
- retrieval or answer generation

## Citation content doctrine

A citation may:

- identify authority (as stored on source/legal-object lineage)
- identify location (structural reference from legal memory)
- identify structural reference (labels, paths, units)
- preserve provenance and version pins

A citation must **not**:

- interpret authority
- determine relevance
- determine applicability
- determine consequence

## Temporal governance alignment

Citation assembly must preserve:

- `source_version` identity and recorded temporal fields as-is
- `legal_object_version` effective/enforcement lineage as stored
- version identity and `supersedes_version_id` where present
- no silent inference of effective/applicability/repeal dates
- no assumption that latest version equals applicable law

Citation assembly must **not**:

- infer dates
- infer applicability windows
- infer legal force
- infer temporal status

Align with [`TEMPORAL_VERSIONING_ARCHITECTURE.md`](TEMPORAL_VERSIONING_ARCHITECTURE.md) and TASK-005B citation temporal rules in the 004D assembler contract.

## Provenance requirements

Every citation assembly record and resulting citation must preserve unbroken lineage:

```text
source_version
  → extraction_run
  → extracted_text
  → parser_run
  → parsed_structure
  → legal_object
  → legal_object_version
  → citation
```

No break in lineage is permitted. Assembly requests must record `legal_object_id` and `legal_object_version_id` consistently with stored artifacts.

## Answer boundary

```text
citation ≠ answer
```

A citation may later support answer assembly in governed future phases. A citation is **not** itself an answer, legal advice, or taxpayer guidance.

## Retrieval boundary

```text
citation ≠ retrieval result
```

Retrieval (TASK-004A, TASK-007A+ runtime) selects or ranks legal memory. Citation assembly produces governed reference artifacts. Neither substitutes for the other.

## Failure handling

Failures must be:

- persisted in append-only citation assembly results (future)
- queryable by operators and auditors
- not silently retried without explicit policy
- non-destructive to canonical legal objects and prior assembly history

## Concurrency doctrine (OD-021)

Today's orchestration may be single-worker. Future concurrent citation assembly workers must mitigate:

- execution-time replay race (read-check-then-act between workers)
- duplicate citation execution for the same `legal_object_version`

Recommended future mitigations (implementation in TASK-006Z+ / worker hardening, not 006Y):

- row-level locking on assembly or citation rows
- PostgreSQL advisory locks keyed by `legal_object_version_id`
- execution-level uniqueness guards aligned with idempotency doctrine

TASK-006Y defines doctrine only; no concurrency implementation is required here.

## Non-implementation clause

TASK-006Y authorizes governance only, not citation persistence, workers, execution, retrieval, or answers.

## Final principle

A citation is a governed reference to canonical legal memory.

Creating a citation does not create legal meaning, legal advice, taxpayer applicability, retrieval results, or answers.
