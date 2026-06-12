# TASK-009B — Answer Persistence Pre-Authorization

## Status

**TASK-009B** — **COMPLETE** / **ACCEPTED** — tag `v0.1.9-answer-persistence`.

| Phase | Status |
|-------|--------|
| TASK-009A answer assembly | **COMPLETE** / **ACCEPTED** — `v0.1.8-answer-assembly` |
| Answer layer review (009A+) | **ACCEPTED** |
| TASK-009B-PREAUTH (this document) | **ACCEPTED** — DEC-015 |
| TASK-009B-IMPL-AUTH | **ACCEPTED** — DEC-016 — [`TASK-009B-IMPLEMENTATION-AUTHORIZATION.md`](TASK-009B-IMPLEMENTATION-AUTHORIZATION.md) |
| TASK-009B persistence implementation | **COMPLETE** |

## Prerequisite chain

```text
009A-PREAUTH → 009A-IMPL-AUTH → 009A assembly (complete)
  → 009A+ Answer layer review (accepted)
  → 009B-PREAUTH (this contract)
  → [Claude review — pending]
  → 009B-IMPL-AUTH — NOT STARTED
  → 009B persistence — NOT AUTHORIZED
```

## Important

- **Does NOT implement** migrations, ORM models, persistence services, workers, APIs, or tests
- **Does NOT modify** 009A `answer_assembly` assembly logic (except future orchestration hook when 009B authorized)
- **Does NOT authorize** answer worker, response runtime, narrative `answer_text`, or AI generation

## Objective

Establish the governed answer persistence contract — append-only lifecycle for answer assembly outcomes — preserving DEC-010 provenance-once, DEC-011 replay semantics, DEC-013/014 answer boundaries, and RL-O-01 ranking resolution.

## Canonical artifacts

| Artifact | Path |
|----------|------|
| Primary contract | [`ANSWER_PERSISTENCE_CONTRACT.md`](../ANSWER_PERSISTENCE_CONTRACT.md) |
| Answer assembly (upstream) | [`ANSWER_ASSEMBLY_CONTRACT.md`](../ANSWER_ASSEMBLY_CONTRACT.md) |
| Answer layer review | [`TASKS/ANSWER-LAYER-REVIEW.md`](ANSWER-LAYER-REVIEW.md) |
| Ranking persistence pattern | [`TASKS/TASK-008C-RANKING-PERSISTENCE.md`](TASK-008C-RANKING-PERSISTENCE.md) |
| Decision locks | [`DECISION_LOG.md`](../DECISION_LOG.md) — DEC-010 through DEC-015 |

## Governance decisions delivered

### 1. Persistence model

**Recommendation: Option B — append-only answer persistence.**

Option A (ephemeral only) remains closed at 009A (DEC-014). Option B adds audit lifecycle without replacing `assemble_answer_package`.

### 2. Lifecycle model

```text
answer_requests → answer_results (accepted) → assembly → answer_evidence_entries + answer_uncertainty_flags → answer_results (completed | failed)
```

Statuses: `pending`, `accepted`, `completed`, `failed`, `skipped`, `duplicate_rejected`.

### 3. Identity / idempotency

```text
answer_request_hash = SHA-256({
  ranking_request_id,
  contract_version,           // 009B-v1
  assembly_contract_version,  // 009A-v1
  include_rendered_citation_text
})
```

DEC-011 pattern: `force_replay` + `replay_nonce`; partial unique index where `force_replay=false`.

### 4. Upstream resolution (RL-O-01)

`ranking_request_id` required on `answer_requests`. Persist `accepted_ranking_result_id` + `terminal_ranking_result_id` on results for audit. Assembly resolution unchanged from 009A.

### 5. Provenance protection

**Pure-pointer `answer_evidence_entries`** — pointers to `ranked_evidence_reference_id` + `retrieval_evidence_reference_id` + `presentation_order_index` only. **No** `legal_object_id`, `citation_id`, `citation_hash`, or provenance field copies.

### 6. Citation persistence

**Neither** `citation_id` **nor** `rendered_citation_text` on persisted rows. Read-time `CitationFormatter` only (OQ-03 carry-forward).

### 7. Uncertainty persistence

**Yes** — `answer_uncertainty_flags` append-only child rows; `zero_evidence` required for rank_count=0 completions.

