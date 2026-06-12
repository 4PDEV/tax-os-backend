# Answer Worker Contract

## Purpose

Define governed boundaries for the **answer worker** — a single-process orchestration envelope that invokes answer persistence without crossing layer boundaries.

This contract is **governance only** (TASK-009C-PREAUTH). It authorizes the answer worker **design envelope** for downstream bounded implementation. It does **not** authorize worker code, queues, migrations, APIs, response runtime, or narrative answer generation.

## Core principle

**The answer worker orchestrates answer persistence — it does not assemble, rank, retrieve, create citations, generate AI answers, or render public responses.**

```text
AnswerWorkerRequest (accepted envelope)
  → validate_request
  → running (in-worker lifecycle only — no queue broker)
  → persist_answer_for_ranking_request(...)
  → AnswerWorkerOutcome (terminal persistence status + counts)
```

Answer worker is **not**:

- answer assembly (009A) — delegated inside persistence orchestration
- answer persistence implementation (009B) — worker calls one entrypoint only
- ranking or retrieval execution
- citation creation or `CitationAssembler` invocation
- response runtime or HTTP delivery
- semantic / vector search or AI answer generation
- queue infrastructure or distributed job processing

## Mandatory doctrines

| Doctrine | Rule |
|----------|------|
| **Provenance lives once** (DEC-010) | Worker does not read/write provenance tables directly |
| **Replay semantics** (DEC-011) | Worker forwards `force_replay` + `replay_nonce` to persistence unchanged |
| **Answer boundary** (DEC-013) | Worker does not assemble or conclude legal force |
| **Assembly scope** (DEC-014) | Worker does not call `assemble_answer_package` directly |
| **Persistence doctrine** (DEC-015) | Worker does not bypass persistence APIs or duplicate orchestration |
| **Persistence envelope** (DEC-016) | Worker delegates only to `persist_answer_for_ranking_request` |
| **Single-worker** (OD-021) | Process-local mutex allowed; concurrent/distributed workers prohibited |

Upstream contracts (binding, closed):

- [`ANSWER_ASSEMBLY_CONTRACT.md`](ANSWER_ASSEMBLY_CONTRACT.md) (009A-v1)
- [`ANSWER_PERSISTENCE_CONTRACT.md`](ANSWER_PERSISTENCE_CONTRACT.md) (009B-v1)
- [`TASKS/ANSWER-LAYER-REVIEW.md`](TASKS/ANSWER-LAYER-REVIEW.md)
- [`TASKS/ANSWER-PERSISTENCE-REVIEW.md`](TASKS/ANSWER-PERSISTENCE-REVIEW.md)
- [`DECISION_LOG.md`](DECISION_LOG.md) — DEC-010 through DEC-017, OD-021

---

## 1. Worker boundary (governance decision)

### Allowed

| Capability | Mechanism |
|------------|-----------|
| Receive answer persistence request | `AnswerWorkerRequest` envelope |
| Validate request envelope | `AnswerWorker.validate_request()` |
| Invoke governed persistence | `persist_answer_for_ranking_request(session, ...)` **only** |
| Enrich outcome counts (read-only) | `list_evidence_entries_for_result`, `list_uncertainty_flags_for_result` on **accepted** `answer_result` — counts only |
| Return outcome DTO | `AnswerWorkerOutcome` |
| Single-worker mutex | Process-local `threading.Lock` (OD-021) |

### Prohibited

| Capability | Reason |
|------------|--------|
| Direct answer assembly | DEC-014 — inside persistence orchestration only |
| `resolve_ranking_assembly_inputs` | RL-O-01 resolution owned by 009A/009B |
| Direct `create_answer_*` persistence APIs | DEC-016 — orchestration entry only |
| Retrieval execution / persistence writes | Layer boundary |
| Ranking execution / persistence writes | Layer boundary |
| Citation creation / `CitationAssembler` | Citation layer closed |
| AI / semantic / vector reasoning | Not authorized |
| Public response formatting | Response runtime — not authorized |
| HTTP endpoints / FastAPI | API layer — not authorized |
| Queue brokers / consumers | OD-021 + no queue infrastructure |
| Narrative `answer_text`, legal conclusions, recommendations | Answer ≠ legal conclusion |

