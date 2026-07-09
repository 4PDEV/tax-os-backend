# TASK-010A — Implementation Authorization Package

## Status

**COMPLETE** / **ACCEPTED** — design package accepted; implementation delivered (`v0.2.4-response-runtime`).

| Phase | Status |
|-------|--------|
| TASK-010A-PREAUTH | **ACCEPTED** — DEC-019 |
| TASK-010A-IMPLEMENTATION-AUTHORIZATION (this document) | **ACCEPTED** — DEC-020 |
| TASK-010A response runtime code | **ACCEPTED WITH FINDINGS** — `v0.2.4-response-runtime` |

## Accepted baseline

| Item | Value |
|------|--------|
| HEAD | `9e1d5fa` (or newer accepted HEAD) |
| Tag | `v0.2.3-answer-worker-skeleton` |
| TASK-009A | **COMPLETE** — `v0.1.8-answer-assembly` |
| TASK-009B | **COMPLETE** — `v0.1.9-answer-persistence` |
| TASK-009C | **COMPLETE** — `v0.2.3-answer-worker-skeleton` |
| TASK-010A-PREAUTH | **ACCEPTED** — Claude review |
| DEC-010 through DEC-019 | **LOCKED** |

## Binding upstream artifacts

- [`RESPONSE_RUNTIME_CONTRACT.md`](../RESPONSE_RUNTIME_CONTRACT.md) (010A-v1)
- [`TASKS/TASK-010A-RESPONSE-RUNTIME.md`](TASK-010A-RESPONSE-RUNTIME.md)
- [`ANSWER_PERSISTENCE_CONTRACT.md`](../ANSWER_PERSISTENCE_CONTRACT.md) (009B-v1)
- [`ANSWER_WORKER_CONTRACT.md`](../ANSWER_WORKER_CONTRACT.md) (009C-v1)
- [`ANSWER_ASSEMBLY_CONTRACT.md`](../ANSWER_ASSEMBLY_CONTRACT.md) (009A-v1)
- [`TASKS/TASK-009C-IMPLEMENTATION-AUTHORIZATION.md`](TASK-009C-IMPLEMENTATION-AUTHORIZATION.md) (pattern reference)
- [`DECISION_LOG.md`](../DECISION_LOG.md)

## Important

This package **does NOT implement** runtime code, APIs, workers, migrations, ORM models, persistence services, or tests.

---

## 1. Purpose

Lock the **bounded implementation envelope** for TASK-010A response runtime — read-only delivery from completed answer persistence via `build_response` only.

Governance only. No production code in this task.

---

## 2. Scope

### Authorized package (when explicitly authorized)

```text
backend/app/services/response_runtime/
```

**Exactly one package.** No subpackages. No parallel `response_api/`, `response_worker/`, or `response_persistence/` modules.

---

## 3. Entry point (frozen)

```python
def build_response(
    db: Session,
    request: ResponseRequest,
) -> ResponseOutcome:
    """Single delivery entrypoint for response runtime."""
```

**No additional public entry points** in v1.

Optional helper (in `runtime.py` only):

```python
def build_response_request(
    *,
    answer_request_id: UUID,
    contract_version: str = CURRENT_CONTRACT_VERSION,
    include_rendered_citation_text: bool = False,
    answer_result_id: UUID | None = None,
) -> ResponseRequest:
    ...
```

---

## D-R-01 — Module layout (frozen)

| Module | Responsibility |
|--------|----------------|
| `models.py` | `ResponseRequest`, `ResponseOutcome`, `ResponsePackage`, nested DTOs, `ResponseRuntimeError`, `CURRENT_CONTRACT_VERSION` |
| `runtime.py` | `ResponseRuntime`, `build_response`, `build_response_request`, resolution + orchestration |
| `rendering.py` | Deterministic field mapping, provenance join reads, `CitationFormatter` gate |
| `__init__.py` | Public exports |

**No other modules** in `response_runtime/`. No `api.py`, `queue.py`, `broker.py`, `tasks.py`, or `worker.py`.

---

## D-R-02 — Module responsibilities

### `models.py`

- Frozen dataclass DTOs (§D-R-03)
- `ResponseRuntimeError` exception type
- `CURRENT_CONTRACT_VERSION = "010A-v1"`
- Runtime error category constants (optional frozen frozenset mirroring §D-R-07)

### `runtime.py`

- `ResponseRuntime.validate_request()` — envelope validation before reads
- Terminal `completed` result resolution (G-03 rules)
- Accepted sibling lookup for evidence/uncertainty children
- Delegation to `rendering.py` for package construction
- `ResponseOutcome` assembly and persistence-terminal → runtime error mapping (§D-R-07)
- **No** SQL joins beyond orchestration delegation
- **No** writes, workers, retries, or queue logic

