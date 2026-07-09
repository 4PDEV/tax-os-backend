# DECISION LOG

---

## DEC-001
LLMs must never answer tax or legal questions directly from model memory.

Status:
LOCKED

---

## DEC-002
All production answers must be source-referenced.

Status:
LOCKED

---

## DEC-003
Legal objects and source versions must never be silently overwritten.

Status:
LOCKED

---

## DEC-004
The platform must be effective-date-aware and version-aware.

Status:
LOCKED

---

## DEC-005
The system must surface ambiguity, conflicts, uncertainty, and risk rather than pretending certainty.

Status:
LOCKED

---

## DEC-006
Architecture authority remains centralized and governed.

Status:
LOCKED

---

## DEC-007
Development must occur through bounded tasks only.

Status:
LOCKED

---

## DEC-008
Agents may retrieve and structure information but may not autonomously publish production truth.

Status:
LOCKED

---

## DEC-009
The platform shall evolve progressively:
- country by country
- tax regime by tax regime
- module by module

Status:
LOCKED

---

## DEC-010
Ranking stores order only. Provenance lives once in `retrieval_evidence_references`. `ranked_evidence_references` are pure pointers (`retrieval_result_id`, `retrieval_evidence_reference_id`, `presentation_order_index`) — no copied provenance fields.

Authority: TASK-008C-REMEDIATION — [`RANKING_PERSISTENCE_REMEDIATION_008C-REMEDIATION.md`](RANKING_PERSISTENCE_REMEDIATION_008C-REMEDIATION.md); verified TASK-008C-PREAUTH-RECONCILIATION — [`TASKS/TASK-008C-PREAUTH-RECONCILIATION.md`](TASKS/TASK-008C-PREAUTH-RECONCILIATION.md)

Status:
LOCKED

---

## DEC-011 — Force Replay Hash Interpretation

For normal ranking requests (`force_replay = false`), `ranking_request_hash` remains:

```text
SHA-256(canonical_json({
  retrieval_result_id,
  ranking_profile,
  contract_version
}))
```

When `force_replay = true`, the persisted request-hash payload may include replay-specific entropy (e.g. `replay_nonce`) so an additional append-only lifecycle request can be recorded without colliding with the default de-duplication rule.

This interpretation:

- Exists only to allow an additional append-only lifecycle request row
- Does **not** change ranking determinism, ranking output, permutation validation, prerequisite validation, pure-pointer persistence, or provenance-once doctrine (DEC-010)
- Leaves the default non-replay de-duplication rule enforced by partial unique index `UNIQUE (ranking_request_hash) WHERE force_replay = false`

Authority: TASK-008C ranking persistence — Claude review finding F-10 (documentation closure); implementation in [`backend/app/services/ranking_persistence/hashing.py`](backend/app/services/ranking_persistence/hashing.py)

**TASK-008D and TASK-009A remain NOT AUTHORIZED.**

Status:
LOCKED

---

## DEC-012 — Ranking Execution Determinism and Boundary

Ranking execution applies **mechanical permutation over completed retrieval only**.

**Required:**

- Same `retrieval_result` + `ranking_profile` + `contract_version` ⇒ identical ordering (`presentation_order_index` assignment)
- Permutation integrity required — identical multiset of `retrieval_evidence_reference_id` values in and out
- `rank_count` equals retrieval evidence count (and persisted ranked row count)
- Zero-evidence completed retrieval ⇒ `ranking_status=completed`, `rank_count=0`, no error (`evidence_set_empty` prohibited)
- Pure-pointer persistence remains mandatory (DEC-010)
- Force replay behaviour governed by DEC-011
- Single-worker only (OD-021)

**Prohibited:**

- Retrieval re-selection
- AI ranking
- Semantic / vector ranking
- Answer generation
- Legal conclusions
- Citation synthesis

