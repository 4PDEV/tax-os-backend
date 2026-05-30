# Structural Section Parser Contract

Deterministic structural parser (TASK-002F) that converts extracted text into
ordered, hierarchy-aware structural units.

Parsing is strictly:

```text
Extracted Text → Structural Units
```

## Non-negotiable principles

Structural parsing must be deterministic, reproducible, traceable,
hierarchy-aware, and source-backed. The parser must preserve ordering, hierarchy,
text integrity, and structural lineage. It must **never** interpret law, infer
legal meaning, classify topics, or generate legal conclusions. No AI inference
or semantic reasoning is permitted.

## Module layout

```text
backend/app/services/structure_parser/
├── contract.py    # governance boundary + StructuralParseError
├── enums.py       # StructuralUnitType
├── models.py      # StructuralUnit (Pydantic)
├── patterns.py    # regex heading patterns + title split
├── hierarchy.py   # deterministic parent/child assignment
└── parser.py      # StructuralParser.parse()
```

## StructuralUnit

| Field | Meaning |
|-------|---------|
| `source_version_id` | Source version (required) |
| `unit_id` | Deterministic id (`su-NNNN` by document order) |
| `unit_type` | Structural type (`StructuralUnitType`) |
| `unit_label` | Structural label (e.g. `Section 15`) |
| `unit_title` | Optional title after separator (e.g. `Registration Threshold`) |
| `full_heading` | Original heading line |
| `parent_unit_id` | Parent unit id (`None` for root) |
| `hierarchy_level` | Tree depth |
| `start_offset` / `end_offset` | Span in extracted text |
| `raw_text` | Exact substring `text[start:end]` |
| `detected_at` | UTC timestamp |
| `parser_version` | Parser version for reproducibility |

Model uses `extra="forbid"`. Validation: `end_offset >= start_offset`.

## Supported heading patterns (initial)

- `PART I` / `PART 1`
- `CHAPTER I` / `CHAPTER 1`
- `Section 15` / `SECTION 15`
- `Article 5`
- `Schedule A` / `Schedule 1`
- Plus `Act`, `Law`, `Title`, `Regulation`, `Paragraph`, `Subparagraph` surface forms

Roman numerals, Arabic numerals, and lettered schedules supported.

## Heading extraction

`Section 15 — Registration Threshold` →

- `unit_label`: `Section 15`
- `unit_title`: `Registration Threshold`
- `full_heading`: original line preserved

## Hierarchy

Parent-child relationships resolved by structural rank (not legal meaning).
Example: `PART I` → parent of `CHAPTER 1` → grandparent of `Section 15`.

## StructuralParser

```python
units = StructuralParser().parse(source_version_id=version_id, text=extracted_text)
```

Returns ordered `list[StructuralUnit]`. Empty list when no structural headings found.

## Storage

This task introduces **no** database persistence. It establishes the contract,
parser, hierarchy model, and deterministic structure extraction only.

## Out of scope

Topic classification, legal interpretation, semantic parsing, embeddings, AI
extraction, persistence, graph databases, legal object generation, citation
generation, and authority ranking.
