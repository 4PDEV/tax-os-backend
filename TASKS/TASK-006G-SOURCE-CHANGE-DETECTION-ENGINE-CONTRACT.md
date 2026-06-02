# TASK-006G — Source Change Detection Engine Contract

## Status

APPROVED FOR IMPLEMENTATION

## Objective

Define bounded governance for future source change detection over fetched artifacts without legal interpretation.

This task is contract-only and governance-only.

## Canonical Contract

Primary specification:

- `SOURCE_CHANGE_DETECTION_ENGINE_CONTRACT.md`

Task record:

- `TASKS/TASK-006G-SOURCE-CHANGE-DETECTION-ENGINE-CONTRACT.md`

## Scope Summary

Define:

- change detection role and boundaries
- request/result contracts
- detection status/change type/confidence enumerations
- checksum/metadata/structural diff doctrine
- duplicate and false-positive doctrine
- temporal no-inference alignment
- review-required policy
- provenance/audit requirements
- failure taxonomy

## Explicit Prohibitions

- no change-detection engine implementation
- no diff algorithm implementation
- no live fetch/crawl/scrape
- no amendment/legal interpretation
- no automatic source version creation
- no legal object/citation/answer generation

## Acceptance

TASK-006G is complete when:

- contract artifacts exist
- bounded values and doctrines are explicit
- review-before-source-version workflow is explicit
- docs are realigned with no implementation scope creep

## Final Principle

Change detection identifies potential source change only. Legal meaning remains a governed review concern.
