# Ranking Persistence Remediation — TASK-008C-REMEDIATION

## Purpose

Authoritative reconciliation of [`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md) with provenance-once doctrine before **TASK-008C** ranking persistence implementation.

**This document modifies planned architecture only.** It does not implement persistence, migrations, models, workers, APIs, or ranking execution.

| Item | Status |
|------|--------|
| TASK-008B contract | **Amended** — pure-pointer shape (008B-v2) |
| TASK-008C-REMEDIATION | **Complete** — this document |
| TASK-008C implementation | **NOT AUTHORIZED** until separate gate |

---

## Architectural ruling (locked)

| Doctrine | Rule |
|----------|------|
| Ranking stores order only | `presentation_order_index` — not relevance |
| Provenance lives once | Authoritative in `retrieval_evidence_references` |
| Provenance via join | Ranked rows are pure pointers |

---

## Remediation index

| # | Change | Section | Status |
|---|--------|---------|--------|
| 1 | Remove copied provenance from ranked row contract | §RC-01 | **Applied** |
| 2 | Pure-pointer ranking model | §RC-02 | **Applied** |
| 3 | Structural membership composite FK | §RC-03 | **Applied** |
| 4 | Canonical error vocabulary | §RC-04 | **Applied** |
| 5 | Remove `evidence_set_empty` failure | §RC-05 | **Applied** |
| 6 | Prohibited interpretive fields | §RC-06 | **Applied** |
| 7 | Doctrine section update | §RC-07 | **Applied** |

---

## RC-01 — Remove copied provenance fields

**Removed from `ranked_evidence_references` contract:**

- `legal_object_id`
- `legal_object_version_id`
- `source_version_id`
- `citation_id`
- `citation_hash`

**Reason:** duplicates provenance in `retrieval_evidence_references`; violates RK-07 / provenance-once discipline.

---

## RC-02 — Pure-pointer ranking model

**`ranked_evidence_references` minimum shape:**

| Field | Required |
|-------|----------|
| `ranked_evidence_reference_id` | Yes |
| `ranking_result_id` | Yes |
| `retrieval_result_id` | Yes |
| `retrieval_evidence_reference_id` | Yes |
| `presentation_order_index` | Yes |

Sort-time reads from retrieval evidence for permutation are permitted at execution — **not persisted** on ranked rows.

---

## RC-03 — Structural membership enforcement

**On `retrieval_evidence_references` (008C migration):**

```sql
UNIQUE (retrieval_result_id, id)
```

**On `ranked_evidence_references`:**

```sql
FOREIGN KEY (retrieval_result_id, retrieval_evidence_reference_id)
  REFERENCES retrieval_evidence_references (retrieval_result_id, id)
```

Prevents ranking evidence from a different `retrieval_result_id`.

---

## RC-04 — Canonical error vocabulary

Authoritative `error_category` set:

- `retrieval_result_missing`
- `retrieval_result_not_completed`
- `evidence_reference_missing`
- `provenance_incomplete`
- `profile_not_allowed`
- `duplicate_ranking`
- `permutation_mismatch`
- `ranking_pipeline_unavailable`
- `unknown_failure`

Supersedes: `invalid_request`, `retrieval_not_completed`, `permutation_violation`, `evidence_set_empty`.

---

## RC-05 — Zero-result retrieval

Completed retrieval with `result_count=0`:

- Ranking `status=completed`
- `rank_count=0`
- **Not** a failure

`evidence_set_empty` is **prohibited** as an error category.

---

## RC-06 — Prohibited interpretive fields

Explicitly prohibited on ranking persistence:

- `authority_weight`
- `importance_flag`
- `preference_score`

Plus all score and answer fields in 008B §Prohibited fields.

---

## RC-07 — Doctrine

Contract must encode:

- `retrieval result` ≠ ranking
- `ranking` ≠ answer
- `answer` ≠ legal conclusion
- ranking stores order only
- provenance lives once

---

## Authorization gate (TASK-008C)

TASK-008C may be authorized only after:

1. TASK-008C-REMEDIATION **accepted** — this document
2. Amended [`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md) (008B-v2) reviewed
3. TASK-008C-PREAUTH-RECONCILIATION **complete** — [`TASKS/TASK-008C-PREAUTH-RECONCILIATION.md`](TASKS/TASK-008C-PREAUTH-RECONCILIATION.md)
4. Claude review and/or explicit TASK-008C authorization prompt

---

END OF RANKING PERSISTENCE REMEDIATION 008C-REMEDIATION