### `rendering.py`

- Map persisted rows → `ResponsePackage` / nested DTOs
- Read-only provenance resolution via `retrieval_evidence_references` (and justified citation/legal-object joins)
- `CitationFormatter` invocation when `include_rendered_citation_text=true`
- Enforce G-06 order and G-11 determinism
- **No** assembly, persistence, retrieval, or ranking calls

### `__init__.py`

- Export `build_response`, `build_response_request`, public DTOs, `ResponseRuntimeError`, `CURRENT_CONTRACT_VERSION`

---

## D-R-03 — Frozen DTOs

### `ResponseRequest`

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `answer_request_id` | UUID | required | Must be `UUID` instance |
| `contract_version` | str | `010A-v1` | Non-empty; must equal supported version |
| `include_rendered_citation_text` | bool | `false` | |
| `answer_result_id` | UUID \| None | `None` | When set, must belong to `answer_request_id` |

### `ResponseOutcome`

| Field | Type | Notes |
|-------|------|-------|
| `response_status` | str | `completed` \| `failed` only |
| `response_package` | `ResponsePackage` \| None | Present when `response_status=completed` |
| `error_category` | str \| None | Runtime vocabulary only (§D-R-07) |
| `error_message` | str \| None | Human-readable; not legal advice |

### `ResponsePackage`

| Field | Type | Notes |
|-------|------|-------|
| `contract_version` | str | `010A-v1` |
| `answer_request_id` | UUID | Delivery anchor |
| `answer_result_id` | UUID | Terminal `completed` result rendered |
| `rank_count` | int | From terminal completed result |
| `evidence_entries` | list[`ResponseEvidenceEntry`] | Ordered by `presentation_order_index` |
| `uncertainty_flags` | list[`ResponseUncertaintyFlag`] | From accepted sibling |
| `response_metadata` | `ResponseMetadata` \| None | Optional non-authoritative block |

**Excluded (must not appear):** persistence lifecycle fields, hashes, replay fields, ranking result IDs, timestamps, `answer_text`, legal conclusions.

### `ResponseEvidenceEntry` (F-1 / OQ-R-09 locked — Option A)

| Field | Type | Notes |
|-------|------|-------|
| `presentation_order_index` | int | From persisted entry |
| `retrieval_evidence_reference_id` | UUID | Provenance anchor |
| `ranked_evidence_reference_id` | UUID | Persisted pointer |
| `legal_object_id` | str \| None | **Read-only provenance reference** — display/pass-through only; not authoritative; never interpreted or inferred |
| `source_version_id` | UUID \| None | **Read-only provenance reference** — display/pass-through only; not authoritative; never interpreted or inferred |
| `object_identifier` | str \| None | From retrieval evidence join |
| `location_reference` | str \| None | From retrieval evidence join |
| `citation_reference` | `ResponseCitationReference` \| None | |
| `entry_metadata` | dict \| None | Non-authoritative hints only |

**Provenance resolution (locked):**

```text
for each answer_evidence_entry on accepted result:
    join retrieval_evidence_references by retrieval_evidence_reference_id
    legal_object_id = row.legal_object_id or null
    source_version_id = row.source_version_id or null
    object_identifier = row.object_identifier or null
    location_reference = row.location_reference or null
    # no inference when null — do not fabricate
```

### `ResponseCitationReference`

| Field | Type | Notes |
|-------|------|-------|
| `citation_id` | str \| None | From resolved citation row |
| `citation_hash` | str \| None | From resolved citation row |
| `rendered_citation_text` | str \| None | Only when `include_rendered_citation_text=true`; not authoritative |

### `ResponseUncertaintyFlag`

| Field | Type | Notes |
|-------|------|-------|
| `flag_type` | str | `conflict` \| `ambiguity` \| `incomplete_provenance` \| `zero_evidence` \| `other` |
| `severity` | str | `informational` \| `warning` \| `error` |
| `message` | str | From persisted flag |
| `related_evidence_ids` | list[UUID] | `retrieval_evidence_reference_id` values |

### `ResponseMetadata`

| Field | Type | Notes |
|-------|------|-------|
| `rendering_mode` | str | `deterministic` only in 010A-v1 |
| `include_rendered_citation_text` | bool | Echo request flag |
| `notes` | str \| None | Optional |

---

## D-R-04 — Validation gates (G-01–G-12 carry-forward)

No weakening. No additions beyond accepted contract.

