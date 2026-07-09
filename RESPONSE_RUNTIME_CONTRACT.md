# Response Runtime Contract

## Purpose

Define governed boundaries for the **response runtime** — the first user-facing delivery layer that reads completed answer persistence and renders a deterministic response package for downstream callers.

This contract is **governance only** (TASK-010A-PREAUTH). It authorizes the response runtime **design envelope** for downstream bounded implementation. It does **not** authorize runtime services, workers, migrations, ORM models, persistence writes, public HTTP APIs, tests, or narrative answer generation.

## Core principle

**Response runtime delivers persisted answers — it does not retrieve, rank, assemble, persist, invoke workers, or conclude legal force.**

```text
ResponseRequest (delivery envelope)
  → validate_request
  → resolve terminal completed answer_result (read-only)
  → load accepted answer_result children (evidence + uncertainty)
  → resolve provenance for display (read-only joins)
  → render deterministic ResponsePackage
  → ResponseOutcome
```

Response runtime is **not**:

- retrieval execution or evidence selection (007E)
- ranking execution or permutation (008D)
- answer assembly (009A) — package already materialized at persistence
- answer persistence writes (009B) — read-only consumer
- answer worker orchestration (009C)
- citation creation or `CitationAssembler` invocation
- semantic / vector search or AI answer generation
- public HTTP transport (future API layer)

## Mandatory doctrines

| Doctrine | Rule |
|----------|------|
| **Provenance lives once** (DEC-010) | Runtime reads pointers; does not duplicate authoritative pins |
| **Answer ≠ legal conclusion** (DEC-013) | No applicability, legal force, or recommendations in payload |
| **Persistence envelope** (DEC-016) | Runtime consumes `completed` terminal results only — no re-orchestration |
| **Worker boundary** (DEC-017/018) | Runtime does not invoke `run_answer_worker` or `persist_answer_for_ranking_request` |
| **Deterministic-first** (G-11) | Same persisted answer + same rendering options → identical `ResponsePackage` |
| **Read-only delivery** | No `create_*`, no workers, no queues |

Upstream contracts (binding, closed):

- [`ANSWER_WORKER_CONTRACT.md`](ANSWER_WORKER_CONTRACT.md) (009C-v1)
- [`ANSWER_PERSISTENCE_CONTRACT.md`](ANSWER_PERSISTENCE_CONTRACT.md) (009B-v1)
- [`ANSWER_ASSEMBLY_CONTRACT.md`](ANSWER_ASSEMBLY_CONTRACT.md) (009A-v1)
- [`TASKS/ANSWER-LAYER-REVIEW.md`](TASKS/ANSWER-LAYER-REVIEW.md)
- [`TASKS/ANSWER-PERSISTENCE-REVIEW.md`](TASKS/ANSWER-PERSISTENCE-REVIEW.md)
- [`TASKS/TASK-009C-ANSWER-WORKER.md`](TASKS/TASK-009C-ANSWER-WORKER.md)
- [`DECISION_LOG.md`](DECISION_LOG.md) — DEC-010 through DEC-018, DEC-019, DEC-020, OD-021

---

## G-01 — Response runtime boundary

### Allowed

| Capability | Mechanism |
|------------|-----------|
| Validate delivery envelope | `ResponseRuntime.validate_request()` |
| Resolve persisted answer lifecycle | Read `answer_results` for `answer_request_id` |
| Load pure-pointer evidence membership | Read `answer_evidence_entries` on **accepted** `answer_result` |
| Load uncertainty metadata | Read `answer_uncertainty_flags` on **accepted** `answer_result` |
| Resolve display provenance (read-only) | Join via persisted `retrieval_evidence_reference_id` / `ranked_evidence_reference_id` |
| Format citation display text | Read-only `CitationFormatter` when `include_rendered_citation_text=true` |
| Render deterministic DTO | `ResponsePackage` (§G-04) |
| Return delivery outcome | `ResponseOutcome` |

### Prohibited

