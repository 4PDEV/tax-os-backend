# TASK-009C — Implementation Authorization Package

## Status

**COMPLETE** / **ACCEPTED WITH REMEDIATION** — Claude review accepted; **AUTHORIZED FOR LIMITED IMPLEMENTATION**.

| Phase | Status |
|-------|--------|
| TASK-009C-PREAUTH | **ACCEPTED** — DEC-017 |
| TASK-009C-IMPLEMENTATION-AUTHORIZATION (this document) | **ACCEPTED** — DEC-018 |
| TASK-009C answer worker code | **AUTHORIZED FOR LIMITED IMPLEMENTATION** |

## Accepted baseline

| Item | Value |
|------|--------|
| HEAD | `f2a19d1` (or newer accepted HEAD) |
| Tag | `v0.2.1-answer-worker-preauth` |
| TASK-009A | **COMPLETE** — `v0.1.8-answer-assembly` |
| TASK-009B | **COMPLETE** — `v0.1.9-answer-persistence` |
| Answer persistence review (009B+) | **ACCEPTED WITH REMEDIATION** |
| TASK-009C-PREAUTH | **ACCEPTED** |
| DEC-010 through DEC-017 | **LOCKED** |
| OD-021 | **LOCKED** — single-worker carry-forward |

## Binding upstream artifacts

- [`ANSWER_WORKER_CONTRACT.md`](../ANSWER_WORKER_CONTRACT.md) (009C-v1)
- [`TASKS/TASK-009C-ANSWER-WORKER.md`](TASK-009C-ANSWER-WORKER.md)
- [`ANSWER_PERSISTENCE_CONTRACT.md`](../ANSWER_PERSISTENCE_CONTRACT.md) (009B-v1)
- [`TASKS/ANSWER-PERSISTENCE-REVIEW.md`](ANSWER-PERSISTENCE-REVIEW.md)
- [`TASKS/TASK-009B-IMPLEMENTATION-AUTHORIZATION.md`](TASK-009B-IMPLEMENTATION-AUTHORIZATION.md)
- [`TASKS/U-01-RANKING-WORKER-SKELETON.md`](U-01-RANKING-WORKER-SKELETON.md) (pattern reference)
- [`DECISION_LOG.md`](../DECISION_LOG.md)

## Important

This package **does NOT implement** worker code, queues, migrations, ORM models, persistence services, APIs, response runtime, or tests.

---

## D-C-01 — Final module boundary (frozen)

### Package (locked)

```text
backend/app/workers/answer_runtime/
```

| Module | Responsibility |
|--------|----------------|
| `models.py` | `AnswerWorkerRequest`, `AnswerWorkerOutcome`, `AnswerWorkerError`, documented lifecycle constants |
| `worker.py` | `AnswerWorker`, `run_answer_worker`, `build_answer_worker_request`, OD-021 mutex |
| `__init__.py` | Public exports |

**No other modules** in `answer_runtime/`. No `queue.py`, `broker.py`, `tasks.py`, or subpackages.

**Parity:** U-01 `ranking_runtime/` — three modules only.

---

## D-C-02 — Entry point (frozen)

```python
def run_answer_worker(
    db: Session,
    request: AnswerWorkerRequest,
) -> AnswerWorkerOutcome:
    """Single execution entrypoint for answer worker orchestration."""
```

Optional helper (in `worker.py` only):

```python
def build_answer_worker_request(
    *,
    ranking_request_id: UUID,
    contract_version: str = CURRENT_CONTRACT_VERSION,
    assembly_contract_version: str = DEFAULT_ASSEMBLY_CONTRACT_VERSION,
    include_rendered_citation_text: bool = False,
    force_replay: bool = False,
    replay_nonce: str | None = None,
) -> AnswerWorkerRequest:
    ...
```

---

## D-C-03 — DTO fields (frozen)

### `AnswerWorkerRequest`

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `ranking_request_id` | UUID | required | Must be `UUID` instance |
| `contract_version` | str | `009B-v1` | Non-empty |
| `assembly_contract_version` | str | `009A-v1` | Non-empty |
| `include_rendered_citation_text` | bool | `false` | |
| `force_replay` | bool | `false` | |
| `replay_nonce` | str \| None | `None` | Required when `force_replay=true` |

### `AnswerWorkerOutcome`