Authority: TASK-008D-PREAUTH — [`RANKING_EXECUTION_CONTRACT.md`](RANKING_EXECUTION_CONTRACT.md); [`TASKS/TASK-008D-RANKING-EXECUTION.md`](TASKS/TASK-008D-RANKING-EXECUTION.md)

**TASK-008D implementation and TASK-009A remain NOT AUTHORIZED.**

Status:
LOCKED

---

## DEC-013 — Answer Assembly Boundary and Provenance Read Model

Answer assembly constructs a **source-referenced answer package** from **completed ranking output only**.

**Required:**

- Consume terminal `ranking_status=completed` lifecycle and ranked evidence from the **accepted** `ranking_result` for the same `ranking_request_id` (RL-O-01)
- Load retrieval provenance **read-only** via `ranked_evidence_reference` → `retrieval_evidence_reference` joins (DEC-010)
- Preserve ranked evidence multiset and `presentation_order_index` order (E-01–E-07)
- Surface ambiguity and uncertainty explicitly (DEC-005) — no silent certainty
- Use answer-layer canonical error vocabulary — distinct from ranking errors
- Single-worker carry-forward (OD-021) until explicit concurrency governance

**Prohibited:**

- Retrieval execution or evidence re-selection
- Ranking execution or reordering
- Evidence invention, silent omission, or retrieval bypass
- Provenance duplication on answer-owned persistence
- Citation creation or canonical citation mutation
- Legal conclusions, applicability determination, or tax advice fields
- AI / semantic / vector ranking or unconstrained LLM answer generation (DEC-001)
- Answer runtime implementation without explicit authorization following 009A-PREAUTH acceptance

Authority: TASK-009A-PREAUTH — [`ANSWER_ASSEMBLY_CONTRACT.md`](ANSWER_ASSEMBLY_CONTRACT.md); [`TASKS/TASK-009A-ANSWER-ASSEMBLY.md`](TASKS/TASK-009A-ANSWER-ASSEMBLY.md)

**TASK-009A implementation remains NOT AUTHORIZED.**

Status:
LOCKED

---

## DEC-014 — Answer Assembly Implementation Scope (009A-v1)

First bounded answer assembly implementation (**TASK-009A**, when authorized) is **ephemeral only**:

- Returns in-memory `AnswerPackage` — **no** `answer_requests` / `answer_results` persistence (Option A)
- Provenance read-only via joins — DEC-010 preserved; no authoritative provenance duplication
- Append-only persisted lifecycle for answers deferred to **TASK-009B** (Option B — not authorized)
- **CitationFormatter** permitted read-only when `include_rendered_citation_text=true` and `citation_id` resolves
- **CitationAssembler** prohibited in 009A-v1 answer path
- No narrative `answer_text`, legal conclusions, recommendations, or AI generation
- Direct service entry only — answer worker deferred; OD-021 carry-forward for future worker task

