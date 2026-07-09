# TASK-011A — Implementation Authorization Package

## Status

**ACCEPTED WITH FINDINGS** — Claude governance review (20/20 checks); design package locked.

**TASK-011A implementation:** **ACCEPTED WITH FINDINGS** — tag `v0.2.9-api-delivery-skeleton`.

| Phase | Status |
|-------|--------|
| TASK-011A-PREAUTH | **ACCEPTED WITH FINDINGS** — DEC-021 |
| TASK-011A-IMPLEMENTATION-AUTHORIZATION (this document) | **ACCEPTED WITH FINDINGS** — DEC-022 |
| TASK-011A API layer code | **ACCEPTED WITH FINDINGS** — `v0.2.9-api-delivery-skeleton` |

## Accepted baseline

| Item | Value |
|------|--------|
| HEAD | `ce43078` (or newer accepted HEAD) |
| Tag | `v0.2.7-api-layer-preauth` |
| TASK-010A | **COMPLETE** — `v0.2.4-response-runtime` |
| TASK-010A+ | **COMPLETE** — `v0.2.6-response-runtime-layer-review` |
| TASK-011A-PREAUTH | **ACCEPTED WITH FINDINGS** — Claude review (20/20) |
| DEC-010 through DEC-021 | **LOCKED** |

## Binding upstream artifacts

- [`API_RUNTIME_CONTRACT.md`](../API_RUNTIME_CONTRACT.md) (011A-v1)
- [`TASKS/TASK-011A-API-LAYER.md`](TASK-011A-API-LAYER.md)
- [`RESPONSE_RUNTIME_CONTRACT.md`](../RESPONSE_RUNTIME_CONTRACT.md) (010A-v1)
- [`TASKS/TASK-010A-IMPLEMENTATION-AUTHORIZATION.md`](TASK-010A-IMPLEMENTATION-AUTHORIZATION.md) (pattern reference)
- [`DECISION_LOG.md`](../DECISION_LOG.md)

## Important

This package **does NOT implement** API code, FastAPI routes, handlers, middleware, workers, migrations, ORM models, persistence services, or tests.

---

## D-A-01 — Purpose

Lock the **bounded implementation envelope** for TASK-011A API layer — HTTP transport mapping above response runtime via `build_api_delivery_response` only.

Governance only. No production code. No API code. No routes. No handlers. No framework binding.

---

## D-A-02 — Authorized package

```text
backend/app/api/delivery/
```

**Exactly one package.** No subpackages. No parallel `api/query/`, `api/public/`, `delivery_worker/`, or `delivery_persistence/` modules.

**Rationale:** Existing registry admin CRUD lives under `backend/app/api/routes/`. Delivery transport is isolated to prevent conflation with internal registry mutations (DEC-021 / API-OQ admin separation).

---

## D-A-03 — Authorized files

| File | Responsibility |
|------|----------------|
| `models.py` | Frozen API DTOs, `CURRENT_API_CONTRACT_VERSION`, constants |
| `mapper.py` | `build_api_delivery_response`, request/response mapping |
| `errors.py` | API error codes, runtime → API translation, HTTP status table |
| `__init__.py` | Public exports |

**No other modules** in `delivery/`.

**Explicitly excluded from first authorized slice:**

| Excluded | Reason |
|----------|--------|
| `routes.py` / `router.py` | FastAPI route binding **not authorized** in v1 slice |
| `middleware.py` | Not authorized |
| `auth.py` / `dependencies.py` | Not authorized |
| `openapi.py` | Not authorized |
| OpenAPI / Swagger artifacts | Not authorized |
| Dependency / requirements changes | Not authorized |

Route file may be introduced only by a **future explicit route-binding gate** after this skeleton is accepted.

---

## D-A-04 — Public entry boundary

### Conceptual HTTP operation (not implemented here)

```text
POST /query/{answer_request_id}
```

### Frozen callable (future implementation)

```python
def build_api_delivery_response(
    db: Session,
    request: ApiDeliveryRequest,
) -> ApiDeliveryOutcome:
    """Single API delivery entrypoint — maps to build_response only."""
```