| Field | Type | Notes |
|-------|------|-------|
| `answer_request_id` | UUID | Persistence request row — **existing row on duplicate_rejected (F-3)** |
| `answer_result_id` | UUID | Terminal `answer_results.id` |
| `worker_status` | str | `completed` \| `failed` only |
| `answer_status` | str | Persistence terminal: `completed` \| `failed` \| `duplicate_rejected` |
| `evidence_entry_count` | int | From **accepted** result; `0` on failed/duplicate |
| `uncertainty_flag_count` | int | From **accepted** result; `0` on failed/duplicate |
| `error_category` | str \| None | From persistence when terminal is `failed` or `duplicate_rejected` |

**F-4 requirement:** Tests must assert **both** `worker_status` and `answer_status` on every outcome path.

### Documented lifecycle constants (`models.py`)

```python
QUEUE_LIFECYCLE_ACCEPTED = "accepted"
QUEUE_LIFECYCLE_RUNNING = "running"
QUEUE_LIFECYCLE_COMPLETED = "completed"
QUEUE_LIFECYCLE_FAILED = "failed"

DOCUMENTED_QUEUE_LIFECYCLE = frozenset({...})
```

**Not persisted.** Documented in-worker only (mirror U-01).

---

## D-C-04 — Delegation rule (frozen)

### Single authorized write path

```text
persist_answer_for_ranking_request(
    db,
    ranking_request_id=request.ranking_request_id,
    contract_version=request.contract_version,
    assembly_contract_version=request.assembly_contract_version,
    include_rendered_citation_text=request.include_rendered_citation_text,
    force_replay=request.force_replay,
    replay_nonce=request.replay_nonce,
    requested_by_actor_type="worker",
)
```

### Prohibited calls (worker must never invoke)

| API | Layer |
|-----|-------|
| `assemble_answer_package` | 009A assembly |
| `resolve_ranking_assembly_inputs` | 009A validation |
| `create_answer_request` | 009B persistence |
| `create_answer_result` | 009B persistence |
| `create_answer_evidence_entry` | 009B persistence |
| `create_answer_uncertainty_flag` | 009B persistence |

### Permitted read-only (outcome count enrichment only)

| API | Usage |
|-----|-------|
| `list_results_for_request(session, answer_request_id=...)` | Locate `accepted` sibling |
| `list_evidence_entries_for_result(session, answer_result_id=accepted.id)` | `evidence_entry_count` |
| `list_uncertainty_flags_for_result(session, answer_result_id=accepted.id)` | `uncertainty_flag_count` |

**Count enrichment algorithm (locked):**

```text
results = list_results_for_request(answer_request_id)
accepted = sole row where answer_status == "accepted"
if accepted and persistence_outcome.answer_status == "completed":
    evidence_entry_count = len(list_evidence_entries_for_result(accepted.id))
    uncertainty_flag_count = len(list_uncertainty_flags_for_result(accepted.id))
else:
    evidence_entry_count = 0
    uncertainty_flag_count = 0
```

Worker **must not** import or call `get_answer_request` / `get_answer_result` unless added explicitly in a future amendment — v1 uses `list_*` only.

---

## D-C-05 — Failure mapping (frozen)

### Persistence outcome → `AnswerWorkerOutcome`

| Persistence `answer_status` | `worker_status` | `answer_status` | `error_category` | Counts |
|----------------------------|-----------------|-----------------|------------------|--------|
| `completed` | `completed` | `completed` | `None` | Enriched from accepted |
| `failed` | `failed` | `failed` | From `AnswerPersistenceOutcome` | `0` / `0` |
| `duplicate_rejected` | `failed` | `duplicate_rejected` | `duplicate_answer` | `0` / `0` |

### Claude F-3 — `duplicate_rejected` idempotency

When persistence returns `duplicate_rejected`:

- `outcome.answer_request_id` **must** be the **existing** default `answer_requests` row ID
- **No new** `answer_request` row is created for the duplicate default request
- Worker passes through `AnswerPersistenceOutcome.answer_request_id` unchanged
- Tests must verify: second default worker invocation → same `answer_request_id` as first successful run; only new `answer_results` row is `duplicate_rejected`

**Authority:** 009B orchestration already implements this path — worker must not alter or re-wrap IDs.

### Claude F-4 — dual status assertions

Every integration test asserting terminal behavior **must** check:

```python
assert outcome.worker_status == "<expected>"
assert outcome.answer_status == "<expected>"
```

Especially for `duplicate_rejected`: `worker_status=failed`, `answer_status=duplicate_rejected`.

### Pre-persistence failures (no new answer rows)

