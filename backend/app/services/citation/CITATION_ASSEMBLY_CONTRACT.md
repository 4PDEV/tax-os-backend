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

## Temporal metadata on citations (TASK-005B — resolves C1)

Citation assembly must distinguish three classes of temporal information:

| Class | Source | Use in citation |
|-------|--------|-----------------|
| **Source version temporal metadata** | `source_versions` (publication, instrument effective dates) | May appear only when labeled as source-level metadata |
| **Legal object temporal applicability** | `legal_object_versions.effective_from` / `effective_to` | Primary dates for provision applicability in citation output |
| **Citation assembly timestamp** | `CitationResult.assembled_at` | When the citation DTO was built — not legal effective date |

### Rules (governance)

1. Citations may display effective dates **only when** those dates come from the legal object version or from **explicitly provenance-marked** inherited/derived metadata.
2. Citations must **not** silently treat `source_version.effective_from` / `effective_to` as legal-object applicability dates.
3. If the legal object version has **no** effective dates, citation output must **not** imply applicability dates by falling back to source-version dates without provenance disclosure.
4. Missing dates remain **unknown** — not inferred.

### Implementation note

Current `CitationAssembler` uses `version.effective_from or source_version.effective_from` for `CitationResult` and formatter input. This pattern is **non-compliant with Addendum V6** and must be remediated in a future bounded implementation task. TASK-005B updates governance only.

## Immutability

Assembled citations are in-memory DTOs only — **no persistence** in TASK-004D.

## Prohibited

Answer generation, citation ranking, authority weighting, legal reasoning, AI, semantic
search, retrieval, topic classification, cross-regime analysis, API routes, persistence.
