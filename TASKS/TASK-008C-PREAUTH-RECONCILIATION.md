# TASK-008C-PREAUTH-RECONCILIATION — Ranking Persistence Pre-Authorization Reconciliation

## Status

**Complete** — **ACCEPTED** — governance reconciliation verified; **TASK-008C implementation NOT AUTHORIZED**.

| Delivery | Value |
|----------|--------|
| Commit | `cc170aa` — `docs: accept TASK-008C preauth reconciliation` |
| Branch | `main` — pushed `origin/main` |
| Tag | `v0.1.2-ranking-preauth-reconciled` |

## Important

- **Does NOT implement** TASK-008C persistence, migrations, models, workers, or APIs
- **Does NOT modify** retrieval layer (007A–007E)
- **Confirms** amended [`RANKING_RUNTIME_CONTRACT.md`](../RANKING_RUNTIME_CONTRACT.md) (008B-v2) is internally consistent for future 008C design

## Objective

Pre-authorization reconciliation of ranking persistence contract against provenance-once doctrine before TASK-008C authorization prompt or Claude review.

## Prerequisites

| Artifact | Status |
|----------|--------|
| TASK-008B contract | **Complete** (008B-v2) |
| TASK-008C-REMEDIATION | **Complete** |
| Retrieval persistence (007C) | **Complete** — live `retrieval_results.id`, `retrieval_evidence_references.id` |

## Reconciliation checklist (verified)

### 1. Pure-pointer `ranked_evidence_references`

Persisted columns only:

| Column | FK target |
|--------|-----------|
| `ranking_result_id` | `ranking_results.id` |
| `retrieval_result_id` | `retrieval_results.id` |
| `retrieval_evidence_reference_id` | `retrieval_evidence_references.id` |
| `presentation_order_index` | — |

Plus surrogate PK `id`. **No copied provenance fields.**

### 2. Provenance resolution

Provenance obtained **only** by joining `ranked_evidence_references` → `retrieval_evidence_references` → upstream chain.

### 3. Canonical error vocabulary

- `retrieval_result_missing`
- `retrieval_result_not_completed`
- `evidence_reference_missing`
- `provenance_incomplete`
- `profile_not_allowed`
- `duplicate_ranking`
- `permutation_mismatch`
- `ranking_pipeline_unavailable`
- `unknown_failure`

**Removed:** `evidence_set_empty`. Completed retrieval with `result_count=0` → ranking `status=completed`, `rank_count=0`.

### 4. Structural membership protection

```sql
UNIQUE (retrieval_result_id, id)  -- on retrieval_evidence_references (008C migration)

FOREIGN KEY (retrieval_result_id, retrieval_evidence_reference_id)
  REFERENCES retrieval_evidence_references (retrieval_result_id, id)
  -- on ranked_evidence_references
```

### 5. Prohibited-field guard parity

`authority_weight`, `importance_flag`, `preference_score` — prohibited on all ranking persistence surfaces.

### 6. Live parent PK FK targets

All FKs reference `retrieval_results.id` and `retrieval_evidence_references.id` (not legacy or alternate column names).

## Explicit prohibitions (unchanged)

- No Alembic migrations
- No SQLAlchemy models
- No ranking services / workers
- No ranking execution pipeline

## Authorization state

| Item | Status |
|------|--------|
| TASK-008C-PREAUTH-RECONCILIATION | **Complete** |
| TASK-008C persistence implementation | **NOT AUTHORIZED** |
| TASK-008D worker / execution | **NOT AUTHORIZED** |
| TASK-009A answer runtime | **NOT AUTHORIZED** |

## Next gate

Claude review and/or explicit **TASK-008C** persistence authorization prompt.

---

END OF TASK-008C-PREAUTH-RECONCILIATION