| Condition | Behavior |
|-----------|----------|
| `AnswerWorker.validate_request` failure | Raise `AnswerWorkerError` — **no** `persist_answer_for_ranking_request` call |
| OD-021 mutex rejection | Raise `AnswerWorkerError("concurrent answer worker execution not authorized (OD-021)")` — **no** persistence call |
| `AnswerPersistenceError` before/outside successful persist | Raise `AnswerWorkerError` wrapping message — **no** worker-created rows |

### Error category policy

- **Reuse** 009A/009B vocabulary only — **no new** `error_category` values in 009C v1
- Worker `AnswerWorkerError` is a wrapper exception — not persisted
- Prohibited worker-emitted categories: ranking (`duplicate_ranking`, `permutation_mismatch`, etc.)

---

## D-C-06 — OD-021 enforcement (frozen)

Mirror U-01 `ranking_runtime/worker.py`:

```python
_execution_lock = threading.Lock()

def _acquire_single_worker_slot() -> bool:
    return _execution_lock.acquire(blocking=False)

def _release_single_worker_slot() -> None:
    _execution_lock.release()
```

| Rule | Verdict |
|------|---------|
| Process-local `threading.Lock` | **REQUIRED** |
| Non-blocking `acquire(blocking=False)` | **REQUIRED** |
| Reject immediately if slot occupied | **REQUIRED** |
| `release()` in `finally` block | **REQUIRED** |
| Distributed locks | **PROHIBITED** |
| Multi-process / concurrent workers | **PROHIBITED** |

**Persistence in-flight guard** (`in_flight_accepted_answer_result`) remains inside 009B — worker does not duplicate.

---

## D-C-07 — Queue boundary (frozen)

### Documented lifecycle only

```text
accepted → running → completed | failed
```

| Prohibited | |
|------------|--|
| Celery | |
| Redis | |
| RabbitMQ | |
| Kafka | |
| Queue tables / persistent queue state | |
| Background task runners | |

**No `skipped` dry-run path in 009C v1** — worker always invokes full persistence (DEC-017).

---

## D-C-08 — Import boundary guards (frozen)

### Prohibited imports in `answer_runtime/`

| Prohibited prefix / symbol |
|----------------------------|
| `app.services.retrieval_execution` |
| `app.services.ranking_execution` |
| `app.workers.ranking_runtime` |
| `app.workers.retrieval_runtime` |
| `app.services.answer_assembly` |
| `app.services.answer_assembly.validation` |
| `app.services.answer_assembly.assembly` |
| `app.services.response_runtime` |
| `app.services.ai` |
| `app.services.semantic` |
| `app.services.vector` |
| `CitationAssembler` / `app.services.citation.assembler` |
| `fastapi`, `APIRouter` |
| `app.api` |
| `celery`, `redis`, `rabbitmq`, `kafka` |
| `create_answer_request`, `create_answer_result`, `create_answer_evidence_entry`, `create_answer_uncertainty_flag` |
| `assemble_answer_package`, `resolve_ranking_assembly_inputs` |

### Allowed imports

| Permitted | Usage |
|-----------|--------|
| `app.services.answer_persistence.persist_answer_for_ranking_request` | Sole write orchestration |
| `app.services.answer_persistence.list_results_for_request` | Count enrichment |
| `app.services.answer_persistence.list_evidence_entries_for_result` | Count enrichment |
| `app.services.answer_persistence.list_uncertainty_flags_for_result` | Count enrichment |
| `app.services.answer_persistence.CURRENT_CONTRACT_VERSION` | Defaults |
| `app.services.answer_persistence.DEFAULT_ASSEMBLY_CONTRACT_VERSION` | Defaults |
| `app.services.answer_persistence.AnswerPersistenceError` | Error wrapping |
| `app.services.answer_persistence.AnswerPersistenceOutcome` | Outcome mapping |
| `sqlalchemy.orm.Session` | DB session |
| `threading` | OD-021 mutex |
| `uuid` | Type hints / validation |
| `dataclasses` | DTOs |

### Test guard

`test_answer_worker_import_guards` — static scan of `models.py`, `worker.py`, `__init__.py` (mirror U-01 / 009B).

---

## D-C-09 — Implementation test plan (design only)

**Planned module:** `backend/tests/test_answer_worker_skeleton.py`