**No additional public entry points** in v1.

### Delegation rule (locked)

```text
build_api_delivery_response(db, api_request)
  → validate ApiDeliveryRequest
  → map to ResponseRequest
  → outcome = build_response(db, response_request)    # sole downstream call
  → map ResponseOutcome → ApiDeliveryOutcome
```

**Prohibited:** any call other than `build_response` into `app.services.*` or `app.workers.*`.

---

## D-A-05 — DTO freeze

### DTO inventory (Finding 3 — documentation sync)

| Tier | Count | Structures |
|------|-------|------------|
| **Top-level (required)** | **5** | `ApiDeliveryRequest`, `ApiDeliveryResponse`, `ApiDeliveryOutcome`, `ApiDeliveryError`, `ApiDeliveryMetadata` |
| **Nested (also frozen)** | **3** | `ApiDeliveryCitationReference`, `ApiDeliveryEvidenceEntry`, `ApiDeliveryUncertaintyFlag` |
| **Total frozen DTO structures** | **8** | All defined below — field definitions unchanged |

Summary tables elsewhere may list the 5 top-level DTOs only; nested types remain frozen and mandatory.

### Constants

```python
CURRENT_API_CONTRACT_VERSION = "011A-v1"
SUPPORTED_API_CONTRACT_VERSIONS = frozenset({"011A-v1"})

API_TO_RUNTIME_CONTRACT_VERSION = {
    "011A-v1": "010A-v1",
}
```

### `ApiDeliveryRequest`

| Field | Type | Default | Required | Source | Validation |
|-------|------|---------|----------|--------|------------|
| `answer_request_id` | UUID | — | YES | Path `{answer_request_id}` | Valid UUID instance |
| `api_contract_version` | str | `011A-v1` | YES | Body / query | Must be in `SUPPORTED_API_CONTRACT_VERSIONS` |
| `include_rendered_citation_text` | bool | `false` | NO | Body / query | Pass-through |
| `answer_result_id` | UUID \| None | `None` | NO | Body / query | Optional pin; pass-through when set |

### `ApiDeliveryMetadata`

| Field | Type | Notes |
|-------|------|-------|
| `rendering_mode` | str | Copied from `ResponseMetadata.rendering_mode` when present |
| `include_rendered_citation_text` | bool | Copied from `ResponseMetadata.include_rendered_citation_text` |
| `notes` | str \| None | Copied from `ResponseMetadata.notes` |

### `ApiDeliveryCitationReference`

| Field | Type | Notes |
|-------|------|-------|
| `citation_id` | str \| None | Copied from runtime |
| `citation_hash` | str \| None | Copied from runtime |
| `rendered_citation_text` | str \| None | Copied from runtime |

### `ApiDeliveryEvidenceEntry`

| Field | Type | Notes |
|-------|------|-------|
| `presentation_order_index` | int | Copied; order preserved |
| `retrieval_evidence_reference_id` | UUID | Copied |
| `ranked_evidence_reference_id` | UUID | Copied |
| `legal_object_id` | str \| None | Copied — display only |
| `source_version_id` | UUID \| None | Copied — display only |
| `object_identifier` | str \| None | Copied |
| `location_reference` | str \| None | Copied |
| `citation_reference` | `ApiDeliveryCitationReference` \| None | Copied |
| `entry_metadata` | dict \| None | Copied |

### `ApiDeliveryUncertaintyFlag`

| Field | Type | Notes |
|-------|------|-------|
| `flag_type` | str | Copied |
| `severity` | str | Copied |
| `message` | str | Copied |
| `related_evidence_ids` | list[UUID] | Copied |

### `ApiDeliveryError`

| Field | Type | When present | Notes |
|-------|------|--------------|-------|
| `error_code` | str | Failure only | API vocabulary (§D-A-08) |
| `error_message` | str \| None | Failure only | Human-readable; not legal advice |

### `ApiDeliveryResponse`