Authority: TASK-009A-IMPLEMENTATION-AUTHORIZATION — [`TASKS/TASK-009A-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-009A-IMPLEMENTATION-AUTHORIZATION.md)

**TASK-009A implementation remains NOT AUTHORIZED** until explicit acceptance of the implementation authorization package.

Status:
LOCKED

---

## DEC-015 — Answer Persistence Pure-Pointer Doctrine

Answer persistence (**TASK-009B**, when authorized) records **append-only lifecycle and pure-pointer evidence membership only**.

**Required:**

- Tables: `answer_requests`, `answer_results`, `answer_evidence_entries`, `answer_uncertainty_flags` (append-only)
- `answer_request_hash` idempotency with DEC-011 replay pattern (`force_replay` + `replay_nonce`)
- RL-O-01 preserved: `ranking_request_id` on request; `accepted_ranking_result_id` + `terminal_ranking_result_id` on results; evidence rows on **accepted** `answer_result`
- `answer_evidence_entries` store pointers only (`ranked_evidence_reference_id`, `retrieval_evidence_reference_id`, `presentation_order_index`) — **no** provenance field copies (DEC-010)
- Uncertainty flags persisted as child rows; `zero_evidence` required when `rank_count=0`
- Assembly authority remains `assemble_answer_package` (009A) — persistence does not embed assembly logic
- Citation display via read-only `CitationFormatter` at read time only — **no** persisted `rendered_citation_text`
- Ephemeral 009A path preserved (DEC-014)

**Prohibited:**

- Provenance duplication (`legal_object_id`, `citation_id`, `citation_hash`, `source_version_id`, etc. on answer evidence rows)
- Persisted citation text cache as authoritative store
- `CitationAssembler`, citation creation/mutation
- Narrative `answer_text`, legal conclusions, recommendations
- Ranking/retrieval execution from persistence layer
- Answer worker, APIs, response runtime in 009B scope

Authority: TASK-009B-PREAUTH — [`ANSWER_PERSISTENCE_CONTRACT.md`](ANSWER_PERSISTENCE_CONTRACT.md); [`TASKS/TASK-009B-ANSWER-PERSISTENCE.md`](TASKS/TASK-009B-ANSWER-PERSISTENCE.md)

**TASK-009B implementation remains NOT AUTHORIZED.**

Status:
LOCKED

---

## DEC-016 — Answer Persistence Implementation Envelope (009B-v1)

TASK-009B implementation (when authorized) is bounded to **append-only persistence + orchestration hook only**.

**Frozen schema:**

- `answer_requests`, `answer_results`, `answer_evidence_entries`, `answer_uncertainty_flags`
- Contract generation `009B-v1`; assembly remains `009A-v1`

**Frozen lifecycle (Option A):**

```text
answer_request → answer_result(accepted) → assemble_answer_package → children → answer_result(completed|failed)
```

**Frozen integrity:**

- Retrieval composite FK on `answer_evidence_entries` (DEC-010)
- Ranked membership via FK + service validation V-B-02 (RL-O-01)
- Single transaction per orchestration invocation
- `answer_request_hash` + DEC-011 replay pattern
- Pure-pointer evidence rows — prohibited-column matrix §D-09
- No persisted citation text or provenance copies

**Frozen service:** `backend/app/services/answer_persistence/` — `create_*` + read APIs + `persist_answer_for_ranking_request` only

**Prohibited in 009B:** worker, APIs, response runtime, AI, `CitationAssembler`, `answer_text`, legal conclusions, concurrent workers

Authority: TASK-009B-IMPL-AUTH — [`TASKS/TASK-009B-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-009B-IMPLEMENTATION-AUTHORIZATION.md)

**TASK-009B implementation:** **COMPLETE** — tag `v0.1.9-answer-persistence`.

Status:
LOCKED

---

## DEC-017 — Answer Worker Orchestration Boundary (009C-v1)

The answer worker (**TASK-009C**, when authorized) is a **single-process orchestration envelope only**.

**Required:**

- Package: `backend/app/workers/answer_runtime/`
- Entry: `run_answer_worker(db, request)` → `persist_answer_for_ranking_request(...)` **only**
- DTOs: `AnswerWorkerRequest`, `AnswerWorkerOutcome` (contract §3)
- Documented lifecycle: `accepted` → `running` → `completed` | `failed` — **no queue infrastructure**
- OD-021: process-local mutex; concurrent/distributed workers prohibited
- Failure mapping: reuse 009A/009B `error_category` vocabulary — no new categories
- Read-only `list_*` permitted for outcome count enrichment on accepted result only

**Prohibited:**

- Direct `assemble_answer_package`, `resolve_ranking_assembly_inputs`, or `create_answer_*` calls
- Retrieval/ranking execution, citation creation, `CitationAssembler`
- Response runtime, public APIs, AI/semantic/vector
- Celery, Redis, RabbitMQ, Kafka, queue consumers
- Narrative `answer_text`, legal conclusions, recommendations
- Dry-run `skipped` path in v1 (recommendation — full persist only)

