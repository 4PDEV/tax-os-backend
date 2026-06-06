# Retrieval Runtime Contract

## Purpose

Define governed boundaries for **evidence retrieval** from canonical legal memory and persisted citations.

This contract is **governance only**. It authorizes the retrieval runtime **design envelope** for downstream tasks. It does **not** authorize persistence implementation (007C), workers (007D), ranking, answers, or AI retrieval.

## Core principle

**Retrieval returns evidence references — not legal conclusions.**

```text
query → retrieval request → evidence references → retrieval result
```

Retrieval is **not**:

- answer generation
- legal interpretation
- tax advice
- applicability determination
- relevance ranking
- synthesis or recommendations

## Mandatory doctrines

| Doctrine | Rule |
|----------|------|
| `parsed_structure` ≠ legal object | Retrieval reads canonical legal memory only |
| `legal_object` ≠ legal meaning | References only — no interpretation |
| `legal_object` ≠ citation | Citations are separate persisted evidence |
| `citation` ≠ retrieval result | Retrieval may reference citations; it does not create them |
| `retrieval result` ≠ answer | Evidence set supports future governed answer assembly |
| `retrieval result` ≠ legal conclusion | No obligation or consequence inference |

## Retrieval role

Retrieval runtime is responsible for:

- accepting governed retrieval requests with explicit temporal mode
- locating evidence (`legal_object_version` pins, `citation_id` / `citation_hash` references)
- returning provenance-complete reference sets
- recording append-only request/result lifecycle (future 007C)
- enforcing idempotency on `request_hash`
- preserving deterministic ordering (not relevance ranking)

Retrieval runtime must **not**:

- generate answers, advice, or legal conclusions
- rank by relevance, confidence, or semantic similarity
- infer applicability or legal force
- create or re-assemble citations
- invoke AI/LLMs or semantic/vector search
- silently select “latest” or “current” law

## Evidence chain (canonical)

```text
source_version
  → extracted_text
  → parsed_structure
  → legal_object
  → legal_object_version
  → citation
```

Retrieval may return references at `legal_object_version` and `citation` layers. It must not bypass provenance.

---

## Temporal doctrine (R-01)

Every runtime request must specify **`retrieval_mode`**. Silent defaults are **prohibited**.

| Mode | Required inputs | Behavior |
|------|-----------------|----------|
| **`AS_OF_DATE`** | `as_of_date` | Versions effective on date (recommended default) |
| **`EXACT_VERSION`** | `legal_object_version_id` | Pin one version row |
| **`LATEST_VERSION`** | explicit mode only | Use `current_version_id` pointer — **never silent** |

### Rules

1. `effective_on=None` / missing `as_of_date` when mode requires it → **reject** request.
2. `LATEST_VERSION` allowed only when `retrieval_mode=LATEST_VERSION` is explicit.
3. Source-version dates are metadata only — never substitute for legal-object applicability (TASK-004E / Addendum V6).
4. Runtime wrapper around TASK-004A must enforce mode; 004A service on `main` unchanged until separate bounded task.

---

## Version pinning (R-02)

Every evidence item in a retrieval result must carry:

| Field | Required |
|-------|----------|
| `legal_object_id` | Yes |
| `legal_object_version_id` | Yes |
| `source_version_id` | Yes |

**Retrieval without `legal_object_version_id` is prohibited.**

No version inference from `legal_object_id` alone.

---

## Evidence boundary (R-03)

### Default output (reference-only)

| Field | Default |
|-------|---------|
| `citation_id` | Included when citation exists |
| `citation_hash` | Optional canonical identity |
| `legal_object_id` | Yes |
| `legal_object_version_id` | Yes |
| `source_version_id` | Yes |
| `source_document_id` | Yes |
| `location_reference` / `object_identifier` | When available |
| Provenance metadata | Yes |

### Prohibited default output

- answer text
- legal conclusions
- interpretations
- recommendations
- applicability flags
- relevance or confidence scores

### Optional content (explicit opt-in only)

| Flag | Payload |
|------|---------|
| `include_canonical_text` | Legal-object body from version — labeled evidence, not answer |
| `include_rendered_citation_text` | Stored text from `citations` entity — read-only, not re-rendered |

Default path: **references + provenance only**.

---

## Citation evidence path (R-05)

Retrieval evidence must **reference citations** where available. Legal-object references alone are insufficient for governed downstream answer assembly.

### Lookup (read-only)

- By `citation_id` or `citation_hash` on `citations` table (TASK-006AD)
- By `legal_object_version_id` + scope filters

### Required provenance chain

```text
citation_id / citation_hash
  → legal_object_version_id
  → legal_object_id
  → source_version_id
  → source_document_id
```

### Prohibited

- `CitationAssembler` invocation during retrieval
- New citation creation during retrieval
- Applicability inference from citation presence

---

## Deterministic ordering (R-06)

All selection and ordering must be **explicit**.

