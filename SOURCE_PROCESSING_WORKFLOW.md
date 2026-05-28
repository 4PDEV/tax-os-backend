# Source Processing Workflow

Internal queue and job lifecycle for `source_processing_jobs` (TASK-001M, TASK-001N, TASK-001O).

## Job statuses

| `job_status` | Meaning |
|--------------|---------|
| `queued` | Waiting for worker claim |
| `processing` | Claimed and locked |
| `completed` | Finalized successfully |
| `failed` | Finalized with error |
| `cancelled` | Cancelled before completion |

## Ingestion status integration

| Event | `source_versions.ingestion_status` |
|-------|-----------------------------------|
| File uploaded | `queued` |
| Job claimed | `processing` |
| Job completed | `parsed` |
| Job failed | `failed` |

## API flow

1. `POST /source-processing-jobs` — enqueue (version must be `ingestion_status=queued`)
2. `POST /source-processing-jobs/claim-next` — claim next job (`locked_by` required)
3. `POST /source-processing-jobs/{id}/complete` — finalize success
4. `POST /source-processing-jobs/{id}/fail` — finalize failure

Generic `POST /source-processing-jobs/{id}/status` remains for governed transitions (e.g. retry).

## Complete request

```json
{
  "completed_by": "worker-alpha",
  "result_json": { "pages": 10, "language": "en" }
}
```

Persists: `result_json`, `completed_by`, `job_status=completed`.

## Fail request

```json
{
  "failed_by": "worker-alpha",
  "last_error": "parser unavailable",
  "result_json": { "stage": "ocr" }
}
```

Persists: `result_json`, `failed_by`, `last_error`, `job_status=failed`.

## Governance

- Only `processing` jobs may be completed or failed.
- `completed_by` / `failed_by` are required on finalization endpoints.
- `last_error` is required on fail.
- Repeat finalization returns **422**.

## Worker contract (TASK-001P)

Bounded one-shot execution via `app.workers.runner.run_next_job_once`:

1. Claim next `queued` job (`locked_by` = worker id)
2. Invoke a `SourceJobProcessor` implementation
3. Finalize as `completed` or `failed` with structured `result_json`

`NoopProcessor` is the reference harness — no parsing, OCR, or background loops.

```python
from app.workers import NoopProcessor, run_next_job_once

result = run_next_job_once(db, worker_id="worker-alpha", processor=NoopProcessor())
# result.outcome: "no_job" | "completed" | "failed"
```

See [WORKER_CONTRACT.md](WORKER_CONTRACT.md).
