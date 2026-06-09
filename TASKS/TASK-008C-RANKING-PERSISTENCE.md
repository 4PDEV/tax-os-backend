# TASK-008C — Ranking Persistence

## Status

**NOT AUTHORIZED** — awaiting explicit authorization after TASK-008C-PREAUTH-RECONCILIATION and Claude review.

## Prerequisite chain

```text
008A Review → 008A1 Remediation → 008A1 Acceptance
  → 008B Contract (008B-v2)
  → 008C-REMEDIATION
  → 008C-PREAUTH-RECONCILIATION (complete)
  → 008C Persistence (this task) — NOT AUTHORIZED
```

## Binding contract (when authorized)

Implementation must conform to:

- [`RANKING_RUNTIME_CONTRACT.md`](../RANKING_RUNTIME_CONTRACT.md) — §Persistence doctrine, pure-pointer shape, FK targets
- [`RANKING_PERSISTENCE_REMEDIATION_008C-REMEDIATION.md`](../RANKING_PERSISTENCE_REMEDIATION_008C-REMEDIATION.md)
- [`TASKS/TASK-008C-PREAUTH-RECONCILIATION.md`](TASK-008C-PREAUTH-RECONCILIATION.md)

## Planned deliverables (not started)

| Area | Artifact |
|------|----------|
| Migration | `ranking_requests`, `ranking_results`, `ranked_evidence_references` |
| Models | Append-only ORM aligned to pure-pointer shape |
| Service | `ranking_persistence` — lifecycle only, no execution |
| Tests | Schema guards, prohibited-field scans, FK/composite membership |

## Explicit prohibitions until authorized

- No migrations, models, services, workers, APIs
- No ranking execution
- No copied provenance on ranked rows
- No score or answer fields

---

END OF TASK-008C (placeholder — not authorized)