| Field | Type | When present | Notes |
|-------|------|--------------|-------|
| `api_contract_version` | str | Always | `011A-v1` |
| `delivery_status` | str | Always | `completed` \| `failed` |
| `answer_request_id` | UUID | Always | Caller anchor |
| `answer_result_id` | UUID \| None | Success | Terminal completed result |
| `rank_count` | int \| None | Success | From runtime package |
| `evidence_entries` | list[`ApiDeliveryEvidenceEntry`] | Success | Order preserved |
| `uncertainty_flags` | list[`ApiDeliveryUncertaintyFlag`] | Success | Copied |
| `delivery_metadata` | `ApiDeliveryMetadata` \| None | Success | See §D-A-06 Finding 4 rule |
| `error` | `ApiDeliveryError` \| None | Failure | API error envelope |

### Failure shape (IMPL-AUTH Finding 4 — CLOSED)

**Frozen v1 shape:** nested `ApiDeliveryError` on `ApiDeliveryResponse.error`.

| Option | Shape | Verdict |
|--------|-------|---------|
| **A** | Nested `ApiDeliveryError` object on `ApiDeliveryResponse.error` | **SELECTED / FROZEN** |
| **B** | Top-level `error_code` + `error_message` on `ApiDeliveryResponse` | **Rejected for 011A-v1** |

Top-level `error_code` / `error_message` fields on `ApiDeliveryResponse` are **prohibited** in 011A-v1.

### `ApiDeliveryOutcome`

| Field | Type | Notes |
|-------|------|-------|
| `http_status` | int | Frozen HTTP status (§D-A-07) |
| `response` | `ApiDeliveryResponse` | Governed external body |

### Explicitly excluded from all API DTOs

`ranking_request_id`, `retrieval_result_id`, `ranking_profile`, `replay_nonce`, `answer_request_hash`, worker IDs, audit IDs, persistence lifecycle IDs beyond approved anchors, raw `error_category`, raw SQL/ORM objects, `answer_text`, legal conclusions, recommendations, timestamps in payload identity.

---

## D-A-06 — Mapping rules

### ApiDeliveryRequest → ResponseRequest

```text
ResponseRequest(
  answer_request_id = api_request.answer_request_id,
  contract_version = API_TO_RUNTIME_CONTRACT_VERSION[api_request.api_contract_version],
  include_rendered_citation_text = api_request.include_rendered_citation_text,
  answer_result_id = api_request.answer_result_id,
)
```

| Rule | Requirement |
|------|-------------|
| Version map | `011A-v1` → `010A-v1` only |
| Pass-through | `include_rendered_citation_text`, `answer_result_id` unchanged |
| No enrichment | API must not add fields not in `ResponseRequest` |
| No inference | API must not derive ranking/retrieval anchors |

### ResponseOutcome → ApiDeliveryOutcome (success)

When `response_status == completed` and `response_package` is present:

| Step | Rule |
|------|------|
| Status | `http_status = 200` |
| `delivery_status` | `completed` |
| Evidence / flags | Field-wise copy to API DTOs; preserve order |
| `delivery_metadata` | **Finding 4 — CLOSED** (see below) |

### `response_metadata` → `delivery_metadata` (Finding 4 — frozen)

```text
response_metadata is None     → delivery_metadata is None
response_metadata is object   → ApiDeliveryMetadata field-wise copy
never synthesize {} when None
never enrich
never infer
```

### ResponseOutcome → ApiDeliveryOutcome (failure)

| Step | Rule |
|------|------|
| `delivery_status` | `failed` |
| `error_code` | Translate via §D-A-08 — never expose `error_category` |
| `error_message` | Copy from `ResponseOutcome.error_message` when present |
| `http_status` | §D-A-07 table |
| Success-only fields | Must be `None` / absent |

---

## D-A-07 — HTTP status mapping

Deterministic mapping. **Finding 5 — CLOSED** as intentional v1 trade-off.

### API-local validation (before `build_response`)