### 8. Failure model

Reuse 009A assembly categories on `answer_results`. Add persistence-specific: `duplicate_answer`, `ranking_request_missing`, `invalid_answer_request`.

### 9. Worker boundary

**Deferred** — U-02 / TASK-009C future skeleton; not in 009B scope.

### 10. API boundary

Response runtime and public APIs **NOT AUTHORIZED**. Persistence ≠ response delivery.

### 11. Zero-evidence

`completed`, `rank_count=0`, no evidence rows, `zero_evidence` uncertainty flag.

### 12. Readiness criteria

G-01–G-03 met; G-04 Claude review pending; G-05 009B-IMPL-AUTH not started.

## Scope delivered (009B-PREAUTH governance)

- [x] Persistence model recommendation (Option B)
- [x] Lifecycle tables and status vocabulary
- [x] `answer_request_hash` + DEC-011 replay
- [x] RL-O-01 upstream resolution authority
- [x] Pure-pointer provenance doctrine (DEC-010)
- [x] Citation non-persistence decision
- [x] Uncertainty flag schema
- [x] Failure model (assembly + persistence categories)
- [x] Worker / API deferral
- [x] Zero-evidence path
- [x] G-01–G-05 readiness criteria
- [x] DEC-015 locked
- [x] No implementation introduced

## Planned deliverables (not started — requires authorization)

| Area | Artifact (future) |
|------|-------------------|
| Implementation authorization | `TASKS/TASK-009B-IMPLEMENTATION-AUTHORIZATION.md` |
| Migration | `answer_requests`, `answer_results`, `answer_evidence_entries`, `answer_uncertainty_flags` |
| Service | `answer_persistence/` — `create_*` only |
| Tests | Pure-pointer guards, hash idempotency, RL-O-01, zero-evidence |
| Orchestration hook | Optional thin wrapper calling assembly + persistence (009B-IMPL-AUTH scope) |

## Explicit prohibitions (unchanged)

- No migrations, ORM, services, workers, APIs, tests in this task
- No provenance duplication, citation persistence, `answer_text`, legal conclusions
- No AI, semantic/vector, `CitationAssembler`, concurrent workers
- No modification of ranking or retrieval layers

## Acceptance criteria (009B-PREAUTH)

- [x] Answer persistence contract document exists
- [x] Option B recommended with rationale
- [x] Lifecycle model defined
- [x] Hash/idempotency aligned to DEC-011
- [x] RL-O-01 preserved
- [x] Pure-pointer evidence doctrine defined
- [x] Citation/uncertainty persistence decisions documented
- [x] Failure vocabulary defined
- [x] Worker/API boundaries deferred
- [x] Zero-evidence path documented
- [x] Readiness criteria G-01–G-05 documented
- [x] DEC-015 locked

## Pre-auth verdict

**COMPLETE WITH OPEN QUESTIONS** — governance contract delivered; Claude review pending.

**Implementation:** **NOT AUTHORIZED**.

## Open questions

| ID | Question | Disposition |
|----|----------|-------------|
| OQ-B-01 | Orchestration order: persist-then-assemble vs assemble-then-persist? | **Recommend assemble-then-persist** on success — 009B-IMPL-AUTH |
| OQ-B-02 | Composite FK to `ranked_evidence_references` via `(ranking_request_id, id)`? | **Recommend yes** — 009B-IMPL-AUTH migration design |
| OQ-B-03 | `related_evidence_ids` as JSONB vs join table for uncertainty flags? | **Recommend single nullable FK** per flag for v1; JSONB deferred |
| OQ-B-04 | Answer worker task ID: U-02 vs TASK-009C? | **Deferred** — name at worker authorization |
| OQ-B-05 | Read API surface in 009B or separate API task? | **Recommend read-only list/get in 009B service only** — no HTTP |

## Next gates (not authorized)

| Task | Scope |
|------|--------|
| **Claude review** | 009B-PREAUTH contract acceptance |
| **009B-IMPL-AUTH** | Implementation design package |
| **009B** | Answer persistence implementation |
| **Answer worker** | Orchestration skeleton |
| **Response runtime** | Downstream — not authorized |

---

END OF TASK-009B (pre-auth governance — implementation not authorized)