| Group | Tests |
|-------|-------|
| **Delegation** | `run_answer_worker` calls `persist_answer_for_ranking_request` exactly once |
| **No assembly** | Mock/patch — `assemble_answer_package` never called from worker package |
| **No create_*** | `create_answer_*` never called from worker package |
| **DTO schemas** | Frozen field sets on request/outcome dataclasses |
| **Lifecycle constants** | `DOCUMENTED_QUEUE_LIFECYCLE` contains four states only |
| **OD-021 mutex release (R-1)** | Two sequential non-concurrent `run_answer_worker` invocations both succeed after first completes |
| **duplicate_rejected (F-3, F-4)** | Second default invocation: `worker_status=failed`, `answer_status=duplicate_rejected`, **same** `answer_request_id`, no new request row |
| **completed** | `worker_status=completed`, `answer_status=completed`, counts > 0 when evidence exists |
| **failed** | Assembly/persistence failure: both statuses `failed`, counts `0` |
| **Count enrichment** | `evidence_entry_count` / `uncertainty_flag_count` match accepted result lists |
| **Import guards** | Prohibited prefixes absent |
| **No queue infra** | No broker imports; no queue modules under `answer_runtime/` |
| **No API/response runtime** | No FastAPI / `response_runtime` imports |
| **AP-R-03 fixture note** | Document that `persist_answer_for_ranking_request` calls `session.commit()` — integration tests may need isolated DB or ordering discipline per [`TASKS/ANSWER-PERSISTENCE-REVIEW.md`](ANSWER-PERSISTENCE-REVIEW.md) AP-R-03 |
| **End-to-end** | Completed ranking → worker → terminal `completed` |
| **Zero-evidence** | `rank_count=0` → `evidence_entry_count=0`; uncertainty may be > 0 |
| **Validation** | Invalid envelope / missing `replay_nonce` when `force_replay=true` rejected before persist |
| **Worker has no persistence logic** | Source scan — no ranking/assembly algorithms in worker |

**Integration tests require `TEST_DATABASE_URL`.**

---

## D-C-10 — Implementation scope

### TASK-009C may build (when explicitly authorized)

| Artifact | Scope |
|----------|--------|
| `backend/app/workers/answer_runtime/models.py` | §D-C-03 DTOs + lifecycle constants |
| `backend/app/workers/answer_runtime/worker.py` | §D-C-02 entry + §D-C-06 mutex + mapping |
| `backend/app/workers/answer_runtime/__init__.py` | Public exports |
| `backend/tests/test_answer_worker_skeleton.py` | §D-C-09 |

### TASK-009C must NOT build

| Prohibited | |
|------------|--|
| Migrations / ORM models | |
| Changes to `answer_persistence` or `answer_assembly` | |
| Queue infrastructure | |
| Public HTTP APIs / FastAPI routes | |
| Response runtime | |
| AI / semantic / vector | |
| `CitationAssembler` | |
| `answer_text`, legal conclusions, recommendations | |
| Concurrent / distributed workers | |
| Dry-run `skipped` worker path | |

### Upstream preservation

- `persist_answer_for_ranking_request` semantics unchanged (DEC-016)
- `assemble_answer_package` remains callable without worker (DEC-014)
- Ranking worker (U-01) unchanged

---

## Authorization checklist (for future acceptance prompt)

- [ ] Architect accepts §D-C-01–§D-C-10
- [ ] Claude review of this package (recommended)
- [ ] Explicit prompt: **AUTHORIZED FOR LIMITED IMPLEMENTATION**
- [ ] Scope: `answer_runtime/` + `test_answer_worker_skeleton.py` only

---

## Unresolved questions

| ID | Question | Disposition |
|----|----------|-------------|
| U-C-01 | `AnswerWorkerError` vs failed `AnswerWorkerOutcome` on OD-021? | **Recommend raise** `AnswerWorkerError` — mirror U-01; no outcome row |
| U-C-02 | Include `error_message` on `AnswerWorkerOutcome`? | **Defer** — not in frozen field list; use `error_category` only |
| U-C-03 | `get_answer_result` for enrichment vs `list_*` only? | **Locked `list_*` only** per §D-C-04 |
| U-C-04 | Unit tests without DB for validation/OD-021? | **Recommend yes** — mirror `test_ranking_worker_skeleton.py` |

---

## Explicit prohibitions (this task)

- No worker code, queue infrastructure, migrations, ORM, services, APIs, or tests in this task

---

END OF TASK-009C IMPLEMENTATION AUTHORIZATION PACKAGE (implementation NOT AUTHORIZED)