| Condition | API `error_code` | HTTP status |
|-----------|------------------|-------------|
| Malformed / missing `answer_request_id` | `invalid_request` | **400** |
| Unsupported `api_contract_version` | `unsupported_api_version` | **400** |
| Invalid optional UUID pin | `invalid_request` | **400** |
| Envelope schema violation | `invalid_request` | **400** |

### Runtime outcome mapping

| Runtime `response_status` | Runtime `error_category` | API `error_code` | HTTP status |
|---------------------------|--------------------------|------------------|-------------|
| `completed` | — | — | **200** |
| `failed` | `invalid_response_request` | `invalid_request` | **400** |
| `failed` | `contract_version_unsupported` | `unsupported_contract_version` | **400** |
| `failed` | `answer_request_not_found` | `answer_request_not_found` | **404** |
| `failed` | `answer_result_not_found` | `answer_result_not_found` | **404** |
| `failed` | `answer_not_completed` | `answer_not_ready` | **409** |
| `failed` | `answer_not_deliverable` | `answer_not_deliverable` | **409** |
| `failed` | `accepted_result_missing` | `delivery_incomplete` | **503** |
| `failed` | `evidence_count_mismatch` | `delivery_incomplete` | **503** |
| `failed` | `provenance_resolution_failed` | `delivery_incomplete` | **503** |
| `failed` | `citation_format_failed` | `delivery_incomplete` | **503** |
| `failed` | `response_pipeline_unavailable` | `service_unavailable` | **503** |
| `failed` | unmapped / unexpected | `service_unavailable` | **503** |

### Finding 5 — v1 409 trade-off (frozen)

```text
answer_not_completed  → HTTP 409 + error_code answer_not_ready
answer_not_deliverable → HTTP 409 + error_code answer_not_deliverable
```

Clients **must** use `error_code` in the response body to distinguish these cases. No retry headers. No background polling. No async job orchestration.

`delivery_incomplete` maps to **503** (frozen — not 409) to separate integrity/rendering failures from lifecycle-not-ready conflicts.

### Prohibited

- Framework-specific exception types
- Stack traces in production payloads
- Retry-After or polling hints
- Different HTTP status for the same `(response_status, error_category)` pair

---

## D-A-08 — API error vocabulary

### Frozen API error codes

```python
API_ERROR_CODES = frozenset({
    "invalid_request",
    "unsupported_api_version",
    "unsupported_contract_version",
    "answer_request_not_found",
    "answer_result_not_found",
    "answer_not_ready",
    "answer_not_deliverable",
    "delivery_incomplete",
    "service_unavailable",
})
```

### Runtime → API translation (complete)

| Runtime `error_category` | API `error_code` |
|--------------------------|------------------|
| `invalid_response_request` | `invalid_request` |
| `contract_version_unsupported` | `unsupported_contract_version` |
| `answer_request_not_found` | `answer_request_not_found` |
| `answer_result_not_found` | `answer_result_not_found` |
| `answer_not_completed` | `answer_not_ready` |
| `answer_not_deliverable` | `answer_not_deliverable` |
| `accepted_result_missing` | `delivery_incomplete` |
| `evidence_count_mismatch` | `delivery_incomplete` |
| `provenance_resolution_failed` | `delivery_incomplete` |
| `citation_format_failed` | `delivery_incomplete` |
| `response_pipeline_unavailable` | `service_unavailable` |
| *(unmapped)* | `service_unavailable` |

### Prohibited direct exposure

Persistence, ranking, worker, and raw runtime categories — including `duplicate_answer`, `permutation_mismatch`, `worker_status`, SQL errors.

---

## D-A-09 — Import boundary

### Allowed imports

| Import | Usage |
|--------|--------|
| `app.services.response_runtime.build_response` | Sole delegate |
| `app.services.response_runtime.ResponseRequest` | Runtime envelope |
| `app.services.response_runtime.ResponseOutcome` | Outcome mapping |
| `app.services.response_runtime.ResponsePackage` | Success mapping |
| `app.services.response_runtime.ResponseEvidenceEntry` | Nested copy |
| `app.services.response_runtime.ResponseUncertaintyFlag` | Nested copy |
| `app.services.response_runtime.ResponseCitationReference` | Nested copy |
| `app.services.response_runtime.ResponseMetadata` | Metadata mapping |
| `app.services.response_runtime.CURRENT_CONTRACT_VERSION` | Version constant |
| `sqlalchemy.orm.Session` | DB session |
| `uuid`, `dataclasses`, `typing` | Stdlib |