| Capability | Reason |
|------------|--------|
| Retrieval execution / persistence writes | Layer boundary |
| Ranking execution / persistence writes | Layer boundary |
| `assemble_answer_package` | DEC-014 — assembly closed at 009A |
| `persist_answer_for_ranking_request` / all `create_answer_*` | DEC-016 — persistence write boundary |
| `run_answer_worker` / worker packages | DEC-017/018 |
| `CitationAssembler` | Citation creation / mutation prohibited |
| AI / semantic / vector reasoning | Not authorized |
| Narrative `answer_text`, legal conclusions, recommendations | Answer ≠ legal conclusion |
| FastAPI routes / HTTP handlers | Future API layer |
| Queue brokers / background workers | Not authorized |
| Re-sorting, filtering, deduplication of evidence | G-06 deterministic order |
| Persisting rendered output | Delivery is ephemeral |

---

## G-02 — Entry point (frozen design)

### Package (locked for future implementation)

```text
backend/app/services/response_runtime/
```

| Module | Responsibility (future) |
|--------|-------------------------|
| `models.py` | `ResponseRequest`, `ResponsePackage`, `ResponseOutcome`, `ResponseRuntimeError` |
| `runtime.py` | `ResponseRuntime`, `build_response` |
| `rendering.py` | Deterministic field mapping + `CitationFormatter` gate |
| `__init__.py` | Public exports |

**No implementation in TASK-010A-PREAUTH.**

### Entry point (locked)

```python
def build_response(
    db: Session,
    request: ResponseRequest,
) -> ResponseOutcome:
    """Single delivery entrypoint for response runtime."""
    ...
```

Optional helper (future, `runtime.py` only):

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

## G-03 — Inputs

### `ResponseRequest` (frozen)

| Field | Type | Default | Required | Validation |
|-------|------|---------|----------|------------|
| `answer_request_id` | UUID | — | YES | Must be `UUID` instance |
| `contract_version` | str | `010A-v1` | YES | Non-empty; supported version only |
| `include_rendered_citation_text` | bool | `false` | NO | When `true`, invoke read-only `CitationFormatter` |
| `answer_result_id` | UUID \| None | `None` | NO | When set, pin specific terminal `answer_result`; must belong to `answer_request_id` |

### Resolution rule (locked)

When `answer_result_id` is **omitted**:

1. Load all `answer_results` for `answer_request_id` (read-only `list_results_for_request` or equivalent).
2. Select the **latest terminal** row where `answer_status = completed` (by `created_at` desc).
3. If none exists → runtime error `answer_not_completed` (§G-08).

When `answer_result_id` is **provided**:

1. Verify row exists and `answer_request_id` matches envelope.
2. Require `answer_status = completed` for successful delivery.
3. If terminal `failed` / `duplicate_rejected` / `skipped` → map per §G-08 (no silent success).

### Immutable identifiers (locked)

| Identifier | Role |
|------------|------|
| `answer_request_id` | Primary delivery anchor — persisted intent row |
| `answer_result_id` | Optional pin to specific terminal completed result |
| `contract_version` | Response schema generation — `010A-v1` |

**Not accepted as runtime inputs:** `ranking_request_id`, `retrieval_result_id`, `ranking_profile`, replay nonces — those are upstream orchestration concerns.

---

## G-04 — Outputs

### `ResponseOutcome` (frozen envelope)

| Field | Type | Notes |
|-------|------|-------|
| `response_status` | str | `completed` \| `failed` |
| `response_package` | `ResponsePackage` \| None | Present when `response_status=completed` |
| `error_category` | str \| None | Runtime vocabulary only (§G-08) |
| `error_message` | str \| None | Human-readable; not legal advice |

**No persistence metadata leakage:** outcome must not expose ORM instances, internal lifecycle rows (`accepted`), worker fields, hash columns, or `requested_by_actor_*` audit fields unless explicitly added in a future amendment.

### `ResponsePackage` (frozen delivery schema)

```text
ResponsePackage
├── contract_version           string — "010A-v1"
├── answer_request_id          UUID — delivery anchor (caller reference)
├── answer_result_id           UUID — terminal completed result rendered
├── rank_count                 int — from terminal completed result
├── evidence_entries           ordered list[ResponseEvidenceEntry]
├── uncertainty_flags          list[ResponseUncertaintyFlag]
└── response_metadata          ResponseMetadata | null — non-authoritative display block only
```

**Explicitly excluded from `ResponsePackage`:**

- `answer_status` lifecycle values (`accepted`, `duplicate_rejected`, …)
- `accepted_ranking_result_id`, `terminal_ranking_result_id`
- `answer_request_hash`, `force_replay`, `replay_nonce`
- `assembled_at`, `created_at`, `updated_at` (no timestamps in payload identity — G-11)
- `error_category` on success path
- Narrative `answer_text`, `legal_conclusion`, `recommendation_text`

