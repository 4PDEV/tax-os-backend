# Legal Object Persistence Planning Contract

## Purpose

Define the governance, boundaries, risks, and canonical persistence plan for legal
objects **before any persistence implementation**.

This module establishes **Persistence Governance** — not Persistence Implementation.

No database tables, migrations, repositories, CRUD APIs, or storage pipelines exist
here. No persistence work may proceed until this planning contract is reviewed and
approved by architecture.

## Why persistence is gated

Legal object candidates are source-backed structured inputs, not approved legal
truth. TASK-002H convergence resolved OD-010 at contract level by enforcing one
canonical candidate shape. Persistence introduces irreversible historical state;
therefore planning must precede implementation.

Risks without planning:

- duplicate or conflicting persisted identities
- lineage corruption across source versions
- silent overwrite of historical legal text
- convergence bypass from legacy pipelines
- rollback failure after partial persistence batches

## Canonical persistence inputs

The **only** approved persistence input is:

`app.services.legal_object_convergence.models.ConvergedLegalObjectCandidate`

Enforced by `assert_canonical_persistence_input()` in `contract.py`.

### Prohibited direct persistence sources

| Source | Status |
|--------|--------|
| `segmentation` | Blocked |
| `structure_parser` | Blocked |
| `legal_object_extraction` | Blocked |
| `legal_objects` (legacy segment path) | Blocked |

All upstream outputs must pass through convergence first.

## Convergence dependency

Persistence planning assumes the approved canonical flow:

```text
Source Registry
→ Source Versioning
→ Text Extraction
→ Segmentation
→ Structural Section Parser
→ Legal Object Extraction
→ Legal Object Candidate Convergence
→ [Persistence — future, not this task]
```

Rejected convergence outputs (`convergence_status=rejected`) must not be planned
for persistence.

## Planned persistence model

`PlannedLegalObjectPersistenceModel` (Pydantic, `extra="forbid"`) describes
proposed persistence concepts only:

- `legal_object_id`, `source_version_id`, `canonical_path`
- `parent_legal_object_id`, `text_hash`, offsets, `structural_unit_id`
- `effective_from`, `effective_to` (first-class; execution deferred)
- `version_status`, `lineage_chain`, `duplicate_strategy`, `persistence_status`

No SQLAlchemy. No database bindings.

## Immutability philosophy

Persisted legal objects are **append-only historical records**:

- NEVER overwrite persisted rows
- NEVER mutate historical text or canonical IDs
- ALWAYS preserve source_version_id, text_hash, offsets, canonical_path, lineage
- Supersession changes `version_status` only — not stored text

See `rules.py` for explicit NEVER and ALWAYS rule sets.

## Duplicate handling philosophy

See `duplicate_strategy.py`. Planning scenarios include:

- identical text across versions → version as new
- duplicate canonical_path → flag for review
- conflicting legal_object_id → reject
- cross-jurisdiction collision → defer to architecture addendum

No silent merge. No overwrite.

## Lineage philosophy

See `lineage_strategy.py`. Expectations:

- preserve `parent_legal_object_id` and ordered `lineage_chain`
- no orphan children without explicit partial convergence flag
- supersede without mutating historical rows
- effective-date linkage deferred to later implementation task

## Migration sequencing

See `migration_plan.py`. Proposed phases (planning only):

1. **Phase 1** — legal object persistence tables
2. **Phase 2** — lineage constraints
3. **Phase 3** — effective-date indexing
4. **Phase 4** — citation anchor persistence

Phases must not be skipped without architecture approval.

## Rollback philosophy

Rollback restores prior `version_status` and batch boundaries without deleting
historical rows. Failed persistence batches must not leave lineage in an
unrecoverable state. See `risks.py` rollback risk and ALWAYS rules.

## Risk register

See `risks.py` — mandatory explicit documentation of:

- duplicate, lineage, migration drift, historical overwrite risks
- convergence bypass and canonical ID instability
- rollback failure and cross-regime collision risks

## Blocked assumptions

See `BLOCKED_ASSUMPTIONS` in `risks.py`. Examples:

- persistence before convergence approval
- legacy `lo-NNNN` IDs as persistence keys
- in-place update when source text changes
- citation persistence before legal objects are stable

## Module layout

```text
legal_object_persistence_planning/
├── contract.py           # canonical input rule, blocked sources
├── models.py             # PlannedLegalObjectPersistenceModel
├── rules.py              # NEVER / ALWAYS persistence rules
├── duplicate_strategy.py # duplicate scenario planning
├── lineage_strategy.py   # lineage and supersession planning
├── migration_plan.py     # phased migration sequence
└── risks.py              # risk register and blocked assumptions
```

## Limitations

- No persistence execution, effective-date resolution, or citation storage
- Segment batch parent resolution in convergence remains a known gap
- Cross-pipeline deduplication strategy at persistence time is planning-only

## Out of scope (this task)

Database tables, Alembic, SQLAlchemy models, repositories, CRUD APIs, search
indexing, vector DB, embeddings, AI, and answer generation.