### Prohibited imports

| Prohibited |
|------------|
| `app.services.retrieval_execution` |
| `app.services.ranking_execution` |
| `app.workers.ranking_runtime` |
| `app.workers.retrieval_runtime` |
| `app.workers.answer_runtime` |
| `app.services.answer_assembly` |
| `app.services.answer_persistence` |
| `create_answer_*`, `persist_answer_for_ranking_request` |
| `assemble_answer_package`, `resolve_ranking_assembly_inputs` |
| `run_answer_worker`, `run_ranking_worker` |
| `app.services.citation.formatter.CitationFormatter` |
| `CitationAssembler` / `app.services.citation.assembler` |
| `app.services.ai`, `app.services.semantic`, `app.services.vector` |
| `fastapi`, `APIRouter`, `app.api.routes` |
| `celery`, `redis`, `rabbitmq`, `kafka` |

**Test guard:** static scan of all `api/delivery/*.py` for prohibited tokens.

---

## D-A-10 — Runtime behaviour

### Permitted sequence

```text
1. validate ApiDeliveryRequest
2. construct ResponseRequest
3. call build_response(db, response_request)
4. translate outcome → ApiDeliveryOutcome (status + body)
5. return ApiDeliveryOutcome
```

### Prohibited

| Operation | Verdict |
|-----------|---------|
| Writes / `commit` / `persist_*` / `create_*` | **PROHIBITED** |
| Retries | **PROHIBITED** |
| Enqueue / background execution | **PROHIBITED** |
| Orchestration (workers, ranking, answer pipeline) | **PROHIBITED** |
| Direct lower-layer table reads | **PROHIBITED** |
| Direct `CitationFormatter` / provenance resolution | **PROHIBITED** |
| Narrative text / legal conclusions | **PROHIBITED** |

---

## D-A-11 — Determinism

```text
same ApiDeliveryRequest
  × same ResponseOutcome from build_response
  = identical ApiDeliveryOutcome (http_status + response field-wise)
```

| Requirement | Rule |
|-------------|------|
| Timestamps in payload identity | **PROHIBITED** |
| Randomness | **PROHIBITED** |
| Generated content | **PROHIBITED** |
| Non-deterministic ordering | **PROHIBITED** |
| Enrichment beyond runtime | **PROHIBITED** |

---

## D-A-12 — Test authorization

### Authorized test file (when implementation authorized)

```text
backend/tests/test_api_delivery_skeleton.py
```

### Permitted test coverage

| Area | Allowed |
|------|---------|
| DTO validation | `ApiDeliveryRequest` envelope rules |
| Request → runtime mapping | `011A-v1` → `010A-v1`, pass-through fields |
| Runtime → API mapping | success and failure paths |
| Error vocabulary translation | full §D-A-08 table |
| HTTP status mapping | as data-driven table tests |
| `delivery_metadata` mapping | Finding 4: null/object; no empty synthesis |
| 409 trade-off | Finding 5: both categories → 409; distinct `error_code` |
| Import boundaries | static scan — no lower-layer tokens |
| Determinism | same inputs → same `ApiDeliveryOutcome` |
| Delegate-only | mock/patch `build_response`; no other service calls |

### Prohibited in tests

| Prohibited |
|------------|
| Integration HTTP server |
| `httpx` / `requests` against live server |
| FastAPI `TestClient` |
| External network |
| Auth / middleware tests |
| Worker tests |
| Route registration tests (routes not authorized) |

Tests may use `TEST_DATABASE_URL` only if `build_response` integration is exercised — prefer unit tests with mocked `build_response` for v1 skeleton.