### `ResponseEvidenceEntry`

```text
ResponseEvidenceEntry
├── presentation_order_index   int — copied from persisted entry; no re-sort
├── retrieval_evidence_reference_id UUID — provenance anchor for caller traceability
├── ranked_evidence_reference_id UUID — persisted pointer reference
├── legal_object_id            string | null — read-only provenance reference (OQ-R-09 / DEC-020)
├── source_version_id          UUID | null — read-only provenance reference (OQ-R-09 / DEC-020)
├── object_identifier          string | null — read from retrieval evidence join
├── location_reference         string | null — read from retrieval evidence join
├── citation_reference         ResponseCitationReference | null
└── entry_metadata             dict | null — non-authoritative display hints only
```

**OQ-R-09 / F-1 (locked — Option A):** `legal_object_id` and `source_version_id` are **read-only provenance references** resolved via `retrieval_evidence_references` join. They are **not authoritative**, **never interpreted**, **never inferred**, and **display/pass-through only**. When join does not resolve, field is `null` — runtime must not fabricate values.

### `ResponseCitationReference`

```text
ResponseCitationReference
├── citation_id                string | null
├── citation_hash              string | null
└── rendered_citation_text     string | null — present only when requested; not authoritative
```

### `ResponseUncertaintyFlag`

```text
ResponseUncertaintyFlag
├── flag_type                  enum — conflict | ambiguity | incomplete_provenance | zero_evidence | other
├── severity                   enum — informational | warning | error
├── message                    string
└── related_evidence_ids       list[UUID] — retrieval_evidence_reference_id values
```

### `ResponseMetadata`

```text
ResponseMetadata
├── rendering_mode             enum — deterministic (only mode in 010A-v1)
├── include_rendered_citation_text bool
└── notes                      string | null
```

---

## G-05 — Read model

### Permitted reads (locked)

| Store | Usage |
|-------|--------|
| `answer_results` | Resolve terminal `completed` (or explicit pin); read `rank_count` |
| `answer_evidence_entries` | Load membership from **accepted** sibling result |
| `answer_uncertainty_flags` | Load flags from **accepted** sibling result |
| `retrieval_evidence_references` | Read-only provenance resolution for display fields |
| `ranked_evidence_references` | Validate pointer integrity when needed |
| `citations` | Read-only input to `CitationFormatter` |
| `legal_object` / `legal_object_version` / `source_version` | Read-only display joins when required by formatter |

### Permitted read APIs (future implementation)

| API | Usage |
|-----|--------|
| `get_answer_request` | Validate request exists |
| `get_answer_result` | Pin / validate terminal result |
| `list_results_for_request` | Locate accepted + terminal completed siblings |
| `list_evidence_entries_for_result` | Evidence membership |
| `list_uncertainty_flags_for_result` | Uncertainty membership |

### Prohibited reads / calls

| API / store | Reason |
|-------------|--------|
| `retrieval_execution` | Layer boundary |
| `ranking_execution` | Layer boundary |
| `assemble_answer_package` | Assembly boundary |
| All `create_answer_*` | Persistence write boundary |
| `persist_answer_for_ranking_request` | Worker/persistence orchestration |
| `run_answer_worker` | Worker boundary |
| `CitationAssembler` | Mutation / discovery prohibited |

### Accepted-row attachment (RL-O-01 carry-forward)

Evidence and uncertainty children attach to the **`accepted`** `answer_result` row. Terminal `completed` row supplies `rank_count` and delivery eligibility. Runtime **must not** load evidence from the terminal row if children are on accepted sibling.

### Justified joins beyond answer tables

Joins through `retrieval_evidence_reference_id` to retrieval provenance and citation tables are **permitted read-only display resolution** — not retrieval execution. No new evidence selection, filtering, or scope expansion.

---

## G-06 — Rendering rules

| Rule | Requirement |
|------|-------------|
| Evidence order | Strictly `presentation_order_index ASC` as persisted |
| Sorting | **PROHIBITED** — no alternate order keys |
| Filtering | **PROHIBITED** — no omission of persisted entries |
| Deduplication | **PROHIBITED** |
| Inference | **PROHIBITED** — no relevance, applicability, or legal-force derivation |
| Zero-evidence | Return empty `evidence_entries`; preserve `zero_evidence` uncertainty flag |
| Count integrity | `len(evidence_entries)` must equal `rank_count` when `rank_count > 0` |

