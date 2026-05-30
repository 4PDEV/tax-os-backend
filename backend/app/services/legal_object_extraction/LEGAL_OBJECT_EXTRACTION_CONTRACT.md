# Legal Object Extraction Contract

Proto-legal object extraction layer (TASK-002G): **Structural Units → Legal Object Candidates**.

This is the first proto-legal-intelligence boundary. It introduces canonical
identity, lineage, deterministic paths, and object-level text hashing — but
performs **no** legal interpretation, persistence, or AI.

## Purpose

Convert `StructuralUnit` outputs from `structure_parser` into source-backed
`LegalObjectCandidate` records suitable for later validation, persistence,
citation anchoring, effective-date resolution, and topic mapping.

Candidates are **not** approved legal knowledge.

## Governance boundary

This module extracts legal object candidates only:

- no legal interpretation
- no topic classification
- no authority ranking
- no conflict resolution
- no citation or answer generation
- no persistence

## Input contract

```python
list[StructuralUnit]  # from app.services.structure_parser
```

No parallel structural model. No duplication of parser models.

## Output contract

```python
list[LegalObjectCandidate]
```

Key fields: `legal_object_id`, `canonical_path`, `parent_legal_object_id`,
`structural_unit_id`, `text_hash`, `extraction_status`, offsets, `raw_text`.

Pydantic model uses `extra="forbid"`.

## Deterministic identity

```text
legal_object_id = lo_<sha256-first-32-hex>
```

Stable inputs: `source_version_id`, `canonical_path`, `object_type`,
`object_label`, `start_offset`, `text_hash`.

No random UUIDs.

## Canonical path

Built from structural lineage using unit labels only, joined by ` > `:

```text
PART I > CHAPTER 1 > Section 15
```

Root unit: `canonical_path = object_label`.

## Object type mapping

Surface mapping from `StructuralUnitType` → `LegalObjectType`. Unmapped → `UNKNOWN`.

## Parent lineage

`parent_legal_object_id` references the parent's **legal object id**, not the
structural unit id. Missing structural parent in input batch → `PARTIAL` status;
candidate preserved.

## Text hash

`SHA256(raw_text)` — no normalization beyond upstream fidelity.

## Ordering

Output order matches structural unit input order (document order).

## Storage

**No** database models, migrations, CRUD APIs, or repository layer.

## Limitations

- Candidates are not validated legal objects
- No resolution to registry entities
- No integration with citation anchors or cross-references yet
- Relationship to prior `legal_objects` module (TASK-002C segment-backed candidates) is a separate architectural decision (OD-010)

## Usage

```python
from app.services.legal_object_extraction import LegalObjectExtractor
from app.services.structure_parser import StructuralParser

units = StructuralParser().parse(source_version_id=version_id, text=extracted_text)
candidates = LegalObjectExtractor().extract(units)
```
