# API Runtime Contract

## Purpose

Define governed boundaries for the **API layer** — the HTTP transport boundary that exposes completed response runtime delivery to external clients.

This contract is **governance only** (TASK-011A-PREAUTH). It authorizes the API layer **design envelope** for downstream bounded implementation. It does **not** authorize FastAPI routes, HTTP handlers, middleware, authentication, authorization, OpenAPI generation, workers, queues, migrations, ORM models, persistence writes, tests, or narrative answer generation.

## Core principle

**The API layer transports response runtime outcomes — it does not retrieve, rank, assemble, persist, invoke workers, render citations directly, or conclude legal force.**

```text
HTTP request
  → parse + validate ApiDeliveryRequest
  → map to ResponseRequest
  → build_response(db, request)          # sole downstream delegate
  → map ResponseOutcome → ApiDeliveryResponse
  → HTTP status + serialized body
```

The API layer is **not**:

- retrieval execution or evidence selection (007E)
- ranking execution or permutation (008D)
- answer assembly (009A)
- answer persistence writes (009B)
- answer worker orchestration (009C)
- response rendering or provenance join logic (010A) — delegated only
- citation creation or `CitationAssembler` invocation
- semantic / vector search or AI answer generation
- queue brokers or background workers
- registry admin CRUD (existing internal routes — separate concern)

## Mandatory doctrines

| Doctrine | Rule |
|----------|------|
| **API consumes runtime only** (DEC-021) | HTTP boundary calls `build_response` — no reach-around into lower layers |
| **Provenance lives once** (DEC-010) | API does not duplicate or reinterpret provenance |
| **Answer ≠ legal conclusion** (DEC-013) | No applicability, legal force, or recommendations in HTTP payloads |
| **Delivery ≠ persistence** (DEC-019) | API does not write lifecycle rows or trigger workers |
| **Deterministic-first** (G-09) | Same HTTP request × same runtime outcome → identical HTTP payload |
| **Transport only** (G-07) | Validation, mapping, invocation, serialization — nothing else |

Upstream contracts (binding, closed):

- [`RESPONSE_RUNTIME_CONTRACT.md`](RESPONSE_RUNTIME_CONTRACT.md) (010A-v1)
- [`TASKS/TASK-010A-RESPONSE-RUNTIME.md`](TASKS/TASK-010A-RESPONSE-RUNTIME.md)
- [`TASKS/TASK-010A-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-010A-IMPLEMENTATION-AUTHORIZATION.md)
- [`ANSWER_PERSISTENCE_CONTRACT.md`](ANSWER_PERSISTENCE_CONTRACT.md) (009B-v1)
- [`ANSWER_WORKER_CONTRACT.md`](ANSWER_WORKER_CONTRACT.md) (009C-v1)
- [`TASKS/TASK-011A-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-011A-IMPLEMENTATION-AUTHORIZATION.md)
- [`DECISION_LOG.md`](DECISION_LOG.md) — DEC-010 through DEC-021, DEC-022, OD-021

---

## G-01 — Purpose and architectural boundary

### Purpose

The API layer exists **only** to expose **Response Runtime** delivery to external clients through a governed HTTP boundary.

It is the **sole authorized public entry** for answer delivery in future implementation. Clients must not be given alternate paths that bypass `build_response`.

### Architectural position

```text
Retrieval
  ↓
Ranking
  ↓
Ranking Worker
  ↓
Answer Assembly
  ↓
Answer Persistence
  ↓
Answer Worker
  ↓
Response Runtime (010A)
  ↓
API Layer (011A — transport only)
  ↓
External client
```

### Boundary rule

| Layer | Owns |
|-------|------|
| Response runtime | Read persisted answers; render `ResponsePackage` |
| **API layer** | **HTTP parsing, validation, DTO mapping, status codes, serialization** |
| Lower layers | **Not reachable from API** |

**Rule:** `response runtime` ≠ `public API`. Runtime renders; API transports.

---

## G-02 — Ownership

### The API layer owns

| Capability | Description |
|------------|-------------|
| HTTP request parsing | Extract path, query, and body fields into governed DTOs |
| API envelope validation | Validate `ApiDeliveryRequest` before runtime delegation |
| `ResponseRequest` construction | Map approved API inputs to frozen runtime envelope |
| Response runtime invocation | Call `build_response(db, request)` as **sole** downstream entry |
| HTTP response mapping | Map `ResponseOutcome` → `ApiDeliveryResponse` + HTTP status |
| API error translation | Map runtime `error_category` → API-only vocabulary (§G-10) |
| Serialization contract | Governed JSON field names for external clients (design only) |