---

## G-07 — Citation rules

| Component | Verdict |
|-----------|---------|
| `CitationFormatter` | **PERMITTED** — read-only display formatting when `include_rendered_citation_text=true` |
| `CitationAssembler` | **PROHIBITED** |
| Citation discovery | **PROHIBITED** — format only rows resolvable from persisted pins |
| Citation reconstruction | **PROHIBITED** |
| Citation mutation | **PROHIBITED** |
| Persisted `rendered_citation_text` on answer rows | **PROHIBITED** (DEC-010 / OQ-03 carry-forward) |

**Formatter gate (locked):**

```text
if include_rendered_citation_text and citation_id resolves:
    rendered_citation_text = CitationFormatter.format(existing_citation_row)  # read-only
else:
    rendered_citation_text = None
```

---

## G-08 — Error model

### Runtime-specific categories (locked vocabulary)

| Category | Meaning |
|----------|---------|
| `invalid_response_request` | Envelope validation failure |
| `contract_version_unsupported` | Unknown `contract_version` |
| `answer_request_not_found` | No `answer_requests` row |
| `answer_result_not_found` | Pinned `answer_result_id` missing or mismatched |
| `answer_not_completed` | No terminal `completed` result available |
| `answer_not_deliverable` | Terminal `failed`, `duplicate_rejected`, or `skipped` |
| `accepted_result_missing` | Accepted sibling missing for evidence load |
| `evidence_count_mismatch` | Persisted children count ≠ `rank_count` |
| `provenance_resolution_failed` | Read-only join chain incomplete |
| `citation_format_failed` | Formatter failure when flag enabled |
| `response_pipeline_unavailable` | Unexpected internal failure |

### Prohibited runtime categories (reuse blocked)

Do **not** surface persistence/worker/ranking categories directly as delivery errors:

`duplicate_answer`, `permutation_mismatch`, `duplicate_ranking`, `ranking_request_missing`, `assembly_validation_failed`, …

Map to runtime vocabulary at the boundary.

### Persistence terminal → runtime mapping

| Persistence terminal `answer_status` | `response_status` | `error_category` |
|--------------------------------------|-------------------|------------------|
| `completed` | `completed` | `None` |
| `failed` | `failed` | `answer_not_deliverable` |
| `duplicate_rejected` | `failed` | `answer_not_deliverable` |
| `skipped` | `failed` | `answer_not_deliverable` |
| in-flight (`accepted` only) | — | raise `answer_not_completed` |

---

## G-09 — Import guards

### Prohibited imports in `response_runtime/` (frozen)

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

### Allowed imports (frozen)

| Permitted | Usage |
|-----------|--------|
| `app.services.answer_persistence.get_answer_request` | Request validation |
| `app.services.answer_persistence.get_answer_result` | Result pin |
| `app.services.answer_persistence.list_results_for_request` | Sibling resolution |
| `app.services.answer_persistence.list_evidence_entries_for_result` | Evidence load |
| `app.services.answer_persistence.list_uncertainty_flags_for_result` | Uncertainty load |
| `app.services.citation.formatter.CitationFormatter` | Read-only display |
| `sqlalchemy.orm.Session` | DB session |
| `uuid`, `dataclasses` | Types / DTOs |

---

## G-10 — Layer separation

```text
Retrieval
  ↓
Ranking
  ↓
Answer Assembly (009A — ephemeral / inside 009B orchestration)
  ↓
Answer Persistence (009B)
  ↓
Answer Worker (009C)
  ↓
Response Runtime (010A — read + render only)
  ↓
Future API layer (HTTP transport — NOT AUTHORIZED)
```

| Layer | Owns |
|-------|------|
| Retrieval | Evidence selection |
| Ranking | Presentation order permutation |
| Answer assembly | Governed package construction |
| Answer persistence | Append-only lifecycle + pure-pointer children |
| Answer worker | Single-worker persistence orchestration |
| **Response runtime** | **Deterministic delivery DTO from completed persistence** |
| Future API | Transport, auth, versioning negotiation at HTTP boundary |

**Rule:** `answer worker` ≠ `response runtime` ≠ `public API`. Worker persists; runtime renders; API transports.