---

## 2. Worker entry point (frozen design)

### Package (locked for future implementation)

```text
backend/app/workers/answer_runtime/
```

| Module | Responsibility |
|--------|----------------|
| `models.py` | `AnswerWorkerRequest`, `AnswerWorkerOutcome`, documented lifecycle constants |
| `worker.py` | `AnswerWorker`, `run_answer_worker`, `build_answer_worker_request` |
| `__init__.py` | Public exports |

### Entry point (locked)

```python
def run_answer_worker(
    db: Session,
    request: AnswerWorkerRequest,
) -> AnswerWorkerOutcome:
    ...
```

**No implementation in TASK-009C-PREAUTH.**

---

## 3. Request / outcome DTOs (frozen)

### `AnswerWorkerRequest`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `ranking_request_id` | UUID | YES | Upstream identity — completed ranking lifecycle required |
| `contract_version` | str | YES | Default `009B-v1` |
| `assembly_contract_version` | str | YES | Default `009A-v1` |
| `include_rendered_citation_text` | bool | YES | Forwarded to persistence; affects hash |
| `force_replay` | bool | NO | Default `false` — DEC-011 |
| `replay_nonce` | str \| None | Conditional | Required when `force_replay=true` |

**Excluded from worker envelope (persistence-owned):** actor fields may default to `requested_by_actor_type="worker"` inside persistence call — not part of worker request in v1.

### `AnswerWorkerOutcome`

| Field | Type | Notes |
|-------|------|-------|
| `answer_request_id` | UUID | Persistence request row |
| `answer_result_id` | UUID | **Terminal** persistence result row ID |
| `answer_status` | str | Persistence terminal: `completed` \| `failed` \| `duplicate_rejected` |
| `evidence_entry_count` | int | Count on **accepted** `answer_result`; `0` on failed/duplicate |
| `uncertainty_flag_count` | int | Count on **accepted** `answer_result`; `0` on failed/duplicate |
| `error_category` | str \| None | Set when `failed` or `duplicate_rejected` |
| `worker_status` | str | Documented worker lifecycle terminal: `completed` \| `failed` |

**Ranking parity:** `worker_status` mirrors U-01 (`completed` \| `failed`); `answer_status` carries persistence terminal semantics for audit.

---

## 4. Documented worker lifecycle (no queue)

| State | Meaning |
|-------|---------|
| `accepted` | Valid `AnswerWorkerRequest` envelope |
| `running` | In-worker orchestration after mutex acquired (no broker) |
| `completed` | Persistence returned terminal `completed` |
| `failed` | Persistence returned `failed` or `duplicate_rejected`, or worker/persistence error |

```text
accepted → running → completed | failed
```

**No Celery, Redis, RabbitMQ, Kafka, or persistent queue storage.**

**No `skipped` dry-run path in 009C v1** — worker always invokes full persistence orchestration (recommendation; see OQ-C-02).

---

## 5. Delegation rule (locked)

### Single authorized downstream call

```text
persist_answer_for_ranking_request(
    session,
    ranking_request_id=request.ranking_request_id,
    contract_version=request.contract_version,
    assembly_contract_version=request.assembly_contract_version,
    include_rendered_citation_text=request.include_rendered_citation_text,
    force_replay=request.force_replay,
    replay_nonce=request.replay_nonce,
    requested_by_actor_type="worker",
)
```

### Prohibited direct calls

| API | Reason |
|-----|--------|
| `assemble_answer_package` | DEC-014 — persistence orchestration only |
| `resolve_ranking_assembly_inputs` | 009A validation — inside persistence/assembly |
| `create_answer_request` | DEC-016 append-only orchestration |
| `create_answer_result` | DEC-016 |
| `create_answer_evidence_entry` | DEC-016 |
| `create_answer_uncertainty_flag` | DEC-016 |

