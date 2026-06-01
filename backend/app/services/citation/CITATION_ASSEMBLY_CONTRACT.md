# Citation Assembly Contract (TASK-004D)

## Purpose

Deterministically assemble source-backed citations from legal objects, source documents,
and pinned source versions.

```text
Legal Objects + Source References + Source Versions + Locations = Deterministic Citations
```

This establishes **Authority → Citation**, not **Authority → Meaning**.

## Architecture position

```text
004A Retrieval → 004B Effective-Date Resolution → 004C Citation Candidate → 004D Citation Assembly
```

## Module

`backend/app/services/citation/`

| File | Role |
|------|------|
| `contract.py` | Governance boundary |
| `models.py` | `CitationResult`, `AuthorityType`, `CitationAssemblyRequest` |
| `assembler.py` | `CitationAssembler` |
| `formatter.py` | `CitationFormatter` (presentation only) |
| `location.py` | Location reference construction |
| `hash.py` | `citation_hash` / `citation_id` |

## Version awareness

Citations require an explicit `legal_object_version_id` on input **and** on output (`CitationResult.legal_object_version_id`).
The assembler never resolves “latest” or `current_version_id` implicitly.

Citations are version-pinned outputs, not only version-pinned inputs.

## Citation identity

- `citation_hash` and `citation_id` include `legal_object_version_id`.
- Citation identity must **not** rely on `legal_object_id` alone.
- Same `legal_object_id` with different `legal_object_version_id` values must produce different `citation_hash` and `citation_id`.

## Source traceability

Assembly fails when:

- `source_version_id` cannot be resolved
- `location_reference` cannot be built (missing `object_label`)
- `source_version.source_document_id` does not match `legal_object.source_document_id` (`SourceDocumentMismatchError`)

## Hash

`citation_hash = SHA-256(source_version_id | legal_object_id | legal_object_version_id | location_reference)`

## Immutability

Assembled citations are in-memory DTOs only — **no persistence** in TASK-004D.

## Prohibited

Answer generation, citation ranking, authority weighting, legal reasoning, AI, semantic
search, retrieval, topic classification, cross-regime analysis, API routes, persistence.
