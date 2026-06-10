# TASK-008C — Ranking Persistence

## Status

**COMPLETE** — limited persistence implementation (append-only tables, models, persistence service, tests).

**NOT authorized:** ranking execution (008D), workers, algorithms, AI ranking, answer assembly (009A).

## Authorization

Approved for **limited implementation** per pure-pointer contract (`RANKING_RUNTIME_CONTRACT.md` 008B-v2, DEC-010).

## Prerequisite chain

```text
008A Review → 008A1 Remediation → 008A1 Acceptance
  → 008B Contract (008B-v2)
  → 008C-REMEDIATION
  → 008C-PREAUTH-RECONCILIATION (accepted cc170aa)
  → 008C Persistence (this task) — COMPLETE
```

## Deliverables

| Area | Artifact |
|------|----------|
| Migration | `a8c1e4f92b37_create_ranking_persistence_tables.py` |
| Models | `ranking_request`, `ranking_result`, `ranked_evidence_reference` |
| Service | `app/services/ranking_persistence/` — append-only lifecycle |
| Tests | `test_ranking_persistence.py`, `test_ranking_persistence_alembic_migration.py` |

## Tables

| Table | Role |
|-------|------|
| `ranking_requests` | Request envelope + `ranking_request_hash` |
| `ranking_results` | Lifecycle metadata (`ranking_status`, `rank_count`, errors) |
| `ranked_evidence_references` | Pure-pointer permutation rows |

No separate `ranking_errors` table — errors live on `ranking_results` per contract.

## Pure-pointer shape (`ranked_evidence_references`)

Persisted columns only:

- `id` (surrogate PK)
- `ranking_result_id` → `ranking_results.id`
- `retrieval_result_id` → `retrieval_results.id`
- `retrieval_evidence_reference_id` → `retrieval_evidence_references.id`
- `presentation_order_index`
- `created_at` (append-only audit timestamp)

## Constraints implemented

- `UNIQUE (ranking_request_hash) WHERE force_replay = false`
- `UNIQUE (retrieval_result_id, id)` on `retrieval_evidence_references`
- Composite FK: `(retrieval_result_id, retrieval_evidence_reference_id)` → `retrieval_evidence_references (retrieval_result_id, id)`
- `UNIQUE (ranking_result_id, presentation_order_index)`
- `UNIQUE (ranking_result_id, retrieval_evidence_reference_id)`
- CHECK `ranking_profile`, `ranking_status`, `error_category` (canonical vocabulary)
- Zero-result: `ranking_status=completed`, `rank_count=0`, no ranked rows — not an error

## Identity

```text
ranking_request_hash = SHA-256(canonical_json({
  retrieval_result_id,
  ranking_profile,
  contract_version
}))
```

Contract generation: `008B-v2`.

### Force replay (DEC-011)

- Default (`force_replay = false`): hash envelope is `{retrieval_result_id, ranking_profile, contract_version}` only.
- Replay (`force_replay = true`): hash payload may include `replay_nonce` (or equivalent entropy) for an additional append-only request row.
- Replay entropy does not change ranking determinism, output, permutation/prerequisite validation, pure-pointer shape, or provenance-once doctrine.
- Default de-duplication: partial unique index `UNIQUE (ranking_request_hash) WHERE force_replay = false`.

Claude review F-10 closed in [`DECISION_LOG.md`](../DECISION_LOG.md) DEC-011.

## Explicit prohibitions (unchanged)

- No ranking execution logic
- No ranking worker (008D)
- No semantic/AI ranking
- No answer or legal conclusion fields
- No copied provenance on ranked rows
- No concurrent ranking workers
- No API endpoints

## Next gate

**TASK-008D** — ranking worker/execution — **NOT AUTHORIZED**.

---

END OF TASK-008C
