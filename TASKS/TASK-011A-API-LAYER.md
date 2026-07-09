# TASK-011A — API Layer Pre-Authorization

## Status

**TASK-011A-PREAUTH** — **ACCEPTED WITH FINDINGS** — DEC-021.

| Phase | Status |
|-------|--------|
| Response runtime (010A) | **COMPLETE** / **ACCEPTED WITH FINDINGS** — `v0.2.4-response-runtime` |
| Response runtime layer review (010A+) | **COMPLETE** / **ACCEPTED WITH FINDINGS** — `v0.2.6-response-runtime-layer-review` |
| TASK-011A-PREAUTH (this document) | **ACCEPTED WITH FINDINGS** — DEC-021 |
| TASK-011A-IMPL-AUTH | **NOT STARTED** — next gate |
| TASK-011A API layer code | **NOT AUTHORIZED** |

## Prerequisite chain

```text
007A–007E Retrieval (complete)
  → 008B–008D, U-01, 008A+ Ranking (complete)
  → 009A Assembly → 009B Persistence → 009C Worker (complete)
  → 010A Response Runtime → 010A+ Layer Review (complete)
  → 011A-PREAUTH (accepted with findings — Claude review)
  → 011A-IMPL-AUTH — next gate
  → 011A Implementation — NOT AUTHORIZED
```

## Important

- **Does NOT implement** FastAPI routes, HTTP handlers, middleware, auth, workers, APIs, persistence, models, migrations, or tests
- **Does NOT authorize** queue infrastructure, AI generation, `CitationAssembler`, narrative `answer_text`, or legal conclusions
- **Does NOT modify** response runtime, answer stack, ranking, or retrieval layers
- **Does NOT reach around** `build_response` into lower layers

## Objective

Establish the governed API layer contract — HTTP transport boundary above response runtime only — preserving DEC-010 through DEC-020 and OD-021.

## Canonical artifacts

| Artifact | Path |
|----------|------|
| Primary contract | [`API_RUNTIME_CONTRACT.md`](../API_RUNTIME_CONTRACT.md) |
| Response runtime (downstream delegate) | [`RESPONSE_RUNTIME_CONTRACT.md`](../RESPONSE_RUNTIME_CONTRACT.md) |
| Response runtime task record | [`TASKS/TASK-010A-RESPONSE-RUNTIME.md`](TASK-010A-RESPONSE-RUNTIME.md) |
| Decision locks | [`DECISION_LOG.md`](../DECISION_LOG.md) — DEC-021 |

## Governance decisions delivered

### G-01 Purpose and boundary

API layer exists only to expose Response Runtime to external clients. Strictly above 010A; no reach-around.

### G-02 Ownership

Owns: HTTP parsing, API validation, `ResponseRequest` mapping, `build_response` invocation, HTTP status mapping, serialization.

Never owns: retrieval, ranking, assembly, persistence, workers, rendering joins, auth, caching, AI.

### G-03 Entry boundary

Conceptual operation: `POST /query/{answer_request_id}` — design only; no route implementation.

### G-04 Input DTO

`ApiDeliveryRequest` — `answer_request_id`, `api_contract_version` (`011A-v1`), `include_rendered_citation_text`, optional `answer_result_id`. Maps to `ResponseRequest` with version table `011A-v1` → `010A-v1`.

### G-05 Output DTO

`ApiDeliveryResponse` — external envelope mapped from `ResponseOutcome` / `ResponsePackage`. No persistence metadata, audit IDs, replay hashes, or worker fields.

### G-06 Status mapping

Deterministic HTTP status table: 200 success; 400 validation; 404 not found; 409 not ready / not deliverable; 503 incomplete / unavailable.

### G-07 Read-only rule

Validation, mapping, invocation, serialization only. No writes, orchestration, retries, or persistence.

### G-08 Import boundary

Allowed: `build_response` and public response runtime DTOs only.

Prohibited: retrieval, ranking, workers, persistence, assembly, `CitationFormatter`, `CitationAssembler`, AI, queues.

### G-09 Determinism

Same API request × same runtime outcome = identical HTTP payload and status.

### G-10 Error vocabulary

API-only `error_code` list with mandatory runtime → API translation. No direct runtime category exposure.

### G-11 Future integration boundary

Auth, authorization, rate limiting, caching, localization, version negotiation, pagination, streaming, observability, tracing — all deferred; not authorized.

### G-12 Explicit non-goals

Individually prohibits FastAPI implementation, routes, middleware, OAuth, JWT, workers, queues, Redis, RabbitMQ, Kafka, AI, legal conclusions, and lower-layer reach-around.

## Pattern reference

| Layer | Delivery pattern |
|-------|-------------------|
| Response runtime (010A) | `build_response` → `ResponsePackage` |
| **API layer (011A)** | HTTP → `ApiDeliveryRequest` → `build_response` → `ApiDeliveryResponse` |

## Explicit prohibitions

| Prohibited | |
|------------|--|
| API implementation | This task |
| FastAPI routes / handlers | Not authorized |
| Middleware / auth / OAuth / JWT | Not authorized |
| Workers / queues | Not authorized |
| Persistence / assembly / retrieval / ranking | Not authorized |
| AI / semantic / vector | Not authorized |
| `CitationAssembler` / direct `CitationFormatter` | Not authorized |
| `answer_text` / legal conclusions | Not authorized in 011A-v1 |

## Open questions

API-OQ-01 through API-OQ-08 documented in contract — all defer implementation.

## Review result (Claude governance)

**Verdict:** **ACCEPTED WITH FINDINGS** — 20/20 required checks passed; no blocking findings.

TASK-011A-PREAUTH may proceed to governance commit and tag. TASK-011A implementation remains **NOT AUTHORIZED**. TASK-011A-IMPL-AUTH may begin only after PREAUTH governance has been committed and tagged.

### Non-blocking findings (IMPL-AUTH carry-forward)

| ID | Finding | Disposition |
|----|---------|-------------|
| **Finding 4** | Clarify `response_metadata` → `delivery_metadata` mapping | **Recorded** — `null` → `null`; object → object; never synthesize empty object |
| **Finding 5** | v1 HTTP status tradeoff for `answer_not_completed` / `answer_not_deliverable` | **Recorded** — both map to 409; distinguish via API `error_code` (`answer_not_ready` vs `answer_not_deliverable`) |

## Architectural risks

Documented in contract — runtime bypass, metadata leakage, error vocabulary leakage, admin route conflation.

## Next gate

**TASK-011A-IMPL-AUTH** — API Layer Implementation Authorization design package. Implementation, FastAPI routes, and HTTP delivery remain **NOT AUTHORIZED** until explicit IMPL-AUTH acceptance and implementation authorization.

---

END OF TASK-011A PRE-AUTHORIZATION
