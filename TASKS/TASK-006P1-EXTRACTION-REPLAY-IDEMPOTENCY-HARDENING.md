# TASK-006P1 — Extraction Replay & Idempotency Hardening

**Status:** Complete — **verified** 2026-06-02  
**Resolves:** Claude review EXT-01 / F-05, OD-019  
**Blocks cleared:** TASK-006Q gate **open**

## Issue summary

Pre-006P1, extraction trigger idempotency depended on request metadata (`trigger_reason`, `requested_by_actor_type`, `rerun_allowed`) embedded in `trigger_hash`. A plain index on `trigger_hash` allowed race-prone read-then-insert duplicates. Workers could reprocess a `source_version` when a new trigger request used different wording.

## Remediation summary

| Area | Change |
|------|--------|
| Idempotency identity | Default triggers keyed by `source_version_id` only |
| `trigger_hash` | Default: SHA-256(`source_version_id`); force: unique per replay row |
| DB | Partial unique index `uq_extraction_trigger_requests_source_version_default` WHERE `force_reprocess = false` |
| Service | `find_default_trigger_for_source_version()` rejects duplicate default triggers |
| Worker | `source_version_has_completed_extraction()` skips re-extraction unless `force_reprocess=True` |
| `rerun_allowed` | Policy flag only; does **not** bypass idempotency |
| `force_reprocess` | Explicit bypass for new trigger + new extraction run/text |

## DB constraint summary

- `UNIQUE (source_version_id) WHERE force_reprocess = false` on `extraction_trigger_requests`
- `UNIQUE (extraction_run_id)` on `extracted_texts`
- `CHECK` on `extraction_runs.extraction_status` and `parser_runs.parser_status`

Migration: `e8c1d4f92a17`

## Test summary

| Test file | Coverage |
|-----------|----------|
| `test_extraction_replay_idempotency_hardening.py` | Regression: completed extraction + different reason/rerun_allowed → no second run/text; force replay; DB constraint bypass |
| `test_extraction_replay_idempotency_alembic_migration.py` | Migration upgrade/downgrade + index presence |
| Updated persistence/worker/controlled tests | Hash + duplicate semantics |

## Remaining deferred

- OD-020: `trigger_status=completed` vs text-ready (dry-run semantics)
- Application-layer immutability only (no new scope)
- Optional `extraction_mode` in hash if multi-provider default triggers are introduced later

## Final principle

A `source_version` must not be reprocessed because request wording changed. Only explicit `force_reprocess=True` creates a governed replay.