Authority: TASK-009C-PREAUTH — [`ANSWER_WORKER_CONTRACT.md`](ANSWER_WORKER_CONTRACT.md); [`TASKS/TASK-009C-ANSWER-WORKER.md`](TASKS/TASK-009C-ANSWER-WORKER.md)

**TASK-009C implementation remains NOT AUTHORIZED.**

Status:
LOCKED

---

## DEC-018 — Answer Worker Implementation Envelope (009C-v1)

TASK-009C implementation (when authorized) is bounded to **single-worker orchestration skeleton only**.

**Frozen package:**

```text
backend/app/workers/answer_runtime/
  models.py | worker.py | __init__.py
```

**Frozen entry:** `run_answer_worker(db, request) -> AnswerWorkerOutcome`

**Frozen delegation:**

- Sole write path: `persist_answer_for_ranking_request(...)` with `requested_by_actor_type="worker"`
- Read-only `list_*` for outcome count enrichment on **accepted** result only
- Prohibited: `assemble_answer_package`, `resolve_ranking_assembly_inputs`, all `create_answer_*`

**Frozen mapping:**

| Persistence | `worker_status` | `answer_status` |
|-------------|-----------------|-----------------|
| `completed` | `completed` | `completed` |
| `failed` | `failed` | `failed` |
| `duplicate_rejected` | `failed` | `duplicate_rejected` — **existing** `answer_request_id` (F-3) |

**Frozen OD-021:** process-local non-blocking mutex; no distributed workers or queue brokers

**Frozen tests:** `backend/tests/test_answer_worker_skeleton.py` — must assert **both** `worker_status` and `answer_status` (F-4)

**Prohibited in 009C:** migrations, ORM, persistence/assembly changes, queues, APIs, response runtime, AI, `CitationAssembler`, narrative fields, concurrent workers

