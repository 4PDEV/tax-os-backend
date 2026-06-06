# Architecture Review — Retrieval Runtime Pre-Authorization (TASK-007A)

**Review type:** Architecture / governance review only — **not** retrieval runtime implementation  
**Date:** 2026-06-02  
**Scope:** Proposed retrieval runtime introduction after citation layer closure (006Y–006AD); upstream TASK-004A legal-object retrieval, TASK-004B effective-date resolver, TASK-005A temporal governance, TASK-006AD citation entity  
**Authority:** [`backend/app/services/retrieval/LEGAL_OBJECT_RETRIEVAL_CONTRACT.md`](backend/app/services/retrieval/LEGAL_OBJECT_RETRIEVAL_CONTRACT.md), [`TEMPORAL_VERSIONING_ARCHITECTURE.md`](TEMPORAL_VERSIONING_ARCHITECTURE.md), [`CLAUDE_REVIEW_CITATION_PIPELINE_006Y-006AD.md`](CLAUDE_REVIEW_CITATION_PIPELINE_006Y-006AD.md)

**Verdict:** **APPROVED WITH REQUIRED REMEDIATION BEFORE TASK-007B**

This review does **not** authorize retrieval runtime implementation, ranking, answers, legal interpretation, or AI integration.

---

## Executive summary

Evidence retrieval is **architecturally viable** as a governed layer that returns **references and metadata** — not answers, legal conclusions, or applicability decisions.

TASK-004A already provides deterministic **legal-object retrieval** (`LegalObjectRetrievalService`). TASK-007B “retrieval runtime” must be scoped as an **orchestration and persistence layer** above 004A that:

- accepts governed retrieval requests (not free-form answer queries),
- returns evidence sets (`legal_object_version` pins, `citation_id` / `citation_hash` references, provenance),
- preserves `retrieval result ≠ answer` and `citation ≠ legal meaning`.

**Blocking gaps** exist between 004A baseline and safe runtime introduction: implicit “latest” version selection, missing `legal_object_version_id` on retrieval results, undefined citation-reference retrieval, and absent runtime identity/persistence doctrine.

Remediation is required in a bounded **TASK-007A1** package before TASK-007B implementation may be authorized.

---

## Current platform context

| Layer | Status |
|-------|--------|
| Extraction (006M–006P1) | **COMPLETE** |
| Parsing (006Q–006T1A) | **COMPLETE** |
| Legal object memory (006U–006X1) | **COMPLETE** |
| Citation layer (006Y–006AD) | **COMPLETE** — review CLOSED |
| Legal-object retrieval service (004A) | **On `main`** — in-memory deterministic service |
| Retrieval runtime (007B) | **NOT AUTHORIZED** |
| Ranking | **NOT AUTHORIZED** |
| Answer runtime | **NOT AUTHORIZED** |

**Evidence chain (canonical):**

```text
source_version → extracted_text → parsed_structure → legal_object → legal_object_version → citation
```

**Proposed runtime boundary:**

```text
User Query → retrieval request → retrieval runtime → evidence set → retrieval result
```

**Permitted outputs:** `legal_object_version` references, `citation_id` / `citation_hash` references, provenance metadata, structural identifiers.  
**Prohibited outputs:** answers, legal conclusions, applicability decisions, relevance scores, recommendations.

---

## Review question responses

### 1. Retrieval identity

| Question | Recommendation |
|----------|----------------|
| Identify requests by `query_text` or `normalized_query_hash`? | **Neither alone.** Use structured `retrieval_request_hash` over normalized request envelope (jurisdiction, tax_type, filters, `as_of_date`, scope pins) — mirror citation `request_hash` / `citation_hash` separation. Optional `query_text` stored as audit metadata only; not identity. |
| Replayable? | **Yes** — append-only request/result rows; default idempotency on request hash; explicit `force_replay` for audit replay (006Z precedent). |
| Persist results? | **Yes** — append-only `retrieval_requests` / `retrieval_results`; results store evidence references, not synthesized answers. |

### 2. Evidence boundary

Retrieval may return:

| Evidence type | Allowed | Notes |
|---------------|---------|-------|
| `legal_object_version_id` pin | **Required** | Must be explicit on every legal-memory hit |
| `citation_id` / `citation_hash` | **Yes** | Reference persisted citations (006AD) |
| Provenance (`source_version_id`, `source_document_id`) | **Yes** | Required lineage |
| Structural identifiers | **Yes** | `object_identifier`, location reference |
| `rendered_citation_text` | **Optional** | Only when joined from `citations` entity; labeled as stored citation text — not retrieval synthesis |
| `canonical_text` (legal object body) | **Governed** | 004A returns today; runtime must treat as **evidence payload** with integrity hashes — never as answer text; consider separate `include_canonical_text` flag defaulting false for runtime API |
| Legal object titles / structure snippets | **Structural only** | Labels/identifiers from legal memory — not interpretive summaries |

