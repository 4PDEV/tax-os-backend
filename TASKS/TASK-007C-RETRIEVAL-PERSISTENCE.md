# TASK-007C — Retrieval Persistence

## Status

**Authorized for implementation** — persistence-only scope per [`RETRIEVAL_PERSISTENCE_007C1_ACCEPTANCE_REVIEW.md`](../RETRIEVAL_PERSISTENCE_007C1_ACCEPTANCE_REVIEW.md).

## Prerequisite chain

```text
007A Review → 007A1 Remediation → 007A1 Acceptance
  → 007B Contract → 007C Pre-Auth → 007C1 Remediation → 007C1 Acceptance
  → 007C Persistence (this task)
```

## Objective

Implement durable append-only persistence for retrieval governance requests, results, and evidence references per [`RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md`](../RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md).

## Authorized scope

| Area | Requirement |
|------|-------------|
| Tables | `retrieval_requests`, `retrieval_results`, `retrieval_evidence_references` |
| Migration | Alembic — FKs, CHECK constraints, partial unique, order uniqueness |
| Models | `RetrievalRequest`, `RetrievalResult`, `RetrievalEvidenceReference` |
| Service | Request hash canonicalization, metadata whitelist validator, citation consistency validation |
| Tests | Migration tests, persistence tests, RP-08 prohibited-field guards |

## Mandatory constraints

- `request_hash = SHA-256(canonical_json(normalized_retrieval_envelope))`
- Partial unique: `request_hash` WHERE `force_replay = false`
- `UNIQUE(retrieval_result_id, deterministic_order_index)`
- FKs: `legal_objects`, `legal_object_versions`, `source_versions`, `citations` (nullable)
- Append-only — no updates, no hard deletes
- Citation mismatch → `failed` / `provenance_incomplete` — never silent drop/substitution
- Metadata whitelist only — reject unknown and prohibited keys
- OD-021: single-worker only

## Explicit prohibitions

- Retrieval workers or execution (007D)
- Ranking, answers, AI retrieval
- Semantic / vector search
- API routes
- Modification of TASK-004A
- Concurrent retrieval workers

## Not delivered (by design)

- Retrieval runtime execution
- Answer assembly
- Ranking scores or relevance semantics

## Next

TASK-007D retrieval worker/execution — separate task + review gate (not authorized).

---

END OF TASK-007C