### The API layer never owns

| Capability | Owner / rule |
|------------|--------------|
| Evidence retrieval or selection | Retrieval layer — **prohibited** |
| Ranking or re-ordering | Ranking layer — **prohibited** |
| Answer assembly | 009A — **prohibited** |
| Persistence writes | 009B — **prohibited** |
| Worker orchestration | 009C — **prohibited** |
| Provenance joins / citation formatting | 010A `rendering.py` — **prohibited** direct access |
| `CitationFormatter` / `CitationAssembler` | Runtime / citation governance — **prohibited** at API |
| Authentication / authorization enforcement | Future gate — **not in 011A-v1** |
| Rate limiting, caching, streaming | Future gate — **not in 011A-v1** |
| Narrative `answer_text`, legal conclusions, recommendations | **Prohibited** |
| Registry admin CRUD | Existing internal routes — **out of scope** for this contract |

---

## G-03 — Entry boundary (conceptual)

### Logical operation (frozen design concept)

```text
POST /query/{answer_request_id}
```

This is a **conceptual boundary only**.

- No route implementation in TASK-011A-PREAUTH
- No framework syntax, decorators, or handler code
- No OpenAPI artifact generation
- No HTTP framework selection lock

### Semantics (locked intent)

| Element | Rule |
|---------|------|
| Method | `POST` — read-only delivery over HTTP; no resource mutation |
| Path anchor | `answer_request_id` — primary delivery identifier (UUID) |
| Body | Optional delivery options (§G-04) |
| Success | HTTP 200 with `ApiDeliveryResponse` when runtime `response_status=completed` |
| Failure | Deterministic HTTP status per §G-06 |

### Future package (governance placeholder — not authorized)

```text
backend/app/api/delivery/
```

Separate from existing `backend/app/api/routes/` registry admin CRUD. Delivery API must not share handlers with registry mutations.

**No implementation in TASK-011A-PREAUTH.**

---

## G-04 — Input DTO

### `ApiDeliveryRequest` (frozen API envelope)

| Field | Source | Type | Default | Required | Validation |
|-------|--------|------|---------|----------|------------|
| `answer_request_id` | Path `{answer_request_id}` | UUID | — | YES | Valid UUID; passed to `ResponseRequest` |
| `contract_version` | Body or query | str | `011A-v1` | YES | Non-empty; must map to supported runtime version |
| `include_rendered_citation_text` | Body or query | bool | `false` | NO | Passed through to `ResponseRequest` |
| `answer_result_id` | Body or query | UUID \| null | `null` | NO | Optional pin; passed through when set |

### API → runtime version mapping (locked)

| `ApiDeliveryRequest.contract_version` | `ResponseRequest.contract_version` |
|---------------------------------------|-------------------------------------|
| `011A-v1` | `010A-v1` |

API contract version and runtime contract version are **distinct**. API validates its envelope first, then maps to the frozen runtime version. API must not accept arbitrary runtime version strings from clients without an explicit API-version mapping table.

### Prohibited API inputs

| Input | Reason |
|-------|--------|
| `ranking_request_id` | Upstream orchestration — not a delivery anchor |
| `retrieval_result_id` | Layer bypass — prohibited |
| `ranking_profile`, replay nonces, force flags | Persistence/worker concerns |
| `requested_by_actor_*` audit fields | Internal lifecycle — not client-supplied |
| `answer_request_hash` | Persistence metadata — not exposed |
| Free-form query / natural language | No AI or semantic input in 011A-v1 |
| Worker trigger flags | No orchestration at API boundary |

### `ResponseRequest` construction (locked)

```text
ResponseRequest(
  answer_request_id = ApiDeliveryRequest.answer_request_id,
  contract_version = mapped_runtime_version,   # 010A-v1 for 011A-v1
  include_rendered_citation_text = ApiDeliveryRequest.include_rendered_citation_text,
  answer_result_id = ApiDeliveryRequest.answer_result_id,
)
```

---

## G-05 — Output DTO

### `ApiDeliveryResponse` (frozen external envelope)

