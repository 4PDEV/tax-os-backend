# Citation Candidate Contract (TASK-004C)

## Purpose

Convert trusted legal object retrieval/resolution results into citation-ready
candidate DTOs for future citation assembly.

This establishes **citation readiness** — not citation authority, legal interpretation,
or answer generation.

## Architecture position

```text
004A Retrieval → 004B Effective-Date Resolution → 004C Citation Candidate Preparation
```

## Module

`backend/app/services/citation_candidate/`

| File | Role |
|------|------|
| `contract.py` | Governance boundary |
| `models.py` | `CitationCandidateRequest`, `CitationCandidate`, `CandidateStatus` |
| `builder.py` | `CitationCandidateBuilder` |
| `exceptions.py` | Explicit builder errors |

## Builder methods

- `build(request)` — uses resolver when `effective_on` set; retrieval otherwise
- `build_from_retrieval_result()` — from `LegalObjectRetrievalResult`
- `build_from_resolution_result()` — from `EffectiveDateResolutionResult`

## Resolution status mapping

| Resolution (004B) | Candidate status |
|-------------------|------------------|
| `applicable` | `ready` |
| `ambiguous_overlap` | `date_ambiguous` |
| `not_applicable` | `date_not_applicable` |
| `missing_effective_date` | `missing_effective_date` |
| `integrity_failed` | `integrity_failed` |

No silent conversion of ambiguous or missing-date cases to `ready`.

## Source traceability

Candidates include metadata from `source_documents`, `source_versions`, `countries`,
and `tax_types` where available. Missing required linkage → `source_traceability_failed`.

## Immutability

Citation candidates are in-memory DTOs only — **no persistence** in TASK-004C.

## Prohibited

Final citation formatting, style rules, AI, RAG, embeddings, semantic retrieval,
API routes, database migrations, candidate persistence.

## Out of scope

Answer generation, authority hierarchy weighting, legal interpretation.
