# Structural Source Segmentation Contract

Deterministic segmentation layer (TASK-002B) that converts raw extracted text
into ordered, hierarchy-aware structural segments.

Segmentation is strictly:

```text
RAW EXTRACTED TEXT → STRUCTURED TEXT SEGMENTS
```

## Non-negotiable principles

Segmentation must be deterministic, reproducible, traceable, non-interpretive,
hierarchy-aware, and source-faithful. The layer must **never** infer legal
meaning, rewrite text, summarize, classify legal intent, or invent structure
not present in the source. Original text order and fidelity are preserved.

## Module layout

```text
backend/app/services/segmentation/
├── contract.py        # governance boundary + SegmentationError
├── enums.py           # SegmentType, SegmentationStatus
├── models.py          # Segment, SegmentationResult, metadata (Pydantic)
└── segmenters/
    ├── base.py        # BaseSegmenter (can_handle, segment)
    ├── generic.py     # GenericSegmenter (fully implemented)
    └── legislative.py # LegislativeSegmenter (skeleton, NotImplementedError)
```

## SegmentationResult

| Field | Meaning |
|-------|---------|
| `source_version_id` | Source version being segmented |
| `segmentation_status` | `pending` / `success` / `failed` / `partial` |
| `segmenter_name` | Segmenter identity (traceability) |
| `segmenter_version` | Segmenter version (reproducibility) |
| `segmented_at` | UTC timestamp |
| `segment_count` | Number of segments (must equal `len(segments)`) |
| `segments` | Ordered list of `Segment` |
| `metadata` | `SegmentationMetadata` (observational only) |

## Segment

| Field | Meaning |
|-------|---------|
| `segment_id` | Deterministic id (`seg-NNNN` by sequence) |
| `segment_type` | Structural label (`SegmentType`) |
| `hierarchy_level` | Tree depth (`document` = 0) |
| `parent_segment_id` | Parent segment id (`None` for root) |
| `sequence_number` | Stable ordering index |
| `heading` | Structural marker line, if any |
| `raw_text` | Exact substring `source[start:end]` |
| `start_offset` / `end_offset` | Character offsets into extracted text |
| `metadata` | `SegmentMetadata` (counts, matched marker) |

All models use `extra="forbid"` so interpretive content cannot leak into the
contract.

## Segment types

Structural labels only: `document`, `part`, `chapter`, `section`, `article`,
`clause`, `subclause`, `paragraph`, `schedule`, `unknown`. These carry no legal
semantics.

## GenericSegmenter

Deterministic and source-faithful:

1. Emits a root `DOCUMENT` segment spanning the entire text.
2. Splits the body into blocks on blank-line boundaries (offsets preserved).
3. Labels each block via surface markers (e.g. `Article 1`, `(a)`, `1.`).
4. Resolves parent/child links using structural ranks; `hierarchy_level` is the
   resulting tree depth.

Guarantees:

- `raw_text == source[start_offset:end_offset]` for every segment.
- Identical input produces identical segments across runs.
- No semantic interpretation, summarization, or legal inference.

## LegislativeSegmenter

Skeleton only. Inherits `BaseSegmenter` and raises `NotImplementedError`.
Advanced legislative parsing is out of scope for this task.

## Storage

This task does **not** persist segments to the database. It establishes the
contract, models, and deterministic behavior only; persistence is a later task.
