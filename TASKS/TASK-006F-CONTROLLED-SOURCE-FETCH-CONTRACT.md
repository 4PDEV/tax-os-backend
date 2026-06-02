# TASK-006F — Controlled Source Fetch Contract

## Status

APPROVED FOR IMPLEMENTATION

## Objective

Define bounded governance for future controlled source fetching with provenance, integrity, and review-before-ingestion controls.

This task is contract-only and governance-only.

## Canonical Contract

Primary specification:

- `CONTROLLED_SOURCE_FETCH_CONTRACT.md`

Task record:

- `TASKS/TASK-006F-CONTROLLED-SOURCE-FETCH-CONTRACT.md`

## Scope Summary

Define:

- fetch role boundaries
- fetch request/result contracts
- fetch status and failure taxonomy
- content-type discipline
- checksum discipline
- storage and redirect governance
- robots/terms/licensing discipline
- rate-limit/backoff doctrine
- temporal no-inference alignment
- review-before-ingestion workflow
- security constraints

## Explicit Prohibitions

- no live HTTP requests
- no crawling/scraping/scheduling
- no queues
- no storage/fetch implementation
- no automatic source version creation
- no legal/temporal inference
- no production publication

## Acceptance

TASK-006F is complete when:

- contract artifacts exist
- values/taxonomies are explicitly bounded
- review-before-ingestion workflow is explicit
- security/robots/redirect constraints are explicit
- docs are realigned without implementation scope creep

## Final Principle

Controlled fetch acquires candidate source material only. It does not establish legal authority, legal meaning, temporal applicability, or production truth.
