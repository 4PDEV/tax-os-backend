# Canonical Citation Anchor Contract

Deterministic citation anchor layer (TASK-002D) that generates stable,
reproducible, structure-based citation anchors for legal object candidates.

Generation is strictly:

```text
LEGAL OBJECT CANDIDATES → CANONICAL CITATION ANCHORS
```

## Non-negotiable principles

Citation anchors must be deterministic, stable, reproducible, traceable,
hierarchy-aware, and source-faithful. They must **never** depend on AI, semantic
interpretation, mutable display formatting, generated summaries, or transient
database IDs. The same legal object candidate always produces the same canonical
anchor under identical source conditions.

## Module layout

```text
backend/app/services/citation_anchors/
├── contract.py        # governance boundary + CitationAnchorGenerationError
├── enums.py           # CitationAnchorType, GenerationStatus
├── models.py          # CanonicalCitationAnchor, result, metadata (Pydantic)
└── generators/
    ├── base.py        # BaseCitationAnchorGenerator (can_handle, generate)
    ├── generic.py     # GenericCitationAnchorGenerator (fully implemented)
    └── legislative.py # LegislativeCitationAnchorGenerator (skeleton)
```

## CanonicalCitationAnchor

| Field | Meaning |
|-------|---------|
| `citation_anchor_id` | SHA-256 of stable structural inputs (see below) |
| `source_version_id` | Source version (preserved) |
| `legal_object_id` | Originating legal object id (preserved) |
| `source_segment_id` | Originating segment id (preserved) |
| `anchor_type` | Canonical structural type (`CitationAnchorType`) |
| `canonical_anchor` | Slash-joined hierarchy path |
| `display_label` | Deterministic, non-interpretive label |
| `hierarchy_path` | Ordered list of canonical path components (root → current) |
| `sequence_number` | Stable ordering index (preserved) |
| `start_offset` / `end_offset` | Character offsets (preserved) |
| `raw_text` | Exact legal object text (preserved) |
| `metadata` | `CitationAnchorMetadata` (observational only) |

Validation: `end_offset >= start_offset`; `raw_text` and offsets preserved from
the source `LegalObjectCandidate`. `citation_anchor_count == len(citation_anchors)`
on the result. All models use `extra="forbid"`.

## Anchor types

Structural only: `document`, `part`, `chapter`, `section`, `article`, `clause`,
`subclause`, `paragraph`, `schedule`, `definition`, `unknown`. Surface-mapped from
`LegalObjectType`; all unmapped types collapse to `unknown`.

## Deterministic generation algorithm

**Path component** — one per ancestor, `<ANCHOR_TYPE>:<NORMALIZED_VALUE>`:

- Value preference: `object_label` → `heading` → `sequence_number`.
- Normalize: strip outer whitespace; internal whitespace → single hyphen;
  remove unsafe path separators (`/`, `\`).

**Hierarchy path** — ordered components from root to current object. The
`canonical_anchor` is the components joined by `/`, e.g.
`PART:I/CHAPTER:2/SECTION:12/CLAUSE:1`.

**Parent handling** — `parent_legal_object_id` is resolved recursively against
the input collection. If an ancestor is unresolvable, the anchor is generated for
the current object only and an observational warning is recorded (generation does
not fail).

**`citation_anchor_id`** — deterministic SHA-256 over the exact string:

```text
source_version_id|legal_object_id|canonical_anchor|start_offset|end_offset
```

**`display_label`** — deterministic, non-interpretive:
`<Title Case Anchor Type> <object_label or sequence_number>` (e.g. `Section 12`,
`Unknown 3`).

Never used as anchor inputs: database IDs, UUID randomness, timestamps, AI,
semantic interpretation, or raw-text hashing as the primary anchor.

## LegislativeCitationAnchorGenerator

Skeleton only. Inherits `BaseCitationAnchorGenerator` and raises
`NotImplementedError`. Legislative-aware canonical lineages are out of scope here.

## Storage

This task introduces **no** database persistence, migrations, or registry
storage. It establishes the contract and deterministic generation behavior only.