**Must remain prohibited:** answer text, legal conclusions, applicability flags, confidence scores, relevance ranking, AI-generated summaries, tax advice.

### 3. Temporal filtering

| Rule | Requirement |
|------|-------------|
| `as_of_date` / `effective_on` | **Required for runtime requests** — no implicit “today” or “latest law” |
| `effective_on is None` in 004A | Uses `current_version_id` — **implicit latest**; **not acceptable** for governed runtime without explicit operator override flag |
| Source-version dates | Metadata only — never substitute for legal-object version applicability (004E doctrine) |
| Legal-object version dates | Filter per 004A clause; NULL bounds = unbounded on that side — ambiguity must be preserved, not inferred |

### 4. Provenance

Required lineage for citation evidence:

```text
citation_id / citation_hash
  → legal_object_version_id
  → legal_object_id
  → source_version_id
  → source_document_id
```

Runtime must not return citation references without resolvable `legal_object_version_id` and `source_version_id` pins.

### 5. Ranking

| Status | Rule |
|--------|------|
| Relevance ranking | **NOT AUTHORIZED** |
| Deterministic sort | **Allowed** — 004A ordering (`effective_from`, `object_identifier`, `created_at`, `legal_object_id`) is **not** relevance ranking |
| Runtime | Must document sort keys; prohibit score-based reordering |

### 6. Retrieval persistence

**Recommended:** append-only persistence (006Z / 006V precedent).

| Entity | Purpose |
|--------|---------|
| `retrieval_requests` | Intent, actor, `request_hash`, `as_of_date`, scope filters, `force_replay` |
| `retrieval_results` | Lifecycle status, evidence reference list (JSON or child table), error metadata |

Results must **not** store answer text, rankings, or interpretive fields.

### 7. OD-021

Single-worker assumption acceptable for initial runtime. Concurrent retrieval workers require execution-time locks keyed by `request_hash` or evidence-set mutation paths — document in 007A1; implement in 007B+ if concurrency authorized.

### 8. Leakage review

Retrieval runtime must **not** introduce: answer generation, legal reasoning, legal meaning, tax applicability, recommendations, confidence scores, AI/LLM inference, semantic/vector search (004A prohibitions stand).

---

## Findings

### R-01 — HIGH

| Field | Value |
|-------|--------|
| **Title** | Implicit “latest” version when `effective_on` is absent |
| **Exact risk** | `apply_effective_date_filter(None)` joins via `current_version_id`, selecting operational latest without explicit `as_of_date` — violates temporal governance (no silent latest = applicable law). |
| **Blocks TASK-007B?** | **Yes** |
| **Recommended remediation** | TASK-007A1: runtime contract requires explicit `as_of_date`; 004A runtime wrapper rejects None; document override flag if operator intentionally requests current pointer. |

### R-02 — HIGH

| Field | Value |
|-------|--------|
| **Title** | `LegalObjectRetrievalResult` missing `legal_object_version_id` |
| **Exact risk** | Results cannot pin the version row returned; citation handoff and provenance chain break at retrieval → citation boundary. |
| **Blocks TASK-007B?** | **Yes** |
| **Recommended remediation** | TASK-007A1: add `legal_object_version_id` to result model; populate from joined version row; tests for pin stability. |

### R-03 — HIGH

| Field | Value |
|-------|--------|
| **Title** | Evidence envelope undefined — `canonical_text` collapse risk |
| **Exact risk** | 004A returns full `canonical_text`; unconstrained runtime exposure enables answer-like consumption without citation boundary. |
| **Blocks TASK-007B?** | **Yes** |
| **Recommended remediation** | TASK-007A1: define evidence DTO tiers (reference-only vs optional text payload); default runtime path returns references + hashes; text requires explicit `include_canonical_text`. |

### R-04 — HIGH

| Field | Value |
|-------|--------|
| **Title** | No retrieval runtime identity or persistence doctrine |
| **Exact risk** | Without `request_hash`, append-only audit, and result lifecycle, replay/idempotency/concurrency cannot be governed (006Z lesson). |
| **Blocks TASK-007B?** | **Yes** |
| **Recommended remediation** | TASK-007A1: specify `retrieval_request_hash`, tables, prohibited result fields, idempotency — mirror citation governance package. |

### R-05 — HIGH

| Field | Value |
|-------|--------|
| **Title** | No citation reference retrieval path |
| **Exact risk** | 006AD `citations` entity exists but 004A only queries legal objects; runtime cannot return citation evidence without new governed lookup (by `citation_id` / `citation_hash` / filters). |
| **Blocks TASK-007B?** | **Yes** |
| **Recommended remediation** | TASK-007A1: define citation evidence lookup (read `citations` table only; no re-assembly); provenance validation against legal memory. |

