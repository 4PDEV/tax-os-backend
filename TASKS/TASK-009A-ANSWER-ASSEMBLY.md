# TASK-009A — Answer Assembly Pre-Authorization

## Status

**TASK-009A-PREAUTH** — governance contract delivered; **implementation NOT AUTHORIZED**.

| Phase | Status |
|-------|--------|
| Ranking layer review (008A+) | **Complete** / **ACCEPTED** |
| TASK-009A-PREAUTH | **Accepted** — DEC-013 |
| TASK-009A-IMPL-AUTH | **Complete** — DEC-014 — [`TASKS/TASK-009A-IMPLEMENTATION-AUTHORIZATION.md`](TASK-009A-IMPLEMENTATION-AUTHORIZATION.md) |
| TASK-009A implementation | **NOT AUTHORIZED** |
| Answer persistence (009B+) | **NOT AUTHORIZED** |
| Answer worker (009C+) | **NOT AUTHORIZED** |

## Prerequisite chain

```text
007A–007E Retrieval (complete)
  → 008B Contract → 008C Persistence → 008D Execution → U-01 Worker (complete)
  → 008A+ Ranking Layer Review (accepted)
  → 009A-PREAUTH (this contract)
  → [Claude review — pending]
  → 009A-IMPL-AUTH — NOT STARTED
  → 009A Implementation — NOT AUTHORIZED
```

## Important

- **Does NOT implement** answer services, workers, APIs, persistence, models, migrations, or tests
- **Does NOT authorize** AI answer generation, semantic/vector ranking, retrieval re-selection, or legal conclusions
- **Does NOT modify** retrieval layer (007A–007E) or ranking layer (008B–008D, U-01)

## Objective

Establish the governed answer assembly contract — source-referenced answer package construction from completed ranking output and retrieval provenance — preserving `ranking ≠ answer`, `answer ≠ legal conclusion`, and provenance-once (DEC-010).

## Canonical artifacts

| Artifact | Path |
|----------|------|
| Primary contract | [`ANSWER_ASSEMBLY_CONTRACT.md`](../ANSWER_ASSEMBLY_CONTRACT.md) |
| Ranking runtime (upstream) | [`RANKING_RUNTIME_CONTRACT.md`](../RANKING_RUNTIME_CONTRACT.md) (008B-v2) |
| Ranking execution (upstream) | [`RANKING_EXECUTION_CONTRACT.md`](../RANKING_EXECUTION_CONTRACT.md) |
| Ranking layer review | [`TASKS/RANKING-LAYER-REVIEW.md`](RANKING-LAYER-REVIEW.md) |
| Citation governance (upstream) | [`CITATION_ASSEMBLY_CONTRACT.md`](../CITATION_ASSEMBLY_CONTRACT.md) |
| Decision locks | [`DECISION_LOG.md`](../DECISION_LOG.md) — DEC-001, DEC-002, DEC-010, DEC-013, OD-021 |

## Scope delivered (009A-PREAUTH governance)

1. **Answer layer boundary** — inputs (completed ranking + ranked evidence + provenance reads); outputs (`AnswerPackage`); no retrieval, no ranking
2. **Evidence usage rules** — E-01–E-08; ranked-evidence-only; no bypass, invention, or silent omission
3. **Provenance rules** — DEC-010 preserved; read via joins; no duplication on answer-owned storage
4. **Citation assembly rules** — reference construction model; ordering; no citation creation
5. **Answer structure** — `AnswerPackage`, `AnswerEvidenceEntry`, `CitationReference`, `UncertaintyFlag` (009A-v1)
6. **Failure model** — 10 canonical answer error categories; ranking errors not reused
7. **Layer separation** — retrieval / ranking / answer responsibilities defined
8. **AI boundary** — explicit prohibitions; governance-defined AI deferred
9. **Readiness criteria** — implementation authorization gates (G-01–G-05, D-01–D-10)
10. **Ranking result resolution** — accepted vs terminal `ranking_result` rule (closes RL-O-01)

## Planned deliverables (not started — requires authorization)

| Area | Artifact (future) |
|------|-------------------|
| Implementation authorization | `TASKS/TASK-009A-IMPLEMENTATION-AUTHORIZATION.md` |
| Assembly service | `answer_assembly/` — package builder, validation, provenance reads |
| Persistence (if authorized) | `answer_persistence/` — append-only lifecycle |
| Worker skeleton | `workers/answer_runtime/` — orchestration only (OD-021) |
| Tests | Evidence rules, provenance joins, import guards, ranking handoff |
| Layer review | Answer layer review package (post-implementation) |

## Explicit prohibitions (unchanged)

- No migrations, ORM changes, workers, services, APIs, or tests in this task
- No semantic/vector/AI ranking or retrieval re-selection
- No answer narrative generation or legal conclusions
- No citation creation during answer assembly
- No concurrent answer workers
- No modification of retrieval or ranking layers

## Acceptance criteria (009A-PREAUTH)

- [x] Answer assembly contract document exists
- [x] Answer layer boundary defined (consumes ranking; no retrieval/ranking)
- [x] Evidence usage rules E-01–E-08 encoded
- [x] Provenance rules preserve DEC-010
- [x] Citation assembly rules defined (governance only)
- [x] AnswerPackage structure defined (009A-v1)
- [x] Canonical answer error vocabulary distinct from ranking
- [x] Layer separation documented
- [x] AI boundary explicit
- [x] Implementation readiness criteria defined
- [x] RL-O-01 ranking result resolution rule documented
- [x] DEC-013 locked
- [x] No implementation introduced

## Pre-auth verdict

**COMPLETE** — governance contract delivered.

**Implementation:** **NOT AUTHORIZED**.

**Reviewer gate:** Claude acceptance of 009A-PREAUTH pending before implementation authorization package.

## Next gates (not authorized)

| Task | Scope |
|------|--------|
| **Claude review** | 009A-PREAUTH contract acceptance |
| **009A-IMPL-AUTH** | Implementation design package |
| **009A** | Answer assembly implementation |
| **Answer layer review** | End-to-end gate after implementation |
| **Response runtime** | Downstream — not authorized |

## Open questions (for implementation authorization)

| ID | Question | Owner |
|----|----------|-------|
| OQ-01 | Answer persistence | **CLOSED** — Option A ephemeral (DEC-014); Option B → TASK-009B |
| OQ-02 | Narrative `answer_text` | **Open** — not in 009A-v1 |
| OQ-03 | Citation rendering | **CLOSED** — `CitationFormatter` yes; `CitationAssembler` no (DEC-014) |
| OQ-04 | Response runtime handoff: separate pre-auth before public API? | Governance |
| OQ-05 | Zero-evidence answer package: empty `evidence_entries` + informational `zero_evidence` uncertainty flag? | Implementation auth |
| OQ-06 | Citation-required vs citation-optional assembly modes per jurisdiction? | Governance |

---

END OF TASK-009A (pre-auth governance — implementation not authorized)