| Gate | Requirement |
|------|-------------|
| **G-01** | Read + render only — prohibited capabilities blocked at import and runtime |
| **G-02** | Single package `response_runtime/`; single entry `build_response` |
| **G-03** | `ResponseRequest` fields + terminal resolution rules unchanged |
| **G-04** | `ResponsePackage` schema frozen; no persistence metadata leakage |
| **G-05** | Read model + accepted-row attachment rule enforced |
| **G-06** | Persisted order only — no sort/filter/dedupe/inference |
| **G-07** | `CitationFormatter` only when flag set; `CitationAssembler` prohibited |
| **G-08** | Runtime error vocabulary only at delivery boundary |
| **G-09** | Import guards — static test required |
| **G-10** | Layer separation preserved — no upstream orchestration |
| **G-11** | Deterministic payload identity — no timestamps in `ResponsePackage` |
| **G-12** | Prerequisites met; implementation awaits explicit authorization |

### Pre-read validation (`validate_request`)

| Condition | Behavior |
|-----------|----------|
| Invalid `answer_request_id` type | Raise `ResponseRuntimeError` → `invalid_response_request` |
| Empty `contract_version` | Raise `ResponseRuntimeError` → `invalid_response_request` |
| Unsupported `contract_version` | Raise `ResponseRuntimeError` → `contract_version_unsupported` |
| `answer_request_not_found` | After `get_answer_request` returns `None` |

### Post-resolution validation

| Condition | Behavior |
|-----------|----------|
| No terminal `completed` result | `answer_not_completed` |
| Terminal `failed` / `duplicate_rejected` / `skipped` | `answer_not_deliverable` |
| Pinned `answer_result_id` mismatch | `answer_result_not_found` |
| Missing accepted sibling | `accepted_result_missing` |
| `len(evidence_entries) != rank_count` when `rank_count > 0` | `evidence_count_mismatch` |
| Provenance join failure | `provenance_resolution_failed` |
| Formatter failure when flag enabled | `citation_format_failed` |

---

## D-R-05 — Approved read dependencies (F-5)

**Verified:** `get_answer_request()` and `get_answer_result()` **already exist** in answer persistence.

| API | Location | Status |
|-----|----------|--------|
| `get_answer_request(session, *, answer_request_id)` | `backend/app/services/answer_persistence/persistence.py` | **APPROVED** — exported in `answer_persistence.__init__` |
| `get_answer_result(session, *, answer_result_id)` | `backend/app/services/answer_persistence/persistence.py` | **APPROVED** — exported in `answer_persistence.__init__` |
| `list_results_for_request` | same module | **APPROVED** |
| `list_evidence_entries_for_result` | same module | **APPROVED** |
| `list_uncertainty_flags_for_result` | same module | **APPROVED** |

**F-5 disposition:** No Answer Persistence amendment required before TASK-010A implementation. Runtime may import these read APIs as frozen in G-09 / DEC-019.

**Prohibited persistence imports:** all `create_answer_*`, `persist_answer_for_ranking_request`, `AnswerPersistenceOutcome` write orchestration paths.

### Terminal resolution algorithm (locked)

```text
if request.answer_result_id:
    terminal = get_answer_result(answer_result_id)
    verify terminal.answer_request_id == request.answer_request_id
else:
    results = list_results_for_request(answer_request_id)
    terminal = latest row where answer_status == "completed" (created_at desc)

if terminal.answer_status != "completed":
    return failed ResponseOutcome (answer_not_deliverable)

results = list_results_for_request(answer_request_id)
accepted = sole row where answer_status == "accepted"
evidence = list_evidence_entries_for_result(accepted.id) ordered ASC
flags = list_uncertainty_flags_for_result(accepted.id)
render ResponsePackage from terminal + accepted children
```

---

## D-R-06 — Import boundary (frozen)

### Prohibited imports in `response_runtime/`

| Prohibited prefix / symbol |
|----------------------------|
| `app.services.retrieval_execution` |
| `app.services.ranking_execution` |
| `app.workers.ranking_runtime` |
| `app.workers.retrieval_runtime` |
| `app.workers.answer_runtime` |
| `app.services.answer_assembly` |
| `app.services.answer_assembly.assembly` |
| `create_answer_request`, `create_answer_result`, `create_answer_evidence_entry`, `create_answer_uncertainty_flag` |
| `persist_answer_for_ranking_request` |
| `assemble_answer_package`, `resolve_ranking_assembly_inputs` |
| `app.services.ai` |
| `app.services.semantic` |
| `app.services.vector` |
| `CitationAssembler` / `app.services.citation.assembler` |
| `fastapi`, `APIRouter`, `app.api` |
| `celery`, `redis`, `rabbitmq`, `kafka` |

