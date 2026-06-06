# Ranking Runtime Contract

## Purpose

Define governed boundaries for **mechanical presentation ordering** of retrieval evidence references.

This contract is **governance only**. It authorizes the ranking runtime **design envelope** for downstream tasks. It does **not** authorize persistence implementation (008C), workers (008D), answer runtime (009A), or AI/semantic ranking.

## Core principle

**Ranking permutes evidence presentation order — it does not select, score, or conclude.**

```text
retrieval_result (completed)
  → ranking_request
  → ranking_result
  → ranked_evidence_reference
```

Ranking is **not**:

- evidence selection or re-retrieval
- relevance ranking or scoring
- answer generation or legal interpretation
- applicability determination
- semantic / vector / AI ordering
- filtering, suppression, top-N, or deduplication

## Mandatory doctrines

| Doctrine | Rule |
|----------|------|
| `retrieval result` ≠ ranking | Retrieval owns evidence set; ranking permutes only |
| `ranking` ≠ answer | Ordered pointers support future answer assembly |
| `answer` ≠ legal conclusion | No obligation or consequence inference at ranking |
| `retrieval evidence` ≠ ranking | `deterministic_order_index` is retrieval-owned |
| `presentation_order_index` ≠ relevance rank | Integer position only — no scores |

## Ranking role

Ranking runtime is responsible for:

- accepting governed ranking requests against exactly one **completed** `retrieval_result`
- loading input `retrieval_evidence_references` read-only
- applying a declared **mechanical** `ranking_profile` permutation
- persisting append-only `ranked_evidence_references` with `presentation_order_index`
- enforcing idempotency on `ranking_request_hash`
- preserving permutation invariant (same multiset in, same multiset out)

Ranking runtime must **not**:

- add, remove, filter, or deduplicate evidence
- re-query legal object or citation tables for re-selection
- create citations or invoke `CitationAssembler`
- mutate provenance pins on output rows
- emit scores, answers, or legal conclusions
- invoke AI/LLMs or semantic/vector search

## Layer definition (canonical)

```text
retrieval_result (completed, result_count=N)
  → ranking_request (ranking_request_hash)
  → ranking_result (accepted → completed | failed | skipped)
  → ranked_evidence_references (presentation_order_index 1..N)
```

**Upstream (closed):** retrieval layer 007A–007E — immutable for ranking.

**Downstream (not authorized):** answer assembly 009A+.

---

## Identity — `ranking_request_hash` (RK-02)

```text
ranking_request_hash = SHA-256(
  canonical_json({
    retrieval_result_id,
    ranking_profile,
    contract_version
  })
)
```

### Canonical JSON rules

Same discipline as retrieval RP-01 / 007C1:

- Lexicographic key sort at every nesting level
- Compact UTF-8 serialization
- ISO 8601 UUID strings for IDs
- No floats in envelope
- `contract_version` required when multiple contract generations exist; fixed string for initial contract (e.g. `"008B-v1"`)

### Excluded from hash

- actor fields, timestamps, notes
- relevance / semantic / AI parameters (prohibited)
- raw query text

### Separation

```text
request_hash (retrieval) ≠ ranking_request_hash ≠ retrieval_evidence_reference_id
```

`force_replay` appends new lifecycle rows — does not bypass permutation or prerequisite validation.

---

## Ranking profiles (RK-08)

**Closed enum — no runtime-created profiles. No configurable profile definitions.**

| Profile | Semantics |
|---------|-----------|
| `CANONICAL` | Identity permutation — preserves retrieval `deterministic_order_index` order |
| `EFFECTIVE_DATE_DESC` | Sort by `effective_from` descending — **sort only**, not recency-as-importance |
| `GROUP_BY_SOURCE` | Group by `source_version_id`; deterministic group order + within-group order |
| `GROUP_BY_DOCUMENT` | Group by `source_document_id`; deterministic group order + within-group order |

**New profiles require governance amendment** — not runtime configuration.

---

## Completed retrieval prerequisite (RK-03)

Ranking may consume **only**:

| Input | Rule |
|-------|------|
| `retrieval_result_id` | Required FK |
| `retrieval_status` | Must be `completed` |

**Rejected inputs:**

| Status | Action |
|--------|--------|
| `accepted` | Reject — `error_category=retrieval_not_completed` |
| `failed` | Reject — `error_category=retrieval_not_completed` |
| `skipped` | Reject — `error_category=retrieval_not_completed` |
| `pending` | Reject — `error_category=retrieval_not_completed` |

**Validation:**

- `retrieval_result.result_count` must equal count of `retrieval_evidence_references` for that result
- Zero-result (`result_count=0`) is valid → ranking completes with `rank_count=0`

---

## Ranked object (input)

Input set = **all** `retrieval_evidence_references` rows for the pinned `retrieval_result_id`.

- Exactly one completed retrieval result per ranking request
- No cross-result merging
- No subset selection

Fields read **read-only** from each input row (RK-05):