| Field | Type | When present | Notes |
|-------|------|--------------|-------|
| `api_contract_version` | str | Always | `011A-v1` |
| `delivery_status` | str | Always | `completed` \| `failed` — mirrors runtime success/failure at API boundary |
| `answer_request_id` | UUID | Always | Caller anchor |
| `answer_result_id` | UUID \| null | Success only | Terminal completed result delivered |
| `rank_count` | int \| null | Success only | From `ResponsePackage` |
| `evidence_entries` | list | Success only | Mapped from `ResponseEvidenceEntry` — order preserved |
| `uncertainty_flags` | list | Success only | Mapped from `ResponseUncertaintyFlag` |
| `delivery_metadata` | object \| null | Optional | Non-authoritative display block only |
| `error_code` | str \| null | Failure only | API vocabulary (§G-10) — not runtime category |
| `error_message` | str \| null | Failure only | Human-readable; not legal advice |

### Field mapping from `ResponsePackage` (success path)

API maps runtime DTO fields **without mutation**:

| Runtime field | API field | Rule |
|---------------|-----------|------|
| `contract_version` | *(internal)* | Not exposed — API exposes `api_contract_version` instead |
| `answer_request_id` | `answer_request_id` | Copy |
| `answer_result_id` | `answer_result_id` | Copy |
| `rank_count` | `rank_count` | Copy |
| `evidence_entries` | `evidence_entries` | Copy structure; no re-sort |
| `uncertainty_flags` | `uncertainty_flags` | Copy |
| `response_metadata` | `delivery_metadata` | Rename only; no enrichment — see mapping rule below |

**`response_metadata` → `delivery_metadata` mapping (locked — Finding 4 CLOSED in IMPL-AUTH):**

```text
null  → null
object → object   # field-wise copy; no enrichment
never synthesize an empty object when runtime value is null
```

### Explicitly excluded from HTTP responses

The API layer **must not** expose:

| Excluded | Reason |
|----------|--------|
| `answer_status` lifecycle values (`accepted`, `duplicate_rejected`, …) | Persistence internals |
| `accepted_ranking_result_id`, `terminal_ranking_result_id` | Persistence internals |
| `answer_request_hash`, `force_replay`, `replay_nonce` | Replay / audit internals |
| `requested_by_actor_*`, `created_at`, `updated_at` on persistence rows | Audit metadata |
| Worker fields (`worker_status`, mutex tokens) | Worker boundary |
| ORM instances or raw SQL row dumps | Implementation leakage |
| Runtime `error_category` strings directly | Use API translation layer (§G-10) |
| Narrative `answer_text`, `legal_conclusion`, `recommendation_text` | Not authorized |

---

## G-06 — Status mapping

Deterministic mapping from `ResponseOutcome` to HTTP status codes and `delivery_status`.

### Success

| Runtime | API `delivery_status` | HTTP status |
|---------|---------------------|-------------|
| `response_status=completed` | `completed` | **200 OK** |

### Failure mapping (locked)

| Runtime `error_category` | API `error_code` (§G-10) | HTTP status |
|--------------------------|--------------------------|-------------|
| `invalid_response_request` | `invalid_request` | **400 Bad Request** |
| `contract_version_unsupported` | `unsupported_contract_version` | **400 Bad Request** |
| `answer_request_not_found` | `answer_request_not_found` | **404 Not Found** |
| `answer_result_not_found` | `answer_result_not_found` | **404 Not Found** |
| `answer_not_completed` | `answer_not_ready` | **409 Conflict** |
| `answer_not_deliverable` | `answer_not_deliverable` | **409 Conflict** |
| `accepted_result_missing` | `delivery_incomplete` | **503 Service Unavailable** |
| `evidence_count_mismatch` | `delivery_incomplete` | **503 Service Unavailable** |
| `provenance_resolution_failed` | `delivery_incomplete` | **503 Service Unavailable** |
| `citation_format_failed` | `delivery_incomplete` | **503 Service Unavailable** |
| `response_pipeline_unavailable` | `service_unavailable` | **503 Service Unavailable** |
| Unmapped / unexpected | `service_unavailable` | **503 Service Unavailable** |

### v1 HTTP status tradeoff (Finding 5 — IMPL-AUTH carry-forward)

In **011A-v1**, both runtime categories:

```text
answer_not_completed
answer_not_deliverable
```

map to **409 Conflict**. Clients **must** distinguish them via API `error_code` in the response body:

