# Ranking Execution Contract

## Purpose

Define governed boundaries for **deterministic mechanical ranking execution** — applying declared `ranking_profile` permutations over completed retrieval evidence and persisting pure-pointer `ranked_evidence_references`.

This contract is **governance only** (TASK-008D-PREAUTH). It authorizes the ranking execution **design envelope** for downstream bounded implementation. It does **not** authorize worker code, services, migrations, APIs, answer runtime (009A), or AI/semantic ranking.

## Core principle

**Ranking execution permutes evidence presentation order — it does not select, score, re-retrieve, or conclude.**

```text
ranking_request (persisted)
  → ranking_result (accepted)
  → ranking execution (mechanical permutation)
  → ranked_evidence_references (pure pointers)
  → ranking_result (completed | failed)
```

Ranking execution is **not**:

- evidence selection or re-retrieval
- relevance ranking or scoring
- answer generation or legal interpretation
- applicability determination
- semantic / vector / AI ordering
- filtering, suppression, top-N, or deduplication

## Mandatory doctrines

| Doctrine | Rule |
|----------|------|
| `retrieval result` ≠ ranking | Execution consumes completed retrieval only — no re-selection |
| `ranking` ≠ answer | Ordered pointers support future answer assembly only |
| `answer` ≠ legal conclusion | No obligation or consequence inference at execution |
| **Ranking stores order only** | `presentation_order_index` — no scores, no authority weighting |
| **Provenance lives once** | Pins authoritative in `retrieval_evidence_references` only (DEC-010) |
| **Deterministic execution** | Same inputs + profile → same permutation |
| **Permutation only** | Identical evidence multiset in and out |

Upstream contracts (binding, closed):

- [`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md) (008B-v2)
- [`TASKS/TASK-008C-RANKING-PERSISTENCE.md`](TASKS/TASK-008C-RANKING-PERSISTENCE.md) (008C complete)
- [`DECISION_LOG.md`](DECISION_LOG.md) — DEC-010, DEC-011, DEC-012

---

## 1. Deterministic ranking execution invariants

Ranking execution **must** be fully deterministic given:

| Input | Source |
|-------|--------|
| `retrieval_result_id` | `ranking_requests.retrieval_result_id` |
| `retrieval_status` | Must be `completed` |
| `retrieval_result.result_count` | Must match evidence row count |
| Input evidence set | All `retrieval_evidence_references` for `retrieval_result_id` |
| `ranking_profile` | Closed enum from request |
| `contract_version` | `"008B-v2"` (current generation) |

**Determinism rules:**

- Same completed retrieval result + same profile + same contract generation → **identical** ordered list of `retrieval_evidence_reference_id` values and `presentation_order_index` assignments
- Sort-time reads from retrieval evidence rows (and permitted joins) are **read-only** — values used for ordering **must not** be copied onto ranked rows
- No randomness, no timestamps in sort keys, no actor-specific behavior, no floating-point sort keys
- Profile algorithms defined in [`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md) §Deterministic ordering — execution must match contract exactly

**Prohibited nondeterminism:**

- AI/LLM ordering
- Semantic/vector similarity
- Relevance or confidence scores
- Runtime-defined profiles or sort keys
- Re-querying retrieval for different evidence subsets

---

## 2. Permutation integrity invariants

Ranking execution is **permutation only** (RK-04).

| Rule | Requirement |
|------|-------------|
| Input membership | Set of `retrieval_evidence_reference_id` values for pinned `retrieval_result_id` |
| Output membership | Identical set |
| Input count | `N` = `retrieval_result.result_count` |
| Output count | `rank_count` = `N` (or 0 when N=0) |
| Multiplicity | Duplicates preserved — no deduplication |
| Order index | `presentation_order_index` contiguous `1..N` |

**Pre-persist validation (execution MUST perform):**

1. Load all input `retrieval_evidence_reference_id` values for `retrieval_result_id`
2. Apply profile permutation → ordered list
3. Assert `len(output_ids) == len(input_ids) == N`
4. Assert `set(output_ids) == set(input_ids)` with identical multiplicity
5. Assign `presentation_order_index` 1..N in output order
6. On mismatch → `ranking_status=failed`, `error_category=permutation_mismatch`

**Prohibited:**

- additions, removals, filtering, suppression, top-N, deduplication, `LIMIT`-as-ranking

**Persisted output shape (008C pure-pointer — DEC-010):**

Each `ranked_evidence_reference` row stores **only**:

- `ranking_result_id`, `retrieval_result_id`, `retrieval_evidence_reference_id`, `presentation_order_index`

No copied provenance. Composite FK membership enforced at persistence layer.

---

## 3. Zero-evidence execution path

When `retrieval_result.result_count = 0` and `retrieval_status = completed`:

| Step | Behavior |
|------|----------|
| Prerequisite | Valid — zero-result retrieval is success, not failure |
| Input load | Zero `retrieval_evidence_references` rows |
| Permutation | Identity on empty set |
| Persist ranked rows | **None** |
| Terminal result | `ranking_status=completed`, `rank_count=0` |
| Error | **None** — `evidence_set_empty` is **prohibited** |

Execution must not treat empty evidence as `failed` or emit any error category for valid zero-result retrieval.

---

## 4. Ranking profile governance

**Closed enum — no runtime-created profiles.**

| Profile | Execution semantics |
|---------|---------------------|
| `CANONICAL` | Sort by `deterministic_order_index ASC`; identity permutation |
| `EFFECTIVE_DATE_DESC` | Primary `effective_from DESC NULLS LAST`; mechanical tie-break chain |
| `GROUP_BY_SOURCE` | Group by `source_version_id`; inter-group `source_version_id ASC`; within-group tie-break chain |
| `GROUP_BY_DOCUMENT` | Group by `source_document_id`; inter-group `source_document_id ASC NULLS LAST`; NULL group last |

**Governance rules:**

- Profiles are declared on `ranking_requests.ranking_profile` only
- Invalid or unknown profile at execution → `failed`, `error_category=profile_not_allowed`
- New profiles require governance amendment — not runtime configuration
- Profile sort keys are **mechanical** — not legal authority, relevance, or recency-as-importance

