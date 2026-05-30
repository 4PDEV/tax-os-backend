# Effective-Date Resolver Contract (TASK-004B)

## Purpose

Deterministic resolution of which legal object versions apply on a given date.
Builds on TASK-004A retrieval; prepares time-aware citation and answer assembly.

This module performs **time-aware legal memory resolution** — NOT legal reasoning.

## Core boundary

Resolves applicability by date only. No interpretation, ranking, citations, AI,
embeddings, or semantic search.

## Module

`backend/app/services/effective_date/`

| File | Role |
|------|------|
| `contract.py` | Governance boundary |
| `models.py` | Request/result models and `ResolutionStatus` |
| `resolver.py` | `EffectiveDateResolver` |
| `exceptions.py` | Explicit resolver errors |

## Date rule

```text
effective_from <= effective_on
AND (effective_to IS NULL OR effective_to >= effective_on)
```

NULL `effective_from` → unbounded past (consistent with TASK-004A).

## Resolution statuses

| Status | Meaning |
|--------|---------|
| `applicable` | Exactly one version matches; effective dates present |
| `not_applicable` | No version matches the date rule |
| `ambiguous_overlap` | Multiple versions match — no silent selection |
| `missing_effective_date` | Matching version has both dates NULL |
| `integrity_failed` | Hash/traceability verification failed |

## Ambiguous overlap

When more than one version of the same `legal_object_id` applies on `effective_on`,
returns `ambiguous_overlap` — addresses TASK-004A deferred hardening.

## Prohibited

Answer generation, citation assembly, embeddings, pgvector, RAG, AI, authority ranking.

## Out of scope

API routes, frontend, cross-regime logic.