Authority: TASK-009C-IMPL-AUTH — [`TASKS/TASK-009C-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-009C-IMPLEMENTATION-AUTHORIZATION.md)

**TASK-009C implementation:** **AUTHORIZED FOR LIMITED IMPLEMENTATION** — bounded worker skeleton per DEC-018.

**Remediation R-1 (non-blocking):** OD-021 mutex release — sequential non-concurrent invocations test in `test_answer_worker_skeleton.py`.

Status:
LOCKED

---

## DEC-019 — Response Runtime Boundary (010A-v1)

TASK-010A defines the **read-only delivery layer** above completed answer persistence.

**Core rule:** Response runtime **reads and renders** persisted answers — it does **not** retrieve, rank, assemble, persist, invoke workers, or generate legal conclusions.

**Frozen package (future):**

```text
backend/app/services/response_runtime/
```

**Frozen entry:** `build_response(db, request) -> ResponseOutcome`

**Frozen inputs:** `ResponseRequest` — `answer_request_id`, `contract_version` (`010A-v1`), `include_rendered_citation_text`, optional `answer_result_id`

**Frozen outputs:** `ResponsePackage` — deterministic delivery DTO; no persistence metadata leakage; no ORM objects

**Frozen read model:**

- `answer_results`, `answer_evidence_entries`, `answer_uncertainty_flags`
- Read-only provenance/citation joins via persisted pointers
- Permitted: `get_answer_*`, `list_*` from answer persistence only
- Evidence/uncertainty loaded from **accepted** sibling; terminal `completed` supplies eligibility

**Frozen rendering:** persisted `presentation_order_index` order only — no sort, filter, dedupe, inference

**Frozen citation rule:** read-only `CitationFormatter` permitted; `CitationAssembler` prohibited

**Frozen determinism:** same completed result × same rendering options → identical `ResponsePackage`; no timestamps in payload identity

**Frozen error vocabulary:** runtime-specific categories (`answer_not_completed`, `answer_not_deliverable`, …) — do not expose persistence/worker categories directly

**Prohibited in 010A:** retrieval/ranking/assembly execution, all `create_answer_*`, workers, queues, APIs, AI, `CitationAssembler`, narrative `answer_text`, legal conclusions, recommendations

Authority: TASK-010A-PREAUTH — [`RESPONSE_RUNTIME_CONTRACT.md`](RESPONSE_RUNTIME_CONTRACT.md); [`TASKS/TASK-010A-RESPONSE-RUNTIME.md`](TASKS/TASK-010A-RESPONSE-RUNTIME.md)

**TASK-010A implementation:** **ACCEPTED WITH FINDINGS** — delivered at `v0.2.4-response-runtime`.

**TASK-010A+ layer review:** **ACCEPTED WITH FINDINGS** — Response Runtime Layer complete; no API scope opened.

Status:
LOCKED

---

## DEC-020 — Response Runtime Implementation Envelope (010A-v1)

TASK-010A implementation (when authorized) is bounded to **read-only delivery runtime only**.

**Frozen package:**

```text
backend/app/services/response_runtime/
  models.py | runtime.py | rendering.py | __init__.py
```

**Frozen entry:** `build_response(db, request) -> ResponseOutcome`

**Frozen delegation:**

- Read-only: `get_answer_request`, `get_answer_result`, `list_results_for_request`, `list_evidence_entries_for_result`, `list_uncertainty_flags_for_result` (F-5 — **already exist**)
- Read-only provenance joins in `rendering.py` only
- Read-only `CitationFormatter` when `include_rendered_citation_text=true`
- Prohibited: all `create_answer_*`, `persist_answer_for_ranking_request`, `run_answer_worker`, `assemble_answer_package`

**Frozen `ResponseEvidenceEntry` (F-1 / OQ-R-09 Option A):**

- `legal_object_id` and `source_version_id` included as **read-only provenance references**
- Display/pass-through only — not authoritative; never interpreted or inferred; `null` when join unresolved

**Frozen rendering:** persisted `presentation_order_index` order only; G-11 determinism

**Frozen errors:** runtime vocabulary only — no persistence category reuse

**Frozen tests:** `backend/tests/test_response_runtime_skeleton.py`

**Prohibited in 010A:** migrations, ORM, persistence/assembly/worker changes, queues, APIs, AI, `CitationAssembler`, narrative fields, caching, streaming, pagination

Authority: TASK-010A-IMPL-AUTH — [`TASKS/TASK-010A-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-010A-IMPLEMENTATION-AUTHORIZATION.md)

**TASK-010A implementation:** **ACCEPTED WITH FINDINGS** — bounded runtime per DEC-020; tag `v0.2.4-response-runtime`. Non-blocking: citation-flag negative test, import guard token expansion, future D-R-06/G-05 doc reconciliation.

**TASK-010A+ layer review:** **ACCEPTED WITH FINDINGS** — Response Runtime Layer complete; tag `v0.2.6-response-runtime-layer-review`. No API-layer implementation or pre-authorization opened.

Status:
LOCKED

---

## DEC-021 — API Layer Boundary (011A-v1)

TASK-011A defines the **HTTP transport layer** strictly above response runtime.

**Core rule:** API layer **transports** `build_response` outcomes — it does **not** retrieve, rank, assemble, persist, invoke workers, render provenance joins directly, or generate legal conclusions.

**Frozen conceptual entry:** `POST /query/{answer_request_id}` — design only; no route implementation in PREAUTH

**Frozen API inputs:** `ApiDeliveryRequest` — `answer_request_id`, `api_contract_version` (`011A-v1`), `include_rendered_citation_text`, optional `answer_result_id`

**Frozen API → runtime mapping:** `011A-v1` → `ResponseRequest` with `contract_version=010A-v1`

**Frozen delegate:** `build_response(db, request)` — **sole** downstream entry; no reach-around into answer persistence, workers, or lower layers

**Frozen outputs:** `ApiDeliveryResponse` — external envelope; no persistence metadata, audit IDs, replay hashes, or worker fields