### Allowed imports

| Permitted | Usage |
|-----------|--------|
| `app.services.answer_persistence.get_answer_request` | Request validation (F-5) |
| `app.services.answer_persistence.get_answer_result` | Result pin (F-5) |
| `app.services.answer_persistence.list_results_for_request` | Sibling resolution |
| `app.services.answer_persistence.list_evidence_entries_for_result` | Evidence load |
| `app.services.answer_persistence.list_uncertainty_flags_for_result` | Uncertainty load |
| `app.services.citation.formatter.CitationFormatter` | Read-only display |
| `app.models.retrieval_evidence_reference` (or repository read helper) | Provenance join reads in `rendering.py` only |
| `app.models.citation` / citation read helpers | Formatter input resolution |
| `sqlalchemy.orm.Session` | DB session |
| `uuid`, `dataclasses` | Types / DTOs |

**Test guard:** `test_response_runtime_import_guards` — static scan of all `response_runtime/*.py`.

---

## D-R-07 — Runtime behaviour

| Rule | Verdict |
|------|---------|
| Read-only | **REQUIRED** — no INSERT/UPDATE/DELETE |
| Deterministic rendering | **REQUIRED** — G-11 |
| No mutations | **REQUIRED** |
| No writes | **REQUIRED** |
| No retries | **REQUIRED** in v1 |
| No orchestration | **REQUIRED** — no worker/persistence calls |
| No persistence | **REQUIRED** |
| No queue | **REQUIRED** |
| No worker | **REQUIRED** |
| No session.commit() in runtime | **REQUIRED** — read-only consumer |

---

## D-R-08 — Error mapping (frozen)

### Runtime vocabulary (exact — no persistence reuse)

| Category | When |
|----------|------|
| `invalid_response_request` | Envelope validation failure |
| `contract_version_unsupported` | Unknown `contract_version` |
| `answer_request_not_found` | Missing `answer_requests` row |
| `answer_result_not_found` | Pinned result missing or mismatched |
| `answer_not_completed` | No terminal `completed` result |
| `answer_not_deliverable` | Terminal `failed` / `duplicate_rejected` / `skipped` |
| `accepted_result_missing` | No accepted sibling for children |
| `evidence_count_mismatch` | Children count ≠ `rank_count` |
| `provenance_resolution_failed` | Join chain incomplete |
| `citation_format_failed` | Formatter error when flag enabled |
| `response_pipeline_unavailable` | Unexpected internal failure |

### Persistence terminal → runtime (locked)

| Persistence `answer_status` | `response_status` | `error_category` |
|----------------------------|-------------------|------------------|
| `completed` | `completed` | `None` |
| `failed` | `failed` | `answer_not_deliverable` |
| `duplicate_rejected` | `failed` | `answer_not_deliverable` |
| `skipped` | `failed` | `answer_not_deliverable` |
| in-flight (`accepted` only) | — | `answer_not_completed` |

**Do not expose** `duplicate_answer`, `assembly_validation_failed`, `permutation_mismatch`, or other persistence/worker/ranking categories on `ResponseOutcome`.

---

## D-R-09 — Determinism (frozen)

```text
same terminal completed answer_result_id
  × same ResponseRequest (contract_version + include_rendered_citation_text + answer_result_id pin)
  = identical ResponsePackage (field-wise, including evidence order and provenance fields)
```

| Requirement | Rule |
|-------------|------|
| Randomness | **PROHIBITED** |
| Timestamps in `ResponsePackage` | **PROHIBITED** |
| Non-deterministic ordering | **PROHIBITED** |
| Model-generated text | **PROHIBITED** |
| Inference on `legal_object_id` / `source_version_id` | **PROHIBITED** — pass-through only |

---

## D-R-10 — Explicit non-goals

| Prohibited capability | |
|-----------------------|--|
| Retrieval execution | |
| Ranking execution | |
| Answer assembly | |
| Answer persistence writes | |
| Worker execution | |
| `CitationAssembler` | |
| Citation discovery | |
| Citation mutation | |
| AI | |
| LLMs | |
| Semantic search | |
| Vector search | |
| FastAPI | |
| HTTP routes | |
| REST APIs | |
| Queue systems | |
| Celery | |
| Redis | |
| RabbitMQ | |
| Kafka | |
| Narrative answer generation | |
| `answer_text` generation | |
| Legal conclusions | |
| Recommendations | |
| Concurrent workers | |
| Response caching | |
| Streaming responses | |
| Pagination | |
| Localization | |

