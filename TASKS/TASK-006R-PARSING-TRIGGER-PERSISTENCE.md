# TASK-006R — Parsing Trigger Persistence

## Status

**Complete**

## Objective

Append-only persistence for parsing trigger requests and results per [`PARSING_TRIGGER_CONTRACT.md`](../PARSING_TRIGGER_CONTRACT.md).

## Delivered

| Area | Location |
|------|----------|
| Models | `backend/app/models/parsing_trigger_request.py`, `parsing_trigger_result.py` |
| Migration | `f3b9c2e81a25` — partial unique index on `extracted_text_id` WHERE `force_reparse = false` |
| Services | `backend/app/services/parsing_trigger/` |
| Tests | `test_parsing_trigger_persistence.py`, `test_parsing_trigger_alembic_migration.py` |

## Idempotency

- Default `trigger_hash` = SHA-256(`extracted_text_id`) only
- `force_reparse=True` uses replay nonce (006P1 pattern)
- `rerun_allowed` does not bypass duplicates

## Deferred

- Worker execution-time concurrency (OD-021)
- Complex quarantine/review eligibility when fields exist
- `parsing_already_completed` enforcement at worker layer (future)

## Final principle

Persistence records: **“Parsing may be requested for this extracted_text.”** It does not perform parsing or determine legal meaning.