- `retrieval_evidence_reference_id`
- `legal_object_id`, `legal_object_version_id`
- `source_version_id`, `source_document_id`
- `citation_id`, `citation_hash` (when present)
- `deterministic_order_index` (for `CANONICAL` only)
- `effective_from` (from joined version or denormalized evidence metadata when present)

**Prohibited during ranking:**

- Citation lookup or creation
- `CitationAssembler` invocation
- Version re-resolution or temporal re-filtering
- Provenance mutation

---

## Permutation invariant (RK-04)

Ranking is **permutation only**.

| Rule | Requirement |
|------|-------------|
| Input membership | Set of `retrieval_evidence_reference_id` values |
| Output membership | Identical set |
| Input count | `N` = `retrieval_result.result_count` |
| Output count | `rank_count` = `N` (or 0 when N=0) |
| Multiplicity | Duplicates preserved — no deduplication |

**Prohibited:**

- additions
- removals
- filtering
- suppression
- top-N (when N < input count)
- deduplication
- `LIMIT`-as-ranking

---

## Deterministic ordering (008A1 forward conditions)

### Canonical tie-break chain (shared)

After primary sort key(s) for a profile, apply this **mechanical** chain:

```text
1. effective_from ASC NULLS LAST     (omitted when already primary DESC key)
2. legal_object_id ASC
3. legal_object_version_id ASC
4. citation_hash ASC NULLS LAST
5. object_identifier ASC NULLS LAST
6. retrieval_evidence_reference_id ASC   (guaranteed-unique final tiebreaker)
```

Step 6 ensures total order even when all prior keys collide.

### `CANONICAL`

Sort input rows by `deterministic_order_index ASC`.

Assign `presentation_order_index` 1..N in that order.

Identity permutation relative to retrieval canonical order.

### `EFFECTIVE_DATE_DESC` (Condition 3 — sort-only)

**Primary:**

```text
effective_from DESC NULLS LAST
```

**Then tie-break chain** (excluding duplicate `effective_from` key):

```text
legal_object_id ASC
legal_object_version_id ASC
citation_hash ASC NULLS LAST
object_identifier ASC NULLS LAST
retrieval_evidence_reference_id ASC
```

**Not authorized:** interpreting DESC as legal importance, recency weighting, or relevance.

### `GROUP_BY_SOURCE` (Condition 1 — inter-group ordering)

**Group key:** `source_version_id`

**Group ordering (inter-group):**

```text
source_version_id ASC
```

(UUID lexical order — deterministic, not authority weighting)

**Within-group ordering:**

```text
effective_from ASC NULLS LAST
legal_object_id ASC
legal_object_version_id ASC
citation_hash ASC NULLS LAST
object_identifier ASC NULLS LAST
retrieval_evidence_reference_id ASC
```

**Output construction:** Emit groups in `source_version_id ASC` order; within each group emit rows in within-group order. Assign `presentation_order_index` 1..N globally across concatenated groups.

### `GROUP_BY_DOCUMENT` (Condition 1 — inter-group ordering)

**Group key:** `source_document_id` (nullable)

**Group ordering (inter-group):**

```text
source_document_id ASC NULLS LAST
```

Rows with `NULL` `source_document_id` form a single trailing group.

**Within-group ordering:** same chain as `GROUP_BY_SOURCE` within-group.

**Output construction:** Emit non-null document groups in `source_document_id ASC` order, then the NULL group last; assign `presentation_order_index` 1..N globally.

```text
presentation ordering ≠ relevance ranking
profile sort keys ≠ legal authority weighting
```

---

## Naming standard (Condition 4)

**Use only:** `presentation_order_index`

**Do not use:** `rank_position`, `ranking_position`, `rank`, `relevance_rank`, `deterministic_order_index` (retrieval-owned)

`presentation_order_index` starts at **1**, contiguous through `N`.

---

## Prohibited fields (RK-07, RK-09)

**Prohibited on ranking requests, results, ranked references, DTOs, APIs, and DB columns:**

| Category | Fields |
|----------|--------|
| Scores | `ranking_score`, `relevance_score`, `confidence_score`, `semantic_score`, `embedding_score`, `ai_score`, `llm_score`, `bm25_score` |
| Answer / conclusion | `answer_text`, `legal_conclusion`, `applicability_flag`, `recommendation_text`, `summary_text` |
| Interpretive | `authority_weight`, `importance_flag`, `preference_score` |

---

## Persistence doctrine (RK-06 — binding constraints for 008C)

**008C not authorized by this contract alone.** This section defines **binding requirements** 008C must implement.

### Tables (append-only)

| Table | Role |
|-------|------|
| `ranking_requests` | Request envelope + `ranking_request_hash` |
| `ranking_results` | Lifecycle metadata |
| `ranked_evidence_references` | Permutation output rows |

### Append-only rules

- No `UPDATE` of prior ranking results or ranked references
- No `DELETE` of prior rows
- `force_replay` creates new lifecycle rows only

### Required constraints (008C MUST implement)