### Permitted read-only (outcome enrichment only)

| API | Usage |
|-----|-------|
| `list_results_for_request` | Locate accepted sibling of terminal result |
| `list_evidence_entries_for_result` | `evidence_entry_count` |
| `list_uncertainty_flags_for_result` | `uncertainty_flag_count` |

---

## 6. Single-worker doctrine (OD-021)

| Rule | Verdict |
|------|---------|
| Process-local mutex (`threading.Lock`) | **ALLOWED** |
| Non-blocking acquire; reject concurrent in-process invocation | **REQUIRED** |
| Distributed / multi-process workers | **PROHIBITED** |
| Celery / Redis / RabbitMQ / Kafka | **PROHIBITED** |
| Queue consumers | **PROHIBITED** |

**Error on concurrent worker:** `AnswerWorkerError("concurrent answer worker execution not authorized (OD-021)")`

**Persistence in-flight guard** remains authoritative inside `persist_answer_for_ranking_request` (`in_flight_accepted_answer_result`) — worker does not reimplement.

---

## 7. Failure mapping (locked)

### Persistence → worker outcome

| Persistence `answer_status` | `worker_status` | `answer_status` (outcome) | `error_category` | Counts |
|----------------------------|-----------------|---------------------------|------------------|--------|
| `completed` | `completed` | `completed` | `null` | From accepted result |
| `failed` | `failed` | `failed` | From persistence | `0` / `0` |
| `duplicate_rejected` | `failed` | `duplicate_rejected` | `duplicate_answer` | `0` / `0` |

### Pre-persistence failures

| Condition | Worker behavior |
|-----------|-----------------|
| Invalid request envelope | `AnswerWorkerError` — no persistence call |
| OD-021 mutex rejection | `AnswerWorkerError` — no persistence call |
| `AnswerPersistenceError` (in-flight, ranking missing, etc.) | `AnswerWorkerError` wrapping message; `worker_status=failed` |
| Unhandled exception | `AnswerWorkerError` or failed outcome with `unknown_failure` / `answer_pipeline_unavailable` |

### Error category policy

- **Reuse** existing 009A assembly + 009B persistence vocabulary — **no new categories** in 009C v1
- Worker may add **wrapper** `AnswerWorkerError` strings — must not invent new `error_category` values on `answer_results`
- Prohibited on worker mapping: ranking categories (`duplicate_ranking`, `permutation_mismatch`, etc.)

---

## 8. Import boundary guards (frozen for future implementation)

### Prohibited in `answer_runtime/`

| Prohibited | Reason |
|------------|--------|
| `app.services.retrieval_execution` | No retrieval |
| `app.services.ranking_execution` | No ranking |
| `app.workers.ranking_runtime` | No ranking worker coupling |
| `app.workers.retrieval_runtime` | No retrieval worker coupling |
| `app.services.answer_assembly` | No direct assembly (including `assemble_answer_package`, `validation`) |
| `app.services.answer_persistence` except `persist_answer_for_ranking_request` + read `list_*` | Delegation only |
| `app.services.response_runtime` | Not authorized |
| `app.services.ai` | No AI |
| `app.services.semantic` | No semantic |
| `app.services.vector` | No vector |
| `CitationAssembler` / `app.services.citation.assembler` | OQ-03 closed |
| `fastapi`, `APIRouter`, `app.api` | No HTTP |
| `celery`, `redis`, `rabbitmq`, `kafka` | No queue infrastructure |

### Permitted

| Permitted | Usage |
|-----------|--------|
| `app.services.answer_persistence.persist_answer_for_ranking_request` | Orchestration |
| `app.services.answer_persistence.list_*` | Outcome count enrichment only |
| `app.services.answer_persistence.CURRENT_CONTRACT_VERSION` | Defaults |
| `sqlalchemy.orm.Session` | Passed through |

---

## 9. Test plan (design only)

**Planned module:** `backend/tests/test_answer_worker_skeleton.py`

