# Legal Object Candidate Convergence Contract

## Purpose

Resolve **OD-010** at the contract level before any legal object persistence.

Two upstream pipelines currently produce candidate-like outputs:

```text
segmentation      → legal_objects/           (legacy segment-backed)
structure_parser  → legal_object_extraction/ (structural-unit-backed)
```

This module defines a **convergence boundary**: all candidates must normalize to one
canonical shape and identity policy before persistence planning may proceed.

## Governance boundary

Convergence performs:

- canonical candidate shape enforcement
- upstream source classification
- deterministic mapping from legacy segment candidates
- validation and identity verification
- explicit rejection of unmappable inputs

Convergence does **not** perform:

- legal interpretation
- topic classification
- authority ranking
- conflict resolution
- citation generation
- database persistence
- AI or embeddings

## Canonical candidate model

The canonical model is:

`app.services.legal_object_extraction.models.LegalObjectCandidate`

All persistence-bound workflows must consume converged candidates in this shape.

## Canonical identity

The canonical identity generator is:

`app.services.legal_object_extraction.identity.generate_legal_object_id`

Format: `lo_<sha256-first-32-hex-chars>` from stable inputs
(`source_version_id`, `canonical_path`, `object_type`, `object_label`,
`start_offset`, `text_hash`).

No other legal object ID generator may be used going forward unless approved
by architecture addendum. Legacy `lo-NNNN` segment IDs are **not** canonical.

## Accepted upstream pipelines

| Source | Enum | Behavior |
|--------|------|----------|
| Structural extraction | `STRUCTURAL_UNIT` | Pass-through as `CANONICAL` (or `PARTIAL` if upstream status is partial) |
| Segment extraction | `SEGMENT` | Map into canonical model as `MAPPED` or `PARTIAL` |
| Unrecognized legacy | `LEGACY` / `UNKNOWN` | `REJECTED` unless explicitly mapped |

## Mapping rules

### Structural candidates

Structural-unit-backed candidates from `legal_object_extraction` are already
canonical. The mapper validates identity and returns `CANONICAL`.

### Segment candidates

Segment-backed candidates from `legal_objects` are mapped deterministically:

- `object_type` — surface mapping to canonical `LegalObjectType` (unmapped → `UNKNOWN`)
- `object_label` — from legacy `object_label` or `heading` (required)
- `canonical_path` — legacy `object_label` (single-node; batch path enrichment deferred)
- `structural_unit_id` — legacy `source_segment_id` (traceability)
- `legal_object_id` — regenerated via canonical identity generator
- `text_hash` — `SHA256(raw_text)`
- `parent_legal_object_id` — set to `None`; legacy parent IDs cannot be resolved
  without batch context → `PARTIAL` with warning

Unmappable segment candidates (missing label, missing text, wrong type) return
`REJECTED` explicitly — never silently dropped.

## Validation rules

`LegalObjectCandidateValidator` checks:

- required fields present (`legal_object_id`, `source_version_id`, `canonical_path`, `raw_text`)
- `text_hash == SHA256(raw_text)`
- `legal_object_id` matches canonical generator output
- offsets are valid (`end_offset >= start_offset`)
- duplicate ID detection available via `check_duplicate_ids()`

## Rejected candidate behavior

`REJECTED` convergence status includes explicit warnings explaining failure.
Unmappable inputs are never silently accepted.

## Persistence blocker rule

**No legal object persistence may proceed until candidates pass through this
convergence boundary.**

OD-010 is governed at contract level by this module. Persistence tasks must
consume `ConvergedLegalObjectCandidate` outputs only.

## Future deprecation path

- `legal_objects/` segment-backed extractors remain available but are **legacy**
  for identity purposes.
- New work should prefer: `structure_parser` → `legal_object_extraction` → convergence.
- Segment path must always map through `LegalObjectCandidateMapper.from_segment_candidate`.
- Architecture may later deprecate segment-backed extraction entirely once structural
  pipeline coverage is sufficient.

## Limitations

- Single-candidate segment mapping cannot resolve legacy parent IDs to canonical
  parent IDs without batch context.
- Canonical path for segment candidates uses label-only paths until batch lineage
  enrichment is approved.
- Convergence does not merge duplicate candidates across pipelines — deduplication
  is a future persistence concern.

## Module layout

```text
legal_object_convergence/
├── contract.py      # governance boundary, LegalObjectConvergenceError
├── enums.py         # ConvergenceSource, ConvergenceStatus
├── models.py        # ConvergedLegalObjectCandidate
├── mapper.py        # LegalObjectCandidateMapper
└── validator.py     # LegalObjectCandidateValidator
```
