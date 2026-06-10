# TASK-008D — Ranking Execution

## Status

**TASK-008D-PREAUTH** — governance contract delivered; **implementation NOT AUTHORIZED**.

| Phase | Status |
|-------|--------|
| TASK-008D-PREAUTH | **Complete** — execution contract envelope |
| TASK-008D implementation | **NOT AUTHORIZED** |

## Prerequisite chain

```text
008B Contract → 008C-REMEDIATION → 008C-PREAUTH → 008C Persistence (complete)
  → 008D-PREAUTH (this contract)
  → 008D Controlled Execution — NOT AUTHORIZED
  → Ranking Layer Review
  → 009A Answer Assembly — NOT AUTHORIZED
```

## Important

- **Does NOT implement** ranking worker, execution services, APIs, migrations, models, or tests
- **Does NOT authorize** answer runtime (009A), AI/semantic/vector ranking, or concurrent workers
- **Does NOT modify** retrieval layer (007A–007E) or ranking persistence schema (008C)

## Objective

Establish the governed ranking execution contract — deterministic mechanical permutation over completed retrieval evidence — preserving `retrieval result ≠ ranking`, `ranking ≠ answer`, and provenance-once (DEC-010).

## Canonical artifacts

| Artifact | Path |
|----------|------|
| Primary contract | [`RANKING_EXECUTION_CONTRACT.md`](../RANKING_EXECUTION_CONTRACT.md) |
| Runtime contract (upstream) | [`RANKING_RUNTIME_CONTRACT.md`](../RANKING_RUNTIME_CONTRACT.md) (008B-v2) |
| Persistence (upstream) | [`TASKS/TASK-008C-RANKING-PERSISTENCE.md`](TASK-008C-RANKING-PERSISTENCE.md) |
| Decision locks | [`DECISION_LOG.md`](../DECISION_LOG.md) — DEC-010, DEC-011, DEC-012 |
| Execution pattern reference | [`TASKS/TASK-007E-CONTROLLED-RETRIEVAL-EXECUTION.md`](TASK-007E-CONTROLLED-RETRIEVAL-EXECUTION.md) |

## Scope delivered (008D-PREAUTH governance)

1. **Deterministic execution invariants** — same inputs + profile → same permutation
2. **Permutation integrity invariants** — identical multiset in/out; pre-persist validation
3. **Zero-evidence execution path** — `completed`, `rank_count=0`; no `evidence_set_empty`
4. **Ranking profile governance** — closed enum; mechanical sort only
5. **Canonical execution error vocabulary** — 9 categories; prohibited legacy terms
6. **Ranking execution lifecycle** — `accepted` → execute → `completed` \| `failed`; append-only
7. **Single-worker doctrine** — OD-021; concurrent workers not authorized
8. **Explicit prohibitions** — AI, semantic, vector, answer, legal conclusions, APIs, workers

## Planned deliverables (not started — requires authorization)

| Area | Artifact (future) |
|------|-------------------|
| Execution service | `ranking_execution/` — profile permuters, validation, orchestration |
| Controlled provider | `workers/ranking_runtime/controlled_provider.py` |
| Dry-run skeleton | `workers/ranking_runtime/` — `accepted` → `skipped` |
| Tests | Permutation proofs, zero-result, import guards, profile determinism |
| Docs | Implementation task closure, layer review package |

## Explicit prohibitions (unchanged)

- No migrations, ORM changes, workers, services, APIs, or tests in this task
- No semantic/vector/AI ranking
- No answer generation or legal conclusions
- No retrieval re-selection (`retrieval_execution`)
- No concurrent ranking workers
- No runtime-created ranking profiles
- No modification of retrieval or 008C persistence layers

## Acceptance criteria (008D-PREAUTH)

- [x] Execution contract document exists
- [x] Deterministic invariants encoded
- [x] Permutation integrity rules encoded
- [x] Zero-evidence path documented
- [x] Profile governance aligned to 008B-v2
- [x] Canonical error vocabulary aligned to 008C
- [x] Lifecycle pipeline documented
- [x] Single-worker doctrine documented
- [x] Prohibitions and import guards documented
- [x] DEC-012 locked
- [x] No implementation introduced

## Next gates (not authorized)

| Task | Scope |
|------|--------|
| **TASK-008D** | Controlled ranking execution implementation |
| **Ranking layer review** | End-to-end gate after 008D |
| **TASK-009A** | Answer assembly pre-auth |

---

END OF TASK-008D (pre-auth governance — implementation not authorized)
