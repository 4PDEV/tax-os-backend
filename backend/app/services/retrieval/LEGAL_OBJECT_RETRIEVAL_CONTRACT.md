# Legal Object Retrieval Contract (TASK-004A)

## Purpose

Deterministic retrieval of trusted persisted legal objects for future citation assembly,
effective-date filtering, authority grouping, and answer generation.

This task establishes **trusted legal memory retrieval** — NOT intelligent search.

## Core principle

Retrieval must be:

- deterministic
- auditable
- source-backed
- version-aware
- effective-date-aware
- integrity-aware

Retrieval must NEVER:

- infer legal meaning
- rank by AI intuition
- hallucinate
- silently suppress conflicts

## Module

`backend/app/services/retrieval/`

| File | Role |
|------|------|
| `contract.py` | Governance boundary; prohibited capabilities |
| `models.py` | `LegalObjectRetrievalRequest`, `LegalObjectRetrievalResult` |
| `filters.py` | Status and effective-date filtering; deterministic ordering |
| `exceptions.py` | Explicit retrieval failures |
| `retrieval_service.py` | `LegalObjectRetrievalService` |

## Service methods

- `retrieve()` — general deterministic retrieval
- `retrieve_by_id()` — single object; raises `LegalObjectNotFoundError`
- `retrieve_active()` — active status only
- `retrieve_effective()` — requires `effective_on` date

## Effective-date rule

```text
effective_from <= effective_on
AND (effective_to IS NULL OR effective_to >= effective_on)
```

When `effective_from` / `effective_to` are NULL, the version is treated as unbounded on that bound.

## Status filtering

Default excludes `archived` and `rejected`. `superseded` excluded unless
`include_superseded=True`. `include_archived=True` includes archived rows.

## Ordering

Deterministic only: `effective_from`, `object_identifier` (structural unit + label),
`created_at`, `legal_object_id`.

## Traceability

Every result includes `source_document_id`, `source_version_id`, `text_hash`,
`integrity_hash`, and structural `object_identifier`.

## Prohibited (TASK-004A)

No embeddings, pgvector, semantic search, BM25, RAG, AI retrieval, answer generation,
citation assembly, or ranking models.

## Out of scope

- FastAPI routes / CRUD APIs
- Ingestion wiring
- Answer engine
