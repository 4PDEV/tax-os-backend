# TASK-007C1 — Retrieval Persistence Remediation Package

## Status

**Complete** — governance-only remediation package delivered; **awaiting acceptance review** before TASK-007C authorization.

## Important

- **Does NOT implement TASK-007C**
- **TASK-007C remains NOT AUTHORIZED**
- No tables, migrations, models, services, workers, or APIs

## Objective

Close blocking **007C** pre-auth findings **RP-01 through RP-06** (and recommended RP-05, RP-07, RP-08) at the governance level.

## Source review

[`ARCHITECTURE_REVIEW_RETRIEVAL_PERSISTENCE_007C-PREAUTH.md`](../ARCHITECTURE_REVIEW_RETRIEVAL_PERSISTENCE_007C-PREAUTH.md) — **APPROVED WITH REQUIRED REMEDIATION BEFORE TASK-007C**

| Finding | Status after 007C1 |
|---------|-------------------|
| RP-01 HIGH — request_hash canonicalization | **Remediated (spec)** |
| RP-02 HIGH — evidence FK constraints | **Remediated (spec)** |
| RP-03 HIGH — citation consistency | **Remediated (spec)** |
| RP-04 MEDIUM — CHECK constraints | **Remediated (spec)** |
| RP-05 MEDIUM — order index | **Remediated (spec)** |
| RP-06 HIGH — metadata whitelist | **Remediated (spec)** |
| RP-07 LOW — zero-result semantics | **Remediated (spec)** |
| RP-08 LOW — prohibited-field tests | **Remediated (spec)** |

## Canonical artifacts

| Artifact | Path |
|----------|------|
| Remediation specification | [`RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md`](../RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md) |
| Pre-auth review | [`ARCHITECTURE_REVIEW_RETRIEVAL_PERSISTENCE_007C-PREAUTH.md`](../ARCHITECTURE_REVIEW_RETRIEVAL_PERSISTENCE_007C-PREAUTH.md) |
| Runtime contract | [`RETRIEVAL_RUNTIME_CONTRACT.md`](../RETRIEVAL_RUNTIME_CONTRACT.md) |
| Task record | `TASKS/TASK-007C1-RETRIEVAL-PERSISTENCE-REMEDIATION.md` |

## Explicit prohibitions

- no Alembic migrations
- no ORM models
- no retrieval services or workers
- no modification of TASK-004A
- no ranking, answers, or AI search

## Acceptance criteria

- [x] Remediation package exists
- [x] RP-01 through RP-06 addressed
- [x] RP-05, RP-07, RP-08 included
- [x] Planned schema documented
- [x] Governance docs updated
- [x] No implementation introduced
- [x] TASK-007C remains NOT AUTHORIZED

## Next gate

**Remediation acceptance review** for 007C1 — then bounded TASK-007C authorization.

---

END OF TASK-007C1
