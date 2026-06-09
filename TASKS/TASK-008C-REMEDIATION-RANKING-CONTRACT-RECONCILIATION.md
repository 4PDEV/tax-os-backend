# TASK-008C-REMEDIATION — Ranking Contract Reconciliation

## Status

**Complete** — governance reconciliation delivered; TASK-008C implementation **not authorized**.

## Important

- **Does NOT implement** TASK-008C persistence, migrations, models, workers, or APIs
- **Does NOT modify** retrieval layer (007A–007E)
- **Amends** TASK-008B contract to pure-pointer ranked row shape (008B-v2)

## Objective

Reconcile accepted TASK-008B with provenance-once architectural ruling before ranking persistence begins.

## Architectural ruling (locked)

Ranking stores order only. Provenance lives once in `retrieval_evidence_references`. Ranked rows are pure pointers.

## Deliverables

| Artifact | Path |
|----------|------|
| Amended contract | [`RANKING_RUNTIME_CONTRACT.md`](../RANKING_RUNTIME_CONTRACT.md) (008B-v2) |
| Remediation spec | [`RANKING_PERSISTENCE_REMEDIATION_008C-REMEDIATION.md`](../RANKING_PERSISTENCE_REMEDIATION_008C-REMEDIATION.md) |
| Updated 008A1 RK-05 | [`RANKING_RUNTIME_REMEDIATION_008A1.md`](../RANKING_RUNTIME_REMEDIATION_008A1.md) |
| Task record | `TASKS/TASK-008C-REMEDIATION-RANKING-CONTRACT-RECONCILIATION.md` |

## Changes applied

1. Removed copied provenance fields from ranked row contract
2. Pure-pointer model: `retrieval_result_id`, `retrieval_evidence_reference_id`, `presentation_order_index`
3. Composite FK structural membership documented
4. Canonical error vocabulary unified
5. `evidence_set_empty` removed — zero-result → `completed`, `rank_count=0`
6. Prohibited: `authority_weight`, `importance_flag`, `preference_score`
7. Doctrine updated: provenance lives once; ranking stores order only

## Acceptance criteria

- [x] 008B contradiction removed
- [x] Pure-pointer architecture documented
- [x] Error vocabulary unified
- [x] `evidence_set_empty` removed
- [x] Prohibited fields documented
- [x] Doctrine updated
- [x] No implementation code introduced
- [x] No migrations created

## Next gate

**TASK-008C** — Ranking Persistence (pre-auth / remediation / implementation — **not authorized** until explicit task).

---

END OF TASK-008C-REMEDIATION