### R-06 — MEDIUM

| Field | Value |
|-------|--------|
| **Title** | `retrieve_by_id()` ordering gap when multiple versions match |
| **Exact risk** | `.first()` without deterministic order when `effective_on` set and multiple versions match — non-reproducible selection (004A deferred hardening). |
| **Blocks TASK-007B?** | **Yes** (for runtime wrapping 004A) |
| **Recommended remediation** | Apply `apply_deterministic_order` before `.first()`; test multi-version overlap. |

### R-07 — MEDIUM

| Field | Value |
|-------|--------|
| **Title** | Namespace collision — `source_retrieval_log` vs legal retrieval runtime |
| **Exact risk** | Operator confusion; accidental coupling of source-ingestion retrieval logs with legal-memory evidence retrieval. |
| **Blocks TASK-007B?** | No |
| **Recommended remediation** | TASK-007A1: naming doctrine — `retrieval_governance_*` or `legal_evidence_retrieval_*`; document distinction from source fetch logs. |

### R-08 — MEDIUM

| Field | Value |
|-------|--------|
| **Title** | Deterministic sort vs ranking ambiguity |
| **Exact risk** | Future implementers may treat ordered lists as relevance-ranked results. |
| **Blocks TASK-007B?** | No |
| **Recommended remediation** | Runtime contract explicit: ordering = stable tie-break only; no scores; no “top result” semantics. |

### R-09 — MEDIUM

| Field | Value |
|-------|--------|
| **Title** | 004A contract purpose drift |
| **Exact risk** | Contract states purpose includes “answer generation” path while prohibiting it — governance ambiguity. |
| **Blocks TASK-007B?** | No |
| **Recommended remediation** | Amend 004A contract: retrieval feeds evidence for **future governed** answer assembly; runtime does not generate answers. |

### R-10 — INFORMATIONAL (OD-021 carry-forward)

| Field | Value |
|-------|--------|
| **Title** | Concurrent retrieval workers |
| **Exact risk** | DB uniqueness alone insufficient under concurrent orchestration. |
| **Blocks TASK-007B?** | No (single-worker initial scope) |
| **Recommended remediation** | Document `request_hash`-keyed advisory/row locks for future concurrency gate. |

---

## What 007A does NOT authorize

| Capability | Authorized? |
|------------|-------------|
| TASK-007B retrieval runtime implementation | **No** — 007A1 spec delivered; acceptance review pending |
| Ranking / relevance scoring | **No** |
| Answer runtime | **No** |
| Legal interpretation / tax advice | **No** |
| Applicability inference | **No** |
| AI / LLM / semantic search | **No** |

---

## Required sequence before TASK-007B

```text
TASK-007A Review (this document) — APPROVED WITH REQUIRED REMEDIATION — **done**
  → TASK-007A1 — retrieval runtime remediation package — **complete** ([`RETRIEVAL_RUNTIME_REMEDIATION_007A1.md`](RETRIEVAL_RUNTIME_REMEDIATION_007A1.md))
  → TASK-007A1 acceptance review — **pending**
  → TASK-007B — bounded retrieval runtime implementation — **not authorized**
```

---

## Final verdict

**APPROVED WITH REQUIRED REMEDIATION BEFORE TASK-007B**

Retrieval runtime may be **considered** after TASK-007A1 closes findings R-01 through R-06 (minimum). Findings R-07–R-10 are recommended governance hygiene.

Preserved doctrines:

```text
parsed_structure ≠ legal object
legal_object ≠ legal meaning
legal_object ≠ citation
citation ≠ retrieval result
retrieval result ≠ answer
```

---

## References

- [`CLAUDE_REVIEW_CITATION_PIPELINE_006Y-006AD.md`](CLAUDE_REVIEW_CITATION_PIPELINE_006Y-006AD.md)
- [`CLAUDE_REVIEW_LEGAL_OBJECT_PROMOTION_006U-X.md`](CLAUDE_REVIEW_LEGAL_OBJECT_PROMOTION_006U-X.md)
- [`CITATION_EXECUTION_REMEDIATION_006AC1.md`](CITATION_EXECUTION_REMEDIATION_006AC1.md) (identity/persistence precedent)
- [`TASKS/TASK-007A-RETRIEVAL-RUNTIME-PREAUTH-REVIEW.md`](TASKS/TASK-007A-RETRIEVAL-RUNTIME-PREAUTH-REVIEW.md)

---

END OF TASK-007A PRE-AUTHORIZATION REVIEW
