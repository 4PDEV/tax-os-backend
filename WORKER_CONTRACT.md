# Worker Contract

Deterministic worker execution contract for `source_processing_jobs` (TASK-001P).

## Purpose

Prove the processing lifecycle without autonomous background workers or real parsers:

```text
queued → processing (claimed) → completed | failed
```

## Modules

| Module | Role |
|--------|------|
| `app.workers.contract` | `SourceJobProcessor` protocol, `ProcessingResult` |
| `app.workers.noop_processor` | No-op harness for tests and manual verification |
| `app.workers.runner` | `run_next_job_once` one-shot orchestration |

## Processor contract

```python
class SourceJobProcessor(Protocol):
    def process(self, job: SourceProcessingJob, version: SourceVersion) -> ProcessingResult:
        ...
```

`ProcessingResult`:

- `success: bool`
- `result_json: dict | None` — persisted on finalize
- `error_message: str | None` — required semantics when `success` is false

## One-shot runner

```python
result = run_next_job_once(
    db,
    worker_id="worker-alpha",
    processor=NoopProcessor(),
    job_type="source_ingestion",  # optional filter
    commit=True,  # default; set False when the caller owns the transaction
)
```

| `result.outcome` | Meaning |
|------------------|---------|
| `no_job` | Queue had no claimable jobs |
| `completed` | Job finalized successfully |
| `failed` | Job finalized with error |

## No-op processor

`NoopProcessor(should_fail=False)` returns deterministic JSON metadata only.

Use `should_fail=True` to exercise the failure path in tests.

## Explicit non-goals

- No background daemon or infinite poll loop
- No OCR, parsing, extraction, or AI agents
- No automatic enqueue — jobs must exist via API first

## Preconditions

A job is claimable when:

- `job_status == queued`
- Linked `source_versions.ingestion_status == queued` (file attached)

The runner delegates claim, finalize, and ingestion sync to `app.services.processing_queue`.
