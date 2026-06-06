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

### Rules (governance + implementation — TASK-004E)

1. `CitationResult.effective_from` / `effective_to` are populated **only** from `legal_object_versions.effective_from` / `effective_to`.
2. Citations must **not** silently treat `source_version.effective_from` / `effective_to` as legal-object applicability dates.
3. If the legal object version has **no** effective dates, `CitationResult` leaves applicability fields **null** — unknown, not inferred.
4. Source-version effective dates may appear only on `CitationResult.source_version_effective_from` / `source_version_effective_to` and in `citation_text` lines prefixed with **"Source version metadata:"** — never as legal-object applicability.
5. `publication_date` remains source-version metadata (`CitationResult.publication_date`); it is not legal-object applicability.
6. Missing legal-object dates remain **unknown** — not inferred from source metadata, latest version, or assembly timestamp.

### Addendum V6 compliance (TASK-004E)

- No silent `source_version` → legal_object date inheritance.
- No assumption that latest version equals applicable law.
- No silent temporal inference in assembly or formatter output.
- Unknown temporal state preserved when legal-object dates are absent.

## Immutability

TASK-004D assembles in-memory `CitationResult` DTOs. Controlled persistence is governed separately (TASK-006AD `citations` entity keyed by `citation_hash`).

## Prohibited

Answer generation, citation ranking, authority weighting, legal reasoning, AI, semantic
search, retrieval, topic classification, cross-regime analysis, API routes, persistence.
