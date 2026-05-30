# Legal Object Extraction Contract

Deterministic legal object layer (TASK-002C) that maps structural text segments
into canonical legal object candidates.

Extraction is strictly:

```text
STRUCTURED TEXT SEGMENTS → CANONICAL LEGAL OBJECT CANDIDATES
```

## Non-negotiable principles

Legal object extraction must be deterministic, reproducible, traceable,
non-interpretive, source-faithful, and segment-backed. The layer must **never**
infer legal meaning, summarize provisions, classify tax topics, determine legal
effect, resolve conflicts, rank authority, or generate advice.

## Module layout

```text
backend/app/services/legal_objects/
├── contract.py        # governance boundary + LegalObjectExtractionError
├── enums.py           # LegalObjectType, ExtractionStatus
├── models.py          # LegalObjectCandidate, result, metadata (Pydantic)
└── extractors/
    ├── base.py        # BaseLegalObjectExtractor (can_handle, extract)
    ├── generic.py     # GenericLegalObjectExtractor (fully implemented)
    └── legislative.py # LegislativeLegalObjectExtractor (skeleton, NotImplementedError)
```

## LegalObjectCandidate

| Field | Meaning |
|-------|---------|
| `legal_object_id` | Deterministic id (`lo-NNNN` by sequence) |
| `source_version_id` | Source version (preserved) |
| `source_segment_id` | Originating segment id (traceability) |
| `object_type` | Canonical structural type (`LegalObjectType`) |
| `object_label` | Structural label (source heading, else type name) |
| `heading` | Source heading line, if any |
| `raw_text` | Exact segment text (preserved) |
| `start_offset` / `end_offset` | Character offsets (preserved from segment) |
| `sequence_number` | Stable ordering index (preserved) |
| `parent_legal_object_id` | Parent object id (mapped from parent segment) |
| `hierarchy_level` | Tree depth (preserved from segment) |
| `metadata` | `LegalObjectMetadata` (observational only) |

Validation: `end_offset >= start_offset`; `raw_text` and offsets are preserved
from the source segment.

## LegalObjectExtractionResult

| Field | Meaning |
|-------|---------|
| `source_version_id` | Source version |
| `extraction_status` | `pending` / `success` / `failed` / `partial` |
| `extractor_name` / `extractor_version` | Traceability / reproducibility |
| `extracted_at` | UTC timestamp |
| `legal_object_count` | Must equal `len(legal_objects)` |
| `legal_objects` | Ordered list of `LegalObjectCandidate` |
| `metadata` | `LegalObjectExtractionMetadata` (observational only) |

All models use `extra="forbid"` so interpretive content cannot leak into the
contract.

## Legal object types

Structural only: `act`, `regulation`, `order`, `notice`, `judgment`, `treaty`,
`part`, `chapter`, `section`, `article`, `clause`, `subclause`, `paragraph`,
`schedule`, `definition`, `unknown`. Semantic/tax-topic types (obligation,
exemption, penalty, rate, right, prohibition, …) are explicitly out of scope.

## GenericLegalObjectExtractor

Deterministic and source-faithful. Maps each `Segment` to exactly one
`LegalObjectCandidate` using a fixed surface mapping:

| SegmentType | LegalObjectType |
|-------------|-----------------|
| `part` | `part` |
| `chapter` | `chapter` |
| `section` | `section` |
| `article` | `article` |
| `clause` | `clause` |
| `subclause` | `subclause` |
| `paragraph` | `paragraph` |
| `schedule` | `schedule` |
| `unknown` | `unknown` |
| `document` | `unknown` |

Preserves `source_version_id`, `source_segment_id`, `raw_text`, offsets,
`sequence_number`, `hierarchy_level`, and parent/child relationships. No semantic
interpretation.

## LegislativeLegalObjectExtractor

Skeleton only. Inherits `BaseLegalObjectExtractor` and raises
`NotImplementedError`. Legislative-aware container/hierarchy resolution is out of
scope for this task.

## Storage

This task introduces **no** database persistence, migrations, or registry
storage. It establishes the contract and deterministic extraction behavior only.
