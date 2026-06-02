# TASK-006S — Parsing Worker Skeleton

## Status

**Complete** — accepted at `checkpoint-task-006s-parsing-worker-skeleton`

## Objective

Dry-run-only orchestration from `parsing_trigger_request` to `parser_run` lifecycle records.

## Delivered

| Area | Location |
|------|----------|
| Worker package | `backend/app/workers/parsing/` |
| Runner | `run_parsing_dry_run()` — requires `dry_run=True` |
| Provider | `DryRunParsingProvider` / `ParsingProvider` protocol |
| Idempotency | `extracted_text_has_completed_parsing()` skip unless `force_reparse=True` |

## Boundaries

- No real parsing, `parsed_structure`, legal object, citation, or answer side effects
- OD-021 execution-time concurrency deferred to future tasks

## Final principle

The parsing worker skeleton proves orchestration. It does not yet parse legal content.