| Runtime `error_category` | API `error_code` |
|--------------------------|------------------|
| `answer_not_completed` | `answer_not_ready` |
| `answer_not_deliverable` | `answer_not_deliverable` |

Alternative HTTP status splits (e.g. `424` for not-ready) are **deferred** to a future contract amendment. **Finding 5 CLOSED** in [`TASKS/TASK-011A-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-011A-IMPLEMENTATION-AUTHORIZATION.md) (§D-A-07) — intentional v1 409 trade-off frozen.

### API-local validation failures (before runtime call)

| Condition | API `error_code` | HTTP status |
|-----------|------------------|-------------|
| Malformed UUID in path | `invalid_request` | **400 Bad Request** |
| Unsupported `api_contract_version` | `unsupported_api_version` | **400 Bad Request** |
| Invalid JSON body | `invalid_request` | **400 Bad Request** |
| Mutually exclusive or out-of-schema fields | `invalid_request` | **400 Bad Request** |

### Prohibited in status mapping

- Framework-specific exception types or handler signatures
- Retry headers or automatic retry logic
- Different status codes for the same runtime outcome (non-determinism)
- Surfacing persistence/worker error categories without translation

---

## G-07 — Read-only rule

The API layer performs **only**:

1. **Validation** — API envelope and transport constraints
2. **Mapping** — API DTO ↔ `ResponseRequest` / `ResponseOutcome`
3. **Invocation** — `build_response(db, request)`
4. **Serialization** — governed JSON response body

### Prohibited operations

| Operation | Verdict |
|-----------|---------|
| Database writes (`commit`, `create_*`, `persist_*`) | **PROHIBITED** |
| Worker invocation (`run_answer_worker`, ranking/retrieval workers) | **PROHIBITED** |
| Orchestration (trigger ranking, trigger answer pipeline) | **PROHIBITED** |
| Retries (automatic or client-opaque) | **PROHIBITED** |
| Background execution / queue enqueue | **PROHIBITED** |
| Caching of delivery payloads | **PROHIBITED** in 011A-v1 |
| Direct table reads bypassing runtime | **PROHIBITED** |

---

## G-08 — Import boundary

### Allowed imports (future `delivery/` package)

| Permitted | Usage |
|-----------|--------|
| `app.services.response_runtime.build_response` | Sole downstream delegate |
| `app.services.response_runtime.ResponseRequest` | Runtime envelope construction |
| `app.services.response_runtime.ResponseOutcome` | Outcome mapping |
| `app.services.response_runtime.ResponsePackage` | Success payload mapping |
| `app.services.response_runtime.CURRENT_CONTRACT_VERSION` | Runtime version constant |
| `sqlalchemy.orm.Session` | DB session passed to `build_response` |
| `uuid`, `dataclasses` | Types / DTOs |

### Prohibited imports (frozen)

| Prohibited prefix / symbol |
|----------------------------|
| `app.services.retrieval_execution` |
| `app.services.ranking_execution` |
| `app.workers.ranking_runtime` |
| `app.workers.retrieval_runtime` |
| `app.workers.answer_runtime` |
| `app.services.answer_assembly` |
| `app.services.answer_persistence` (except via `build_response` — **no direct import**) |
| `create_answer_*`, `persist_answer_for_ranking_request` |
| `assemble_answer_package`, `resolve_ranking_assembly_inputs` |
| `run_answer_worker`, `run_ranking_worker` |
| `app.services.citation.formatter.CitationFormatter` |
| `CitationAssembler` / `app.services.citation.assembler` |
| `app.services.ai`, `app.services.semantic`, `app.services.vector` |
| `celery`, `redis`, `rabbitmq`, `kafka` |
| `fastapi` implementation coupling in service layer tests | *(governance: delivery package must not import lower layers; framework imports deferred to explicit IMPL-AUTH)* |

**Note:** Existing registry admin routes under `app.api.routes` are **legacy internal scope**. New delivery API must not import their handlers or blend responsibilities.

---

## G-09 — Determinism

```text
same ApiDeliveryRequest
  × same ResponseOutcome from build_response
  = identical ApiDeliveryResponse (field-wise) + identical HTTP status
```

| Requirement | Rule |
|-------------|------|
| Randomness in API payload | **PROHIBITED** |
| Timestamps in payload identity | **PROHIBITED** on success body |
| Non-deterministic field ordering | Serialization must use stable ordering |
| Enrichment beyond runtime output | **PROHIBITED** |
| Model-generated text | **PROHIBITED** in 011A-v1 |

---

## G-10 — Error vocabulary

### API-only error codes (locked)

| API `error_code` | Meaning |
|------------------|---------|
| `invalid_request` | API envelope or transport validation failure |
| `unsupported_api_version` | Unknown `api_contract_version` |
| `unsupported_contract_version` | API version ok but runtime mapping unsupported |
| `answer_request_not_found` | Delivery anchor missing |
| `answer_result_not_found` | Pinned result missing or mismatched |
| `answer_not_ready` | No terminal completed result available |
| `answer_not_deliverable` | Terminal failed / duplicate_rejected / skipped |
| `delivery_incomplete` | Runtime could not complete rendering (integrity/join/formatter) |
| `service_unavailable` | Unexpected internal failure |

### Translation rule (locked)

```text
runtime_error_category → api_error_code (§G-06 table)
```

API responses expose **`error_code` only** — never raw runtime `error_category` or persistence/worker categories.

### Prohibited API error exposure

`duplicate_answer`, `permutation_mismatch`, `ranking_request_missing`, `assembly_validation_failed`, `worker_status`, SQL errors, stack traces (production).

---

## G-11 — Future integration boundary

The following are **explicitly outside TASK-011A** and **not authorized** by this contract:

| Concern | Status |
|---------|--------|
| Authentication (OAuth, API keys, mTLS) | **Defer** — separate governance gate |
| Authorization (RBAC, tenancy, object-level ACL) | **Defer** |
| Rate limiting / throttling | **Defer** |
| Response caching (CDN, reverse proxy, app cache) | **Defer** |
| Localization / multilingual payloads | **Defer** |
| Version negotiation (Accept header, semver routing) | **Defer** — API-OQ-02 |
| Pagination for large evidence sets | **Defer** — API-OQ-03 |
| Streaming / SSE / chunked transfer | **Defer** — API-OQ-05 |
| Observability (metrics, structured logging policy) | **Defer** — document only |
| Distributed tracing (OpenTelemetry) | **Defer** |
| Idempotency keys | **Defer** — API-OQ-07 |
| Correlation / request IDs | **Defer** — API-OQ-08 |
| Webhooks / async delivery | **Defer** — not in 011A-v1 |

No implementation of any item in this section is authorized by TASK-011A-PREAUTH.

---

## G-12 — Explicit non-goals

Individually **prohibited** in TASK-011A-PREAUTH and 011A-v1 unless a future task explicitly authorizes:

| Non-goal | Verdict |
|----------|---------|
| FastAPI route implementation | **PROHIBITED** |
| HTTP route registration | **PROHIBITED** |
| Middleware (auth, CORS policy implementation, request ID) | **PROHIBITED** |
| OAuth / OIDC | **PROHIBITED** |
| JWT / session management | **PROHIBITED** |
| Workers | **PROHIBITED** |
| Queues | **PROHIBITED** |
| Redis | **PROHIBITED** |
| RabbitMQ / Kafka | **PROHIBITED** |
| Background execution | **PROHIBITED** |
| AI / LLM answer generation | **PROHIBITED** |
| Narrative `answer_text` creation | **PROHIBITED** |
| Legal conclusions | **PROHIBITED** |
| Recommendations | **PROHIBITED** |
| `CitationAssembler` | **PROHIBITED** |
| Direct `CitationFormatter` use at API | **PROHIBITED** |
| Retrieval execution / persistence | **PROHIBITED** |
| Ranking execution / persistence | **PROHIBITED** |
| Answer assembly | **PROHIBITED** |
| Answer persistence writes | **PROHIBITED** |
| Answer worker orchestration | **PROHIBITED** |
| OpenAPI / Swagger generation | **PROHIBITED** in PREAUTH |
| Deployment artifacts (Docker, K8s, Terraform) | **PROHIBITED** |
| Database migrations / ORM changes | **PROHIBITED** |

---

## Open questions

| ID | Question | Recommendation |
|----|----------|----------------|
| API-OQ-01 | Authentication strategy (API keys vs OAuth vs mTLS)? | **Defer** — document options only; no implementation in 011A-v1 |
| API-OQ-02 | HTTP version negotiation (`011A-v2`, Accept header, URL prefix)? | **Defer** — freeze `011A-v1` mapping table; negotiation is future gate |
| API-OQ-03 | Pagination for large `evidence_entries`? | **Defer** — v1 returns full ordered list per runtime; pagination requires amendment |
| API-OQ-04 | Localization of `error_message` / display fields? | **Defer** — pass-through from runtime only; no translation layer in v1 |
| API-OQ-05 | Streaming responses? | **Defer** — not authorized in 011A-v1 |
| API-OQ-06 | Response caching (CDN, ETag, Cache-Control)? | **Defer** — no cache headers in v1; determinism requires explicit policy gate |
| API-OQ-07 | Idempotency keys for `POST /query/{answer_request_id}`? | **Defer** — read-only delivery; idempotency semantics TBD at IMPL-AUTH |
| API-OQ-08 | Correlation IDs (`X-Request-ID`) and tracing propagation? | **Defer** — observability gate; not in PREAUTH |

Every recommendation **defers implementation**. No open question authorizes code in TASK-011A-PREAUTH.

---

## Architectural risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| API bypasses runtime and reads persistence tables | High | Freeze import guards; single delegate `build_response`; review scans |
| Persistence metadata leaks in JSON | High | Explicit excluded-field list in §G-05 |
| Runtime error categories exposed to clients | Medium | §G-10 translation layer mandatory |
| Registry admin routes conflated with delivery API | Medium | Separate `api/delivery/` package; distinct contract |
| Framework coupling in domain package | Medium | Defer FastAPI imports to explicit IMPL-AUTH boundary |
| Large evidence payloads over HTTP | Medium | API-OQ-03 — defer pagination; monitor at IMPL-AUTH |

---

## Readiness checklist

### Completed prerequisites (TASK-011A-PREAUTH)

| ID | Criterion | Status |
|----|-----------|--------|
| R-01 | Response runtime accepted (010A) | **MET** |
| R-02 | Response runtime layer review accepted (010A+) | **MET** |
| R-03 | DEC-010 through DEC-020 locked | **MET** |
| R-04 | API runtime contract (this document) | **MET** |
| R-05 | DEC-021 locked | **MET** (this pre-auth) |

### Future implementation prerequisites (NOT MET)

| ID | Criterion |
|----|-----------|
| I-01 | Claude review of TASK-011A-PREAUTH | **MET** — ACCEPTED WITH FINDINGS |
| I-02 | TASK-011A-IMPL-AUTH design package | **MET** |
| I-03 | Claude review of TASK-011A-IMPL-AUTH | **MET** — ACCEPTED WITH FINDINGS |
| I-04 | Explicit **AUTHORIZED FOR LIMITED IMPLEMENTATION** prompt | **MET** |
| I-05 | Bounded `api/delivery/` skeleton + tests | **MET** — `v0.2.9-api-delivery-skeleton` |
| I-06 | API Layer Review (011A+) | **NOT MET** — next gate |

### Future review gate

```text
TASK-011A-PREAUTH — ACCEPTED WITH FINDINGS
  → TASK-011A-IMPL-AUTH — ACCEPTED WITH FINDINGS (DEC-022)
  → TASK-011A implementation — ACCEPTED WITH FINDINGS (v0.2.9-api-delivery-skeleton)
  → API Layer Review (011A+) — next gate
```

**TASK-011A-PREAUTH:** **ACCEPTED WITH FINDINGS** — tag `v0.2.7-api-layer-preauth`.

**TASK-011A-IMPL-AUTH:** **ACCEPTED WITH FINDINGS** — tag `v0.2.8-api-layer-impl-auth`.

**TASK-011A implementation:** **ACCEPTED WITH FINDINGS** — tag `v0.2.9-api-delivery-skeleton`. Nested `ApiDeliveryError` frozen. FastAPI routes **NOT AUTHORIZED**.

---

## Explicit prohibitions (this contract)

- No API implementation in TASK-011A-PREAUTH
- No FastAPI routes, middleware, auth, or OpenAPI artifacts
- No migrations, ORM models, persistence services, workers, or queues
- No direct imports of retrieval, ranking, assembly, persistence, workers, or citation formatters
- No `CitationAssembler`, AI, semantic, or vector imports
- No narrative `answer_text`, legal conclusions, or recommendations in 011A-v1
- No reach-around `build_response` into lower layers

---

END OF API RUNTIME CONTRACT (implementation NOT AUTHORIZED)
