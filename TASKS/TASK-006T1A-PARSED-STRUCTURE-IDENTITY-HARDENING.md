# TASK-006T1A — Parsed Structure Identity Hardening

## Status

**Complete — verified** at `checkpoint-task-006t1a-parsed-structure-identity` (2026-06-02)

## Issue summary (Claude P-01)

`parsed_structures.parser_run_id` had a plain index only. Multiple `parsed_structure` rows could theoretically attach to one `parser_run` under race or accidental replay.

## Remediation summary

| Layer | Change |
|-------|--------|
| Database | `UNIQUE(parser_run_id)` — `uq_parsed_structures_parser_run_id` |
| Service | `persist_parsed_structure()` duplicate rejection preserved |
| Replay | `force_reparse` creates new `parser_run` → new structure row (unchanged) |

Migration: `a4d2e8f93b36`

## Hash integrity summary

`sha256_structure()` reviewed — no changes required. Canonical unit fields only; volatile metadata excluded (see `test_ingestion_hashing.py` + `test_parsed_structure_identity_hardening.py`).

## Tests

| File | Coverage |
|------|----------|
| `test_parsed_structure_identity_hardening.py` | Service duplicate, DB constraint, force_reparse, hash stability |
| `test_parsed_structure_identity_alembic_migration.py` | Migration upgrade/downgrade, constraint presence |

## Remaining deferred

- OD-021 execution-time worker race (unchanged)
- Legal-object promotion gate **open**; TASK-006U contract approved next

## Final principle

A `parser_run` may produce only one canonical `parsed_structure`. Replay must create a new `parser_run`, not overwrite structure history.