| Group | Tests |
|-------|-------|
| **Delegation** | `run_answer_worker` calls `persist_answer_for_ranking_request` exactly once |
| **No duplicate logic** | Worker source has no assembly, ranking, or retrieval algorithms |
| **No direct assembly** | Static scan — no `assemble_answer_package` import |
| **Request/outcome schemas** | Frozen dataclass fields; validation rejects bad envelope |
| **OD-021** | Concurrent `run_answer_worker` in same process rejected |
| **Import guards** | Prohibited prefixes absent from worker package |
| **Lifecycle constants** | Documented states only; no broker imports |
| **Failure propagation** | Persistence `failed` → `worker_status=failed`; `duplicate_rejected` mapped |
| **No queue infrastructure** | No Celery/Redis/RabbitMQ/Kafka imports or modules |
| **End-to-end** | Completed ranking → worker → terminal `completed` with counts > 0 when evidence exists |
| **Zero-evidence** | `rank_count=0` → `evidence_entry_count=0`; uncertainty may be > 0 |

**Integration tests require `TEST_DATABASE_URL`** (same discipline as 009B).

---

## 10. Boundaries with response runtime

| Concern | Answer worker | Response runtime (not authorized) |
|---------|---------------|-----------------------------------|
| Persistence orchestration | **YES** | NO |
| Public HTTP payloads | NO | Future scope |
| Citation display for end users | NO — optional flag forwarded to persistence only | Future scope |
| `answer_text` / narrative rendering | **PROHIBITED** | Future scope |
| Legal conclusions / recommendations | **PROHIBITED** | **PROHIBITED** |

**Answer worker returns `AnswerWorkerOutcome` only** — no response DTO, no API schema, no FastAPI models.

---

## 11. Readiness criteria

### TASK-009C-IMPL-AUTH (design package) must lock

- [ ] Package path and module list
- [ ] Frozen `AnswerWorkerRequest` / `AnswerWorkerOutcome` fields
- [ ] Delegation rule — `persist_answer_for_ranking_request` only
- [ ] Failure mapping table (§7)
- [ ] Import guard list (§8)
- [ ] OD-021 mutex specification
- [ ] Test matrix (§9)
- [ ] Explicit prohibitions (no queue, no APIs, no response runtime)

### TASK-009C implementation (when authorized) must deliver

- [ ] `backend/app/workers/answer_runtime/` skeleton only
- [ ] `run_answer_worker` + `build_answer_worker_request`
- [ ] `test_answer_worker_skeleton.py` per §9
- [ ] No migrations, ORM tables, queue storage, APIs
- [ ] No changes to `answer_persistence` orchestration semantics without new governance gate

---

## End-to-end chain (with worker)

```text
retrieval → ranking (008C–008D, U-01) → answer persistence (009B)
  → [009C] run_answer_worker() → persist_answer_for_ranking_request()
      → assemble_answer_package() [inside 009B only]
```

---

## Open questions

| ID | Question | Recommendation |
|----|----------|----------------|
| OQ-C-01 | Include `answer_request_id` on `AnswerWorkerOutcome`? | **YES** — audit parity with `AnswerPersistenceOutcome` |
| OQ-C-02 | Dry-run / `skipped` worker path like 007D? | **NO in v1** — full persist only; defer dry-run to future gate |
| OQ-C-03 | Combined ranking-then-answer worker chain? | **OUT OF SCOPE** — document separate invocations; no multi-layer worker |
| OQ-C-04 | `session.commit()` inside persistence vs worker transaction? | **Accept 009B behavior** — worker passes session; persistence commits per DEC-016 |

---

## Explicit prohibitions (this contract)

- No worker implementation in TASK-009C-PREAUTH
- No migrations, queue tables, APIs, response runtime
- No concurrent / distributed workers
- No new `error_category` vocabulary
- No `answer_text`, legal conclusions, recommendations, AI

---

END OF ANSWER WORKER CONTRACT (implementation NOT AUTHORIZED)