---

## D-A-13 — Explicit non-goals

Individually **prohibited** unless a future task explicitly authorizes:

- FastAPI routes
- HTTP server binding
- OpenAPI / Swagger
- Middleware
- Authentication
- Authorization
- OAuth
- JWT
- Session management
- Rate limiting
- Caching
- Pagination
- Streaming
- Localization
- Version negotiation beyond `011A-v1` → `010A-v1`
- Observability / tracing / OpenTelemetry
- Workers
- Queues
- Redis
- RabbitMQ
- Kafka
- Celery
- AI / LLM
- Semantic search
- Vector search
- `CitationAssembler`
- `answer_text`
- Legal conclusions
- Recommendations
- Retrieval
- Ranking
- Answer assembly
- Answer persistence

---

## PREAUTH findings disposition

| ID | Finding | IMPL-AUTH disposition |
|----|---------|----------------------|
| **PREAUTH Finding 4** | `delivery_metadata` mapping | **CLOSED** — frozen in §D-A-05 / §D-A-06 |
| **PREAUTH Finding 5** | 409 status trade-off | **CLOSED** — frozen in §D-A-07; distinguish via `error_code` |

## IMPL-AUTH review findings (Claude)

**Verdict:** **ACCEPTED WITH FINDINGS** — 20/20 required checks; no blocking findings.

| ID | Finding | Disposition |
|----|---------|-------------|
| **Finding 3** | DTO count documentation sync (5 top-level + 3 nested = 8) | **CLOSED** — inventory table in §D-A-05 |
| **Finding 4** | Error shape choice (nested `ApiDeliveryError` vs top-level fields) | **CLOSED** — nested `ApiDeliveryError` frozen in implementation |

### Implementation review findings (Claude) — future hardening backlog

**Verdict:** **ACCEPTED WITH FINDINGS** — no blocking findings.

| ID | Finding | Disposition |
|----|---------|-------------|
| **Impl Finding 4** | `__all__` must export exactly one callable (`build_api_delivery_response`); remaining exports DTOs/constants only | **RECORDED** — covered by `test_public_exports_single_callable_only` |
| **Impl Finding 5** | Map `ResponseOutcome(error_category=None)` through full API path → expect `service_unavailable`; no runtime category leakage | **BACKLOG** — defense-in-depth; do not change runtime behaviour |

---

## Implementation checklist

- [x] Scope: `backend/app/api/delivery/` + `test_api_delivery_skeleton.py` only
- [x] Entry: `build_api_delivery_response` only
- [x] Delegate: `build_response` only
- [x] No routes, middleware, auth, OpenAPI
- [x] PREAUTH Finding 4 metadata rule enforced in mapper
- [x] PREAUTH Finding 5 status table enforced in `errors.py`
- [x] IMPL-AUTH Finding 4: nested `ApiDeliveryError` frozen
- [x] Import guard test passes
- [x] No FastAPI `TestClient`

---

## TASK-011A may build (when explicitly authorized)

| Artifact | Section |
|----------|---------|
| `backend/app/api/delivery/models.py` | §D-A-05 |
| `backend/app/api/delivery/mapper.py` | §D-A-04, §D-A-06 |
| `backend/app/api/delivery/errors.py` | §D-A-07, §D-A-08 |
| `backend/app/api/delivery/__init__.py` | Public exports |
| `backend/tests/test_api_delivery_skeleton.py` | §D-A-12 |

## TASK-011A must NOT build

| Artifact | Reason |
|----------|--------|
| `routes.py` / FastAPI routers | Route binding not authorized in v1 slice |
| Middleware / auth modules | §D-A-13 |
| OpenAPI artifacts | §D-A-13 |
| Migrations / ORM | Layer boundary |
| Worker / queue modules | Not authorized |

---

## Next gate

**API Layer Review (011A+).** FastAPI routes, HTTP transport, auth, queues, and AI remain **NOT AUTHORIZED**.

---

END OF TASK-011A IMPLEMENTATION AUTHORIZATION PACKAGE
