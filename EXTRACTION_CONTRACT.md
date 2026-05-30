# Source Text Extraction Contract

Deterministic extraction layer (TASK-002A) that converts raw source files into
structured extracted-text objects.

Extraction is strictly:

```text
SOURCE FILE → RAW EXTRACTED TEXT
```

## Non-negotiable principles

Extraction must be faithful, deterministic, reproducible, traceable,
version-aware, and non-interpretive. The layer must **never** summarize, infer,
rewrite, simplify, or interpret legal meaning.

## Module layout

```text
backend/app/services/extraction/
├── contract.py        # governance boundary + ExtractionError
├── enums.py           # ExtractionStatus
├── models.py          # ExtractionResult, ExtractionMetadata (Pydantic)
├── hashing.py         # sha256_text
└── extractors/
    ├── base.py        # BaseExtractor (can_handle, extract)
    ├── txt.py         # TxtExtractor (fully implemented)
    ├── pdf.py         # PdfExtractor (skeleton, NotImplementedError)
    └── html.py        # HtmlExtractor (skeleton, NotImplementedError)
```

## ExtractionResult

| Field | Meaning |
|-------|---------|
| `source_version_id` | Source version the extraction belongs to |
| `extraction_status` | `pending` / `success` / `failed` / `partial` |
| `extractor_name` | Extractor identity (traceability) |
| `extractor_version` | Extractor version (reproducibility) |
| `extracted_at` | UTC timestamp |
| `content_hash` | SHA-256 of `raw_text` |
| `raw_text` | Text exactly as extracted (no transformation) |
| `metadata` | `ExtractionMetadata` (observational only) |

`ExtractionMetadata` carries only mechanical fields: `encoding`,
`duration_ms`, `char_count`, `line_count`, `byte_count`, `partial`, `warnings`.
Both models reject unknown fields (`extra="forbid"`) to prevent interpretive
content from leaking into the contract.

## Extraction status

Only `PENDING`, `SUCCESS`, `FAILED`, `PARTIAL` are permitted. No additional
statuses may be introduced without a contract revision.

## BaseExtractor

Every extractor implements:

- `can_handle(*, mime_type, filename) -> bool`
- `extract(*, source_version_id, content: bytes) -> ExtractionResult`

`name` and `version` are mandatory for traceability and reproducibility.

## TXT extractor

Fully implemented. Decodes UTF-8 and returns text exactly as decoded — no
normalization or trimming. Invalid UTF-8 degrades deterministically to a
`PARTIAL` result using lossy replacement plus a warning, rather than failing
silently.

## PDF / HTML extractors

Skeletons only. They inherit `BaseExtractor` and raise `NotImplementedError`.
OCR, AI extraction, and parsing logic are explicitly out of scope for this task.

## Storage

This task does **not** persist extracted text. It establishes the contract and
pipeline structure only; persistence is a later task.