Full sort specifications: [`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md) §Deterministic ordering.

---

## 5. Canonical execution error vocabulary

Authoritative `error_category` values for failed ranking execution. **No competing categories.**

```text
retrieval_result_missing
retrieval_result_not_completed
evidence_reference_missing
provenance_incomplete
profile_not_allowed
duplicate_ranking
permutation_mismatch
ranking_pipeline_unavailable
unknown_failure
```

**Prohibited error categories:**

- `evidence_set_empty` (zero-result is success)
- `invalid_request`, `retrieval_not_completed`, `permutation_violation` (superseded vocabulary)

**Typical execution mapping:**

| Condition | `error_category` |
|-----------|------------------|
| `retrieval_result` row missing | `retrieval_result_missing` |
| `retrieval_status` ≠ `completed` | `retrieval_result_not_completed` |
| `result_count` ≠ evidence row count | `evidence_reference_missing` |
| Evidence row fails provenance join integrity | `provenance_incomplete` |
| Unknown `ranking_profile` | `profile_not_allowed` |
| Default request hash collision (idempotency) | `duplicate_ranking` |
| Post-sort membership/count check fails | `permutation_mismatch` |
| Execution infrastructure unavailable | `ranking_pipeline_unavailable` |
| Unclassified failure | `unknown_failure` |

Errors persist on `ranking_results` only — no separate `ranking_errors` table.

---

## 6. Ranking execution lifecycle

### Request identity

```text
ranking_request_hash = SHA-256(canonical_json({
  retrieval_result_id,
  ranking_profile,
  contract_version
}))
```

Force replay: see DEC-011 — replay entropy in hash payload only; does not bypass validation.

### Lifecycle states

```text
ranking_request (persisted)
  → ranking_result (accepted)
  → [execution]
  → ranking_result (completed | failed | skipped | duplicate_rejected)
```

| `ranking_status` | Meaning |
|------------------|---------|
| `pending` | Reserved — pre-acceptance |
| `accepted` | Execution authorized to proceed |
| `completed` | Permutation persisted; `rank_count` set |
| `failed` | Terminal error; `error_category` required |
| `skipped` | Dry-run / no-op terminal (skeleton mode) |
| `duplicate_rejected` | Idempotency rejection |

### Execution pipeline (when authorized)

```text
1. Load ranking_request + latest accepted ranking_result (or create accepted)
2. Validate retrieval_result exists and retrieval_status = completed
3. Validate result_count matches evidence reference count
4. If N=0 → complete with rank_count=0 (no ranked rows)
5. Load retrieval_evidence_references read-only
6. Apply ranking_profile mechanical sort
7. Validate permutation integrity
8. Persist ranked_evidence_references (pure-pointer rows only)
9. Persist ranking_result completed (rank_count=N, completed_at)
```

On failure after `accepted`: append new `ranking_result` row with `failed` — **append-only**, no updates to prior rows.

**Must not modify:** `retrieval_results`, `retrieval_evidence_references`.

### Idempotency

- Default requests: partial unique `UNIQUE (ranking_request_hash) WHERE force_replay = false`
- Duplicate default request → `duplicate_ranking` or `duplicate_rejected` per implementation envelope
- `force_replay=true` → new lifecycle rows only (DEC-011)

---

## 7. Single-worker doctrine (OD-021)

| Rule | Requirement |
|------|-------------|
| Initial orchestration | **Single-worker** ranking execution only |
| Concurrent workers | **NOT AUTHORIZED** |
| Future concurrency | Requires explicit governance gate; `ranking_request_hash`-keyed advisory/row locks |
| Parallel execution | Must not run two executions for same default `ranking_request_hash` |

Dry-run skeleton (pre-execution) may follow retrieval worker pattern: `accepted` → `skipped` without persisting ranked rows.

---

## 8. Explicit prohibitions

### Ranking modalities (prohibited)

| Capability | Status |
|------------|--------|
| AI ranking | **NOT AUTHORIZED** |
| Semantic ranking | **NOT AUTHORIZED** |
| Vector / embedding ranking | **NOT AUTHORIZED** |
| Relevance / confidence scoring | **NOT AUTHORIZED** |
| BM25 or learned rankers | **NOT AUTHORIZED** |

### Downstream boundaries (prohibited)

| Capability | Status |
|------------|--------|
| Answer generation | **NOT AUTHORIZED** |
| Legal conclusions | **NOT AUTHORIZED** |
| Applicability determination | **NOT AUTHORIZED** |
| Citation synthesis / `CitationAssembler` | **NOT AUTHORIZED** |
| Retrieval re-selection (`retrieval_execution`) | **NOT AUTHORIZED** |

### Infrastructure (prohibited until authorized)

| Capability | Status |
|------------|--------|
| Ranking worker implementation | **NOT AUTHORIZED** (this contract is pre-auth only) |
| Execution services / APIs | **NOT AUTHORIZED** |
| Concurrent ranking workers | **NOT AUTHORIZED** |
| Runtime-defined ranking profiles | **NOT AUTHORIZED** |

### Import guard requirements (RE-01)

Future ranking execution code **must not** import:

- `app.services.answer`
- `app.services.ai`
- `app.services.semantic`
- `app.services.vector`
- `app.services.retrieval_execution`
- `CitationAssembler` / `app.services.citation.assembler`

Mechanical boundary tests required at implementation gate.

### Prohibited fields

Same as [`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md) §Prohibited fields — no scores, answer text, legal conclusions, or interpretive weights on execution outputs or DTOs.

---

## Relationship to persistence (008C)

Execution **consumes** append-only persistence:

| Table | Execution role |
|-------|----------------|
| `ranking_requests` | Input envelope |
| `ranking_results` | Lifecycle terminal states |
| `ranked_evidence_references` | Pure-pointer output rows |

Execution must use `ranking_persistence` append-only create paths — no update/delete of historical ranking rows.

---

## Governed pipeline

```text
TASK-008B  Ranking runtime contract (complete)
  → TASK-008C  Persistence (complete — v0.1.3)
  → TASK-008D-PREAUTH  This contract (governance)
  → TASK-008D  Controlled execution (NOT AUTHORIZED)
  → Ranking Layer Review (future)
  → TASK-009A  Answer assembly (NOT AUTHORIZED)
```

---

## References

- [`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md)
- [`TASKS/TASK-008D-RANKING-EXECUTION.md`](TASKS/TASK-008D-RANKING-EXECUTION.md)
- [`TASKS/TASK-008C-RANKING-PERSISTENCE.md`](TASKS/TASK-008C-RANKING-PERSISTENCE.md)
- [`DECISION_LOG.md`](DECISION_LOG.md) — DEC-010, DEC-011, DEC-012
- [`RETRIEVAL_RUNTIME_CONTRACT.md`](RETRIEVAL_RUNTIME_CONTRACT.md)
- [`TASKS/TASK-007E-CONTROLLED-RETRIEVAL-EXECUTION.md`](TASKS/TASK-007E-CONTROLLED-RETRIEVAL-EXECUTION.md) (execution pattern reference)

---

END OF RANKING EXECUTION CONTRACT (TASK-008D-PREAUTH)
