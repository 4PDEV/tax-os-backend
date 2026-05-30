# Cross-Reference Detection Contract

Deterministic cross-reference detection layer (TASK-002E) that identifies
structural references between legal and business authority sources in text.

Detection is strictly: **identify, record, link** — NOT interpret, prioritize,
or reason.

## Non-negotiable principles

Cross-reference detection must be deterministic, reproducible, traceable, and
source-backed. The system must **never** infer legal meaning, authority hierarchy,
legal consequences, or legal interpretation.

## Module layout

```text
backend/app/services/cross_reference/
├── contract.py    # governance boundary + CrossReferenceDetectionError
├── enums.py       # ReferenceType, ReferenceConfidence
├── models.py      # CrossReferenceResult (Pydantic)
├── patterns.py    # deterministic regex patterns
└── detector.py    # CrossReferenceDetector.detect()
```

## CrossReferenceResult

| Field | Meaning |
|-------|---------|
| `source_version_id` | Source version (required — no orphan references) |
| `source_location` | Character offset span `start:end` in scanned text |
| `reference_text` | Matched reference surface form (e.g. `Section 42`) |
| `reference_type` | Structural type (`ReferenceType`) |
| `target_candidate` | Literal target string when extractable (e.g. `VAT Act`) |
| `confidence` | `high` / `medium` / `low` (deterministic, not probabilistic) |
| `detected_at` | UTC timestamp |
| `detector_version` | Detector version for reproducibility |

Model uses `extra="forbid"`.

## Reference types

`section`, `article`, `regulation`, `schedule`, `part`, `chapter`, `act`, `law`,
`guidance`, `case`, `treaty`, `unknown`. Structural labels only — no semantic
classification.

## Confidence model

| Level | Pattern class |
|-------|----------------|
| `high` | Explicit single references (`Section 15`, `Article 8`, …) |
| `medium` | Explicit ranges (`Sections 12-15`, `Articles 1-3`) |
| `low` | Vague phrases (`the above provision`, `aforementioned`, …) |

## Supported patterns (initial)

- Section X / Sections X-Y
- Article X / Articles X-Y
- Regulation X
- Schedule X
- Part X
- Chapter X

Target extraction: ``Section 42 of the VAT Act`` → `reference_text: "Section 42"`,
`target_candidate: "VAT Act"`.

## CrossReferenceDetector

```python
results = CrossReferenceDetector().detect(
    source_version_id=version_id,
    text="See Section 42 of the VAT Act.",
)
```

Returns `list[CrossReferenceResult]`. Empty list when no matches.

## Storage

This task introduces **no** database persistence, graph storage, or registry
storage. It establishes the contract, detector, patterns, and tests only.

## Out of scope

Graph databases, knowledge graphs, legal reasoning, citation ranking, authority
hierarchy, conflict resolution, topic classification, embeddings, and AI extraction.