Permitted: `ORDER BY effective_from`, structural identifiers, `created_at`, `legal_object_id`, `citation_hash` (declared sort keys).

**Required:** apply deterministic `ORDER BY` before any `.first()` or `LIMIT 1`.

Prohibited: implicit database order, relevance scores, “top result” semantics.

```text
ordering ≠ ranking
```

---

## Persistence doctrine (R-04 — future TASK-007C)

Append-only lifecycle tables (planned):

### `retrieval_requests`

- `retrieval_request_id`, `request_hash`, `retrieval_mode`, `as_of_date`, actor fields, `force_replay`, `requested_at`, scope envelope

### `retrieval_results`

- `retrieval_result_id`, `retrieval_request_id`, `retrieval_status`, `result_count`, `completed_at`, error metadata

Evidence reference list on result — references only, not answer payloads.

### `request_hash`

```text
request_hash = SHA-256(normalized_retrieval_envelope)
```

Lifecycle identity only — **not** raw query text, not evidence identity.

`force_replay` is governance audit bypass only — does not bypass provenance or temporal validation.

**007C not authorized by this contract alone.**

---

## RetrievalRequest contract (future implementation)

Required fields:

- `retrieval_request_id`
- `retrieval_mode` — `AS_OF_DATE` | `EXACT_VERSION` | `LATEST_VERSION`
- `as_of_date` (when mode = `AS_OF_DATE`)
- `legal_object_version_id` (when mode = `EXACT_VERSION`)
- `jurisdiction_code`
- `tax_type_code` (nullable)
- scope filters (document, source_version, object_type, object_identifier)
- `requested_by_actor_type`
- `requested_by_actor_identifier` (nullable)
- `requested_at`
- `force_replay`
- `include_canonical_text` (default false)
- `include_rendered_citation_text` (default false)
- `notes` (nullable)

Optional audit field: `query_text` — **not** part of `request_hash`.

---

## RetrievalResult contract (future implementation)

Lifecycle fields:

- `retrieval_result_id`
- `retrieval_request_id`
- `retrieval_status` — `pending` | `accepted` | `completed` | `failed` | `skipped` | `duplicate_rejected`
- `result_count`
- `completed_at`
- `error_category`, `error_message`
- `notes`

Evidence payload: list of **EvidenceReference** items (version pins + citation references + provenance).

**Prohibited on result:** answer text, rankings, scores, interpretations.

---

## Relationship to TASK-004A

[`backend/app/services/retrieval/LEGAL_OBJECT_RETRIEVAL_CONTRACT.md`](backend/app/services/retrieval/LEGAL_OBJECT_RETRIEVAL_CONTRACT.md) defines deterministic **legal-object query** service on `main`.

This contract governs **retrieval runtime orchestration** above 004A:

- enforces temporal modes and evidence envelope
- adds citation reference layer
- defines persistence and worker lifecycle (007C / 007D)

Future implementations must wrap — not silently replace — 004A behavior.

---

## OD-021 (concurrency)

- **Single-worker** retrieval orchestration acceptable initially
- **Concurrent retrieval workers not authorized**
- Future: `request_hash`-keyed advisory/row locks when concurrency gate opens

---

## Governed pipeline

```text
TASK-007B  This contract (governance)
  → TASK-007C  Persistence (not authorized)
  → TASK-007D  Worker / execution (not authorized)
  → Retrieval Layer Review (future)
```

---

## Prohibited capabilities

| Capability | Status |
|------------|--------|
| Ranking / relevance scoring | **NOT AUTHORIZED** |
| Answer runtime | **NOT AUTHORIZED** |
| AI / LLM / semantic search | **NOT AUTHORIZED** |
| Concurrent retrieval workers | **NOT AUTHORIZED** |
| Citation creation / re-assembly | **NOT AUTHORIZED** |
| Legal interpretation | **NOT AUTHORIZED** |

---

## References

- [`RETRIEVAL_RUNTIME_REMEDIATION_007A1.md`](RETRIEVAL_RUNTIME_REMEDIATION_007A1.md)
- [`RETRIEVAL_RUNTIME_007A1_ACCEPTANCE_REVIEW.md`](RETRIEVAL_RUNTIME_007A1_ACCEPTANCE_REVIEW.md)
- [`ARCHITECTURE_REVIEW_RETRIEVAL_RUNTIME_007A-PREAUTH.md`](ARCHITECTURE_REVIEW_RETRIEVAL_RUNTIME_007A-PREAUTH.md)
- [`TEMPORAL_VERSIONING_ARCHITECTURE.md`](TEMPORAL_VERSIONING_ARCHITECTURE.md)
- [`CLAUDE_REVIEW_CITATION_PIPELINE_006Y-006AD.md`](CLAUDE_REVIEW_CITATION_PIPELINE_006Y-006AD.md)

---

END OF RETRIEVAL RUNTIME CONTRACT (TASK-007B)