**Frozen HTTP mapping:** deterministic status table — 200 completed; 400 validation; 404 not found; 409 not ready / not deliverable; 503 incomplete / unavailable

**Frozen API error vocabulary:** `error_code` only — runtime `error_category` translated at boundary; persistence/worker categories never exposed

**Frozen determinism:** same `ApiDeliveryRequest` × same `ResponseOutcome` → identical HTTP payload and status

**Prohibited in 011A:** direct retrieval/ranking/assembly/persistence/worker imports, `CitationFormatter`/`CitationAssembler` at API, queues, auth implementation, caching, streaming, pagination, AI, narrative `answer_text`, legal conclusions, recommendations, FastAPI route implementation in PREAUTH

Authority: TASK-011A-PREAUTH — [`API_RUNTIME_CONTRACT.md`](API_RUNTIME_CONTRACT.md); [`TASKS/TASK-011A-API-LAYER.md`](TASKS/TASK-011A-API-LAYER.md)

**TASK-011A-PREAUTH:** **ACCEPTED WITH FINDINGS** — Claude governance review (20/20 checks); tag `v0.2.7-api-layer-preauth`. Non-blocking: Finding 4 (`response_metadata` → `delivery_metadata` mapping); Finding 5 (409 status tradeoff — distinguish via `error_code`).

**TASK-011A implementation remains NOT AUTHORIZED.**

Status:
LOCKED

---

## DEC-022 — API Layer Implementation Envelope (011A-v1)

TASK-011A implementation (when authorized) is bounded to **transport mapping above response runtime only**.

**Frozen package:**

```text
backend/app/api/delivery/
  models.py | mapper.py | errors.py | __init__.py
```

**Frozen entry:** `build_api_delivery_response(db, request) -> ApiDeliveryOutcome`

**Frozen delegate:** `build_response(db, ResponseRequest)` — **sole** downstream call

**Frozen API DTOs:** 5 top-level (`ApiDeliveryRequest`, `ApiDeliveryResponse`, `ApiDeliveryOutcome`, `ApiDeliveryError`, `ApiDeliveryMetadata`) + 3 nested (`ApiDeliveryCitationReference`, `ApiDeliveryEvidenceEntry`, `ApiDeliveryUncertaintyFlag`) = **8** total

**Frozen version map:** `011A-v1` → `010A-v1`

**Frozen metadata rule (Finding 4):** `response_metadata` null → `delivery_metadata` null; object → object; never synthesize empty object; never enrich

**Frozen HTTP mapping (Finding 5):** `answer_not_completed` / `answer_not_deliverable` → **409**; clients distinguish via `answer_not_ready` / `answer_not_deliverable`; `delivery_incomplete` → **503**

**Frozen failure shape:** nested `ApiDeliveryError` on `ApiDeliveryResponse.error` — **CLOSED** (implementation selected Option A; top-level error fields prohibited in 011A-v1)

**Frozen tests:** `backend/tests/test_api_delivery_skeleton.py` — no FastAPI TestClient; no routes

**Prohibited in 011A v1 slice:** FastAPI routes, middleware, auth, OpenAPI, migrations, ORM, persistence/assembly/worker/runtime changes, queues, AI, `CitationFormatter`/`CitationAssembler`, narrative fields, caching, streaming, pagination

Authority: TASK-011A-IMPL-AUTH — [`TASKS/TASK-011A-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-011A-IMPLEMENTATION-AUTHORIZATION.md)

**TASK-011A-IMPL-AUTH:** **ACCEPTED WITH FINDINGS** — Claude governance review (20/20 checks); tag `v0.2.8-api-layer-impl-auth`.

**TASK-011A implementation:** **ACCEPTED WITH FINDINGS** — bounded delivery skeleton per DEC-022; tag `v0.2.9-api-delivery-skeleton`. Nested `ApiDeliveryError` frozen. Non-blocking: Impl Finding 4 (`__all__` export guard — tested); Impl Finding 5 (`error_category=None` mapping — backlog).

Status:
LOCKED