**Partial unique index:**

```sql
UNIQUE (ranking_request_hash) WHERE force_replay = false
```

**Unique presentation index per result:**

```sql
UNIQUE (ranking_result_id, presentation_order_index)
```

**Required CHECK — `ranking_profile`:**

```text
ranking_profile IN ('CANONICAL', 'EFFECTIVE_DATE_DESC', 'GROUP_BY_SOURCE', 'GROUP_BY_DOCUMENT')
```

**Required CHECK — `ranking_status`:**

```text
ranking_status IN (
  'pending', 'accepted', 'completed', 'failed', 'skipped', 'duplicate_rejected'
)
```

**Required CHECK — `error_category` (when present):**

```text
error_category IS NULL OR error_category IN (
  'invalid_request',
  'retrieval_not_completed',
  'permutation_violation',
  'provenance_incomplete',
  'profile_not_allowed'
)
```

### `ranking_results` lifecycle fields (planned)

- `ranking_result_id`, `ranking_request_id`, `retrieval_result_id`
- `ranking_status`, `rank_count`, `completed_at`
- `error_category`, `error_message`, `notes`

`rank_count` must equal persisted `ranked_evidence_references` count.

### `ranked_evidence_references` (planned minimum)

| Field | Required |
|-------|----------|
| `ranked_evidence_reference_id` | Yes |
| `ranking_result_id` | Yes |
| `retrieval_evidence_reference_id` | Yes — FK |
| `presentation_order_index` | Yes |
| `legal_object_id` | Yes — read-only copy |
| `legal_object_version_id` | Yes — read-only copy |
| `source_version_id` | Yes — read-only copy |
| `citation_id` | Nullable — read-only copy |
| `citation_hash` | Nullable — read-only copy |

No score columns. No answer fields.

---

## Import guard requirements (RK-10)

Future ranking execution (008D) **must not** import:

- `app.services.answer`
- `app.services.ai`
- `app.services.semantic`
- `app.services.vector`
- `app.services.retrieval_execution` (re-selection prohibited)
- `CitationAssembler` / `app.services.citation.assembler`

Mechanical tests required at 008D boundary.

---

## OD-021 (concurrency)

- **Single-worker** ranking orchestration acceptable initially
- **Concurrent ranking workers not authorized**
- Future: `ranking_request_hash`-keyed advisory/row locks when concurrency gate opens

---

## Relationship to retrieval layer (007A–007E)

Retrieval layer is **complete** and **closed**.

| Retrieval owns | Ranking owns |
|----------------|--------------|
| Evidence selection | Presentation permutation |
| `deterministic_order_index` | `presentation_order_index` |
| `retrieval_request` / `retrieval_result` | `ranking_request` / `ranking_result` |
| Temporal modes | Mechanical sort profiles only |

Ranking **must not** modify `retrieval_evidence_references` or `retrieval_results`.

---

## Governed pipeline

```text
TASK-008B  This contract (governance)
  → TASK-008C  Persistence (not authorized)
  → TASK-008D  Worker / execution (not authorized)
  → Ranking Layer Review (future)
  → TASK-009A  Answer assembly pre-auth (not authorized)
```

---

## Prohibited capabilities

| Capability | Status |
|------------|--------|
| Ranking persistence / workers (008C / 008D) | **NOT AUTHORIZED** |
| Answer runtime (009A) | **NOT AUTHORIZED** |
| AI / semantic / vector ranking | **NOT AUTHORIZED** |
| Concurrent ranking workers | **NOT AUTHORIZED** |
| Runtime-defined ranking profiles | **NOT AUTHORIZED** |
| Relevance scoring | **NOT AUTHORIZED** |
| Legal interpretation | **NOT AUTHORIZED** |

---

## 008A1 forward conditions — resolution record

| # | Condition | Resolution in this contract |
|---|-----------|----------------------------|
| 1 | Deterministic inter-group ordering | §`GROUP_BY_SOURCE`, §`GROUP_BY_DOCUMENT` |
| 2 | Binding persistence constraints for 008C | §Persistence doctrine |
| 3 | `EFFECTIVE_DATE_DESC` sort-only | §`EFFECTIVE_DATE_DESC` |
| 4 | `presentation_order_index` standard | §Naming standard |

---

## References

- [`RANKING_RUNTIME_REMEDIATION_008A1.md`](RANKING_RUNTIME_REMEDIATION_008A1.md)
- [`RANKING_RUNTIME_008A1_ACCEPTANCE_REVIEW.md`](RANKING_RUNTIME_008A1_ACCEPTANCE_REVIEW.md)
- [`RETRIEVAL_RUNTIME_CONTRACT.md`](RETRIEVAL_RUNTIME_CONTRACT.md)
- [`CLAUDE_REVIEW_RETRIEVAL_PIPELINE_007A-007E.md`](CLAUDE_REVIEW_RETRIEVAL_PIPELINE_007A-007E.md)

---

END OF RANKING RUNTIME CONTRACT (TASK-008B)