---

## G-11 — Determinism

```text
same terminal completed answer_result
  × same ResponseRequest rendering options
  = identical ResponsePackage (field-wise)
```

| Requirement | Rule |
|-------------|------|
| Randomness | **PROHIBITED** |
| Timestamps in payload identity | **PROHIBITED** on `ResponsePackage` |
| Non-deterministic ordering | **PROHIBITED** |
| Model-generated text | **PROHIBITED** in 010A-v1 |

---

## G-12 — Readiness checklist

### Completed prerequisites (TASK-010A-PREAUTH)

| ID | Criterion | Status |
|----|-----------|--------|
| R-01 | Answer assembly accepted (009A) | **MET** |
| R-02 | Answer persistence accepted (009B) | **MET** |
| R-03 | Answer worker accepted (009C) | **MET** |
| R-04 | DEC-010 through DEC-018 locked | **MET** |
| R-05 | Response runtime contract (this document) | **MET** |
| R-06 | DEC-019 locked | **MET** (this pre-auth) |

### Future implementation prerequisites (NOT MET)

| ID | Criterion |
|----|-----------|
| I-01 | Claude review of TASK-010A-PREAUTH |
| I-02 | TASK-010A-IMPL-AUTH design package |
| I-03 | Explicit **AUTHORIZED FOR LIMITED IMPLEMENTATION** prompt |
| I-04 | `TEST_DATABASE_URL` integration test discipline |

### Future review gate

```text
TASK-010A-PREAUTH (this document)
  → Claude review
  → TASK-010A-IMPL-AUTH
  → explicit implementation authorization
  → bounded response_runtime/ skeleton + tests
```

**TASK-010A implementation:** **ACCEPTED WITH FINDINGS** — delivered at `v0.2.4-response-runtime`.

---

## Open questions

| ID | Question | Recommendation |
|----|----------|----------------|
| OQ-R-01 | Authorize narrative `answer_text` in response runtime? | **Defer** — not in 010A-v1; requires separate governance gate |
| OQ-R-02 | Localization / multilingual rendering | **Defer** — document `contract_version` negotiation at API layer |
| OQ-R-03 | Jurisdiction-specific rendering rules | **Defer** — pass-through display only; no inference in runtime |
| OQ-R-04 | API ownership vs runtime ownership | **Split** — runtime owns `ResponsePackage`; API owns HTTP schema/transport |
| OQ-R-05 | Pagination for large evidence sets | **Defer** — v1 returns full ordered list; pagination is API concern |
| OQ-R-06 | Streaming responses | **Defer** — not authorized in 010A-v1 |
| OQ-R-07 | Response caching | **Defer** — no cache layer in first slice; API/CDN is future scope |
| OQ-R-08 | Version negotiation (`010A-v2`, API semver) | **Document** — runtime validates `contract_version`; HTTP negotiation future |
| OQ-R-09 | Include `legal_object_id` / `source_version_id` in delivery DTO? | **CLOSED** — **Option A locked** (DEC-020): include as read-only provenance references on `ResponseEvidenceEntry`; display/pass-through only |
| OQ-R-10 | Deliver `failed` persistence packages for audit UI? | **Recommend no in v1** — return `answer_not_deliverable`; optional future `include_failed=true` gate |

---

## Architectural risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Runtime re-implements assembly joins | High | Freeze read model + prohibited imports; tests scan for `assemble_answer_package` |
| Persistence metadata leaks to public DTO | Medium | Explicit excluded-field list in §G-04 |
| CitationFormatter drift vs persisted pins | Low | Formatter uses resolved `citations` row only; no Assembler |
| Evidence re-ordering at delivery | High | G-06 — persisted order only |
| API layer bypasses runtime | Medium | Future API task must call `build_response` — no direct table reads at HTTP boundary |
| Large evidence payloads | Medium | OQ-R-05 — defer pagination; monitor at API gate |

---

## Explicit prohibitions (this contract)

- No runtime implementation in TASK-010A-PREAUTH
- No migrations, ORM models, persistence services, workers, queues
- No FastAPI routes or public APIs
- No `CitationAssembler`, AI, semantic, or vector imports
- No narrative `answer_text`, legal conclusions, or recommendations in 010A-v1
- No retrieval, ranking, assembly, or persistence writes

---

END OF RESPONSE RUNTIME CONTRACT