---

## D-R-11 — Implementation test plan (design only)

**Planned module:** `backend/tests/test_response_runtime_skeleton.py`

| Group | Tests |
|-------|-------|
| **Delegation** | `build_response` uses read APIs only — no `create_*` / `persist_*` / workers |
| **No assembly** | `assemble_answer_package` never called from runtime package |
| **DTO schemas** | Frozen field sets including `legal_object_id` + `source_version_id` on `ResponseEvidenceEntry` |
| **Terminal resolution** | Latest `completed` selected when `answer_result_id` omitted |
| **Accepted sibling** | Evidence/uncertainty loaded from `accepted` row only |
| **OQ-R-09 / F-1** | `legal_object_id` / `source_version_id` pass-through from retrieval evidence join; `null` when unresolved |
| **Determinism** | Same inputs → identical `ResponsePackage` (no timestamp fields) |
| **Order** | Evidence order matches `presentation_order_index`; no re-sort |
| **CitationFormatter gate** | Formatter called only when `include_rendered_citation_text=true` |
| **Error mapping** | Persistence `failed` → `answer_not_deliverable`; no persistence category leakage |
| **Import guards** | Prohibited prefixes absent |
| **No API/queue** | No FastAPI / broker imports |
| **End-to-end** | Worker-completed answer → `build_response` → `response_status=completed` |
| **Zero-evidence** | `rank_count=0` → empty evidence; `zero_evidence` flag preserved |
| **Validation** | Unsupported `contract_version` rejected before render |
| **F-5** | Uses existing `get_answer_request` / `get_answer_result` — no new persistence APIs required |

**Integration tests require `TEST_DATABASE_URL`.**

---

## D-R-12 — Implementation scope

### TASK-010A may build (when explicitly authorized)

| Artifact | Scope |
|----------|--------|
| `backend/app/services/response_runtime/models.py` | §D-R-03 DTOs |
| `backend/app/services/response_runtime/runtime.py` | §D-R-03 entry + resolution |
| `backend/app/services/response_runtime/rendering.py` | §D-R-02 rendering + provenance reads |
| `backend/app/services/response_runtime/__init__.py` | Public exports |
| `backend/tests/test_response_runtime_skeleton.py` | §D-R-11 |

### TASK-010A must NOT build

| Prohibited | |
|------------|--|
| Migrations / ORM models | |
| Changes to `answer_persistence`, `answer_assembly`, or `answer_runtime` | |
| Public HTTP APIs / FastAPI routes | |
| Workers / queue infrastructure | |
| AI / semantic / vector | |
| `CitationAssembler` | |
| `answer_text`, legal conclusions, recommendations | |
| Answer Persistence amendments (F-5 — not required) | |

### Upstream preservation

- Answer persistence read APIs unchanged (DEC-016)
- Answer worker (009C) unchanged
- `assemble_answer_package` remains outside runtime scope (DEC-014)

---

## Authorization checklist (for future acceptance prompt)

- [ ] Architect accepts §D-R-01–§D-R-12
- [ ] Claude review of this package (recommended)
- [ ] Explicit prompt: **AUTHORIZED FOR LIMITED IMPLEMENTATION**
- [ ] Scope: `response_runtime/` + `test_response_runtime_skeleton.py` only
- [ ] OQ-R-09 / F-1 Option A accepted
- [ ] F-5 read dependencies verified

---

## Unresolved questions

| ID | Question | Disposition |
|----|----------|-------------|
| U-R-01 | `ResponseRuntimeError` vs failed `ResponseOutcome` on validation? | **Recommend raise** `ResponseRuntimeError` for pre-resolution validation; map persistence terminals to `ResponseOutcome` |
| U-R-02 | Include `legal_object_version_id` on `ResponseEvidenceEntry`? | **Defer** — OQ-R-09 locked `legal_object_id` + `source_version_id` only |
| U-R-03 | Unit tests without DB for validation/import guards? | **Recommend yes** — mirror `test_answer_worker_skeleton.py` |
| U-R-04 | `include_failed=true` audit delivery (OQ-R-10)? | **Defer** — not in 010A-v1 |
| OQ-R-01–OQ-R-08, OQ-R-10 | See contract | **Defer** — unchanged from PREAUTH |
| **OQ-R-09** | Provenance IDs on delivery DTO | **CLOSED** — Option A locked (DEC-020) |

---

## Explicit prohibitions (this task)

- No runtime code, APIs, workers, migrations, ORM, services, or tests in this task

---

END OF TASK-010A IMPLEMENTATION AUTHORIZATION PACKAGE
