# TASK-009A — Implementation Authorization Package

## Status

**COMPLETE** / **ACCEPTED** — implementation design locked (Claude review accepted).

**TASK-009A implementation remains NOT AUTHORIZED** until explicit bounded implementation authorization prompt.

| Phase | Status |
|-------|--------|
| TASK-009A-PREAUTH | **ACCEPTED** — DEC-013 |
| Ranking layer review (008A+) | **ACCEPTED** |
| TASK-009A-IMPLEMENTATION-AUTHORIZATION (this document) | **COMPLETE** — design package |
| TASK-009A answer assembly code | **NOT AUTHORIZED** |
| TASK-009B answer persistence | **NOT AUTHORIZED** |
| Answer worker skeleton | **NOT AUTHORIZED** (deferred) |

## Accepted baseline

| Item | Value |
|------|--------|
| HEAD | `b417746` (or newer accepted HEAD) |
| Ranking layer | **COMPLETE** — `v0.1.5-ranking-worker-skeleton` |
| TASK-009A-PREAUTH | **ACCEPTED** |
| DEC-010, DEC-011, DEC-012, DEC-013 | **LOCKED** |
| DEC-014 | **LOCKED** (this package — implementation scope) |
| OD-021 | **LOCKED** — single-worker carry-forward |

## Binding upstream artifacts

- [`ANSWER_ASSEMBLY_CONTRACT.md`](../ANSWER_ASSEMBLY_CONTRACT.md) (009A-v1)
- [`TASKS/TASK-009A-ANSWER-ASSEMBLY.md`](TASK-009A-ANSWER-ASSEMBLY.md)
- [`TASKS/RANKING-LAYER-REVIEW.md`](RANKING-LAYER-REVIEW.md) — RL-O-01
- [`RANKING_EXECUTION_CONTRACT.md`](../RANKING_EXECUTION_CONTRACT.md)
- [`CITATION_ASSEMBLY_CONTRACT.md`](../CITATION_ASSEMBLY_CONTRACT.md)
- [`backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md`](../backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md) (004D)
- [`DECISION_LOG.md`](../DECISION_LOG.md)

## Important

This package **does NOT implement** answer assembly services, workers, APIs, persistence, tests, models, migrations, or runtime code.

---

## 1. OQ-01 — Persistence scope (LOCKED)

### Decision: **Option A — Ephemeral `AnswerPackage` only**

**TASK-009A first implementation slice:** in-memory / return-value assembly only. **No** `answer_requests`, **no** `answer_results`, **no** Alembic migrations for answer tables.

### Rationale

| Factor | Option A (chosen) | Option B (deferred) |
|--------|-------------------|---------------------|
| Scope bounding | Proves RL-O-01 resolution and E-01–E-08 without schema commitment | Requires 009B persistence design + migration gate |
| DEC-010 | No answer-owned rows → zero risk of provenance duplication at persistence | Must enforce pure-pointer or reference-only answer rows in 009B |
| Append-only doctrine | Preserved platform-wide; **deferred** to TASK-009B when persistence is authorized | Native fit for audit lifecycle |
| Pattern parity | Ranking had 008C before 008D; answer persistence logically precedes full lifecycle in a **separate** bounded task | Would bundle two layers in one task |
| Test focus | Assembly correctness, import guards, deterministic package shape | Adds idempotency/replay tests prematurely |

### Doctrine preservation

| Doctrine | How Option A preserves it |
|----------|---------------------------|
| **DEC-010 provenance-once** | All provenance read via joins from `retrieval_evidence_references`; nothing authoritative written by answer layer |
| **Append-only** | No answer rows created → no mutation surface; ranking/retrieval append-only rows remain untouched |
| **Source-referenced (DEC-002)** | `AnswerPackage` carries reference IDs only — not authoritative provenance copies |

### Deferred path — Option B (TASK-009B, not authorized)

When explicitly authorized:

```text
answer_requests (append-only intent + answer_request_hash)
  → answer_results (accepted)
  → [assembly]
  → answer_results (completed | failed)
```

- Persisted package snapshot or pointer envelope only — **no** copied provenance columns (DEC-010)
- Full `requested` → `accepted` → `completed` | `failed` persisted lifecycle
- Idempotency / replay doctrine aligned with DEC-011 pattern (separate decision at 009B pre-auth)

**009A must not** introduce persistence “temporarily” — ephemeral only until 009B authorization.

---

## 2. OQ-03 — CitationFormatter authorization (LOCKED)

### Decision: **Read-only `CitationFormatter` permitted** in first implementation slice

**`CitationAssembler` is NOT permitted** in TASK-009A.

### Allowed (009A-v1)

| Capability | Boundary |
|------------|----------|
| `CitationFormatter` | Format **existing** persisted citation text for display when `citation_id` resolves to a `citations` row |
| Input | `citation_id` / `citation_hash` from `retrieval_evidence_reference` (read-only pin) |
| Output | `CitationReference.rendered_citation_text` — labeled stored/rendered text, **not authoritative** |
| Gate | Only when caller sets `include_rendered_citation_text=true` (default `false`) |
| Load path | Read `citations` by `citation_id` — no write, no create |

### Not allowed (009A-v1)

| Capability | Reason |
|------------|--------|
| `CitationAssembler` | Implies governed assembly/review lifecycle — not answer-layer responsibility |
| Citation creation | Prohibited by DEC-013 and citation governance |
| Citation mutation | No updates to `citations` or related canonical rows |
| Citation discovery | No search, candidate generation, or re-resolution of `citation_id` |
| Re-assembly from `legal_object_version` alone | Bypasses persisted citation pin — use retrieval evidence `citation_id` only |
| Fabricated `rendered_citation_text` | When `citation_id` absent → `citation_reference_status=absent`; text remains `null` |

### Formatter invocation rule (locked)

```text
IF retrieval_evidence.citation_id IS NOT NULL
   AND include_rendered_citation_text = true
   AND citations row exists
THEN
   rendered_citation_text = CitationFormatter.format(existing_citation_row)  -- read-only
ELSE
   rendered_citation_text = null
   citation_reference_status = present | absent | incomplete  -- per pin state
```

Missing citation row when `citation_id` present → `citation_reference_status=incomplete`; assembly **continues** (not `citation_reference_incomplete` error) unless future assembly mode requires citation — **009A-v1 mode: citation optional**.

`citation_reference_incomplete` error category reserved for future **citation-required** assembly modes (OQ-06) — **not triggered in 009A-v1**.

---

## 3. RL-O-01 test requirements (LOCKED)

### Mandatory test group: **ranking result resolution**

**Module (planned):** `backend/tests/test_answer_assembly.py`

### Fixtures (minimum)

| Fixture | Purpose |
|---------|---------|
| `completed_ranking_with_ranked_rows` | Full happy path: terminal `completed` + `accepted` + N ranked rows |
| `completed_ranking_zero_evidence` | `rank_count=0`, empty ranked list |
| `terminal_completed_wrong_id_only` | Terminal `ranking_result_id` passed without accepted sibling — must fail |
| `accepted_without_terminal_completed` | In-flight / incomplete lifecycle — must fail |
| `rank_count_mismatch` | Terminal `rank_count=N`, ranked rows ≠ N — must fail |
| `duplicate_accepted_rows` | Two `accepted` results for one request — must fail `assembly_validation_failed` or `accepted_ranking_result_missing` per resolution rule |

### Resolution function under test (locked name)

```text
resolve_ranking_assembly_inputs(session, *, ranking_request_id) -> RankingAssemblyInputs
```

Returns: `terminal_ranking_result`, `accepted_ranking_result`, `ranked_rows` (ordered).

### Acceptance criteria (all required)

| ID | Criterion | Pass condition |
|----|-----------|----------------|
| RL-T-01 | Terminal lookup | Loads exactly one `ranking_result` with `ranking_status=completed` for `ranking_request_id` |
| RL-T-02 | Accepted lookup | Loads exactly one `ranking_result` with `ranking_status=accepted` for same `ranking_request_id` |
| RL-T-03 | Ranked row parent | `list_ranked_evidence_references(ranking_result_id=accepted.id)` — **not** terminal.id |
| RL-T-04 | Order preserved | Ranked rows ordered by `presentation_order_index` ASC |
| RL-T-05 | Count integrity | `len(ranked_rows) == terminal.rank_count` |
| RL-T-06 | Terminal-only ID rejection | Calling assembly with only terminal `ranking_result_id` (no request resolution) **must fail** `accepted_ranking_result_missing` or validation guard |
| RL-T-07 | Package IDs populated | `AnswerPackage.terminal_ranking_result_id` and `accepted_ranking_result_id` both set correctly on success |
| RL-T-08 | Failed ranking rejected | Terminal `ranking_status=failed` → `ranking_result_not_completed` |
| RL-T-09 | Zero evidence | `rank_count=0` → empty `evidence_entries`, optional `zero_evidence` uncertainty flag |
| RL-T-10 | Retrieval scope | Each ranked row `retrieval_result_id` equals `ranking_request.retrieval_result_id` or `retrieval_result_mismatch` |

---

## 4. Answer assembly service boundary

### Service name (locked)

```text
backend/app/services/answer_assembly/
```

### Primary entry (locked name)

```text
assemble_answer_package(session, *, ranking_request_id, contract_version="009A-v1", include_rendered_citation_text=False, ...) -> AnswerAssemblyOutcome
```

### Package modules (implementation phase only — not created by this task)

| Module | Responsibility |
|--------|----------------|
| `assembly.py` | Orchestration — resolve ranking → load evidence → provenance reads → build `AnswerPackage` |
| `validation.py` | RL-O-01 resolution, E-01–E-08 checks, pre-assembly validation |
| `models.py` | In-memory DTOs only (`AnswerPackage`, `AnswerEvidenceEntry`, `AnswerAssemblyOutcome`, `AnswerAssemblyError`) — not ORM |
| `__init__.py` | Public exports |

### Responsibilities (assembly **must**)

1. Resolve ranking inputs per RL-O-01 (§3)
2. Load `retrieval_evidence_references` read-only for each ranked pointer
3. Load permitted provenance joins (`legal_object_version`, `citation`, `source_version`) read-only
4. Optionally invoke `CitationFormatter` per OQ-03 when flag set
5. Build `AnswerPackage` per contract §5 (009A-v1) — references only, no narrative text
6. Emit `UncertaintyFlag` for `zero_evidence` and `incomplete_provenance` when applicable (DEC-005)
7. Map failures to canonical answer `error_category` (§6)
8. Return ephemeral outcome — **no persistence writes**

### Non-responsibilities (assembly **must NOT**)

| Prohibited | Rationale |
|------------|-----------|
| `retrieval_execution` | DEC-013 — retrieval closed |
| `ranking_execution` / ranking writes | DEC-013 — ranking closed |
| `CitationAssembler` | OQ-03 — assembly lifecycle not answer layer |
| Citation creation / mutation | Citation governance |
| AI / semantic / vector services | Not authorized |
| Narrative `answer_text` | Not in 009A-v1 scope |
| Legal conclusions / recommendations | DEC-001, DEC-013 |
| Evidence reordering | E-02 — ranking order only |
| Retrieval bypass | E-03 |
| Persistence writes | OQ-01 Option A |
| HTTP / worker orchestration | Separate future tasks |

---

## 5. Answer lifecycle

### 009A-v1 ephemeral lifecycle (locked)

Persisted `requested` / `accepted` rows **do not exist** in Option A. Lifecycle is **outcome-only**:

```text
assemble_answer_package invoked
  → [validation] pre-assembly gate
  → [assembly] build AnswerPackage
  → AnswerAssemblyOutcome (answer_status = completed | failed)
```

| Phase | Representation | Notes |
|-------|----------------|-------|
| Pre-assembly gate | Internal validation only | Not a persisted status |
| `completed` | `AnswerAssemblyOutcome.answer_status` | `AnswerPackage` returned |
| `failed` | `AnswerAssemblyOutcome.answer_status` | `error_category` + `error_message`; package may be partial-null |
| `skipped` | Reserved | Not used in 009A-v1 (worker dry-run — future) |

### Status transitions (009A-v1)

```text
[invoke] → completed   (validation + assembly succeed)
[invoke] → failed      (any validation/assembly failure)
```

**No** `requested` or `accepted` **persisted** states in 009A.

### Append-only requirements

| Rule | 009A-v1 behaviour |
|------|-------------------|
| No mutation of retrieval rows | Read-only |
| No mutation of ranking rows | Read-only |
| No mutation of citation rows | Read-only |
| No answer persistence | No `answer_*` tables |
| Outcome immutability | Caller receives new outcome object per invocation — no in-place mutation of prior outcomes |

### Future persisted lifecycle (TASK-009B — not authorized)

```text
answer_request (requested)
  → answer_result (accepted)
  → [assembly]
  → answer_result (completed | failed)
```

Mirrors ranking append-only pattern when Option B is authorized.

---

## 6. Failure mapping

**Canonical categories only** — from [`ANSWER_ASSEMBLY_CONTRACT.md`](../ANSWER_ASSEMBLY_CONTRACT.md) §6. **No new categories.**

| Assembly condition | `error_category` |
|--------------------|------------------|
| `ranking_request` not found | `ranking_result_not_completed` |
| No terminal `ranking_result` with `ranking_status=completed` | `ranking_result_not_completed` |
| Terminal `ranking_status` ≠ `completed` | `ranking_result_not_completed` |
| No `accepted` `ranking_result` for request | `accepted_ranking_result_missing` |
| More than one `accepted` result for request | `accepted_ranking_result_missing` |
| `rank_count > 0` and zero ranked rows on accepted result | `ranked_evidence_missing` |
| `len(ranked_rows) != terminal.rank_count` | `evidence_count_mismatch` |
| `legal_object_version` or required join missing | `provenance_chain_incomplete` |
| Ranked row `retrieval_result_id` ≠ request scope | `retrieval_result_mismatch` |
| E-01–E-07 violation (duplicate/missing/extra entries) | `assembly_validation_failed` |
| Citation-required mode with absent pin (future) | `citation_reference_incomplete` — **not used in 009A-v1** |
| DB/session infrastructure fault | `answer_pipeline_unavailable` |
| Unclassified | `unknown_failure` |

### Prohibited mappings

| Do not use | Layer |
|------------|-------|
| `permutation_mismatch`, `duplicate_ranking`, `profile_not_allowed` | Ranking |
| `retrieval_result_not_completed`, `evidence_reference_missing` | Retrieval (orchestration maps to answer categories above) |
| `evidence_set_empty` | Legacy — prohibited |

### Exception type (locked)

```text
AnswerAssemblyError(category: str, message: str)
```

`AnswerAssemblyOutcome` carries `answer_status`, `answer_package` (nullable on failure), `error_category`, `error_message`.

---

## 7. Import boundary guards (D-05)

### Mandatory prohibited imports in `answer_assembly/`

| Prohibited import | Reason |
|-------------------|--------|
| `app.services.retrieval_execution` | No retrieval re-selection |
| `app.services.ranking_execution` | No ranking execution |
| `app.services.ranking_persistence` write paths (`create_*`) | Read APIs only if imported |
| `app.services.ai` | No AI generation |
| `app.services.semantic` | No semantic reasoning |
| `app.services.vector` | No vector search |
| `app.services.citation.assembler` / `CitationAssembler` | OQ-03 |
| Citation creation / mutation modules | No canonical citation changes |
| `app.workers.answer_runtime` | Worker not in 009A scope |
| `app.workers.ranking_runtime` | No ranking orchestration |
| `app.workers.retrieval_runtime` | No retrieval orchestration |

### Permitted imports (read-only)

| Permitted | Usage |
|-----------|-------|
| `app.services.ranking_persistence` — `get_ranking_result`, `list_results_for_request`, `list_ranked_evidence_references` | RL-O-01 resolution |
| `app.services.retrieval_persistence` — `get_result`, `list_evidence_references` | Provenance reads |
| `app.services.citation.formatter` — `CitationFormatter` | OQ-03 optional render |
| `app.models.*` | ORM read via session |
| SQLAlchemy `Session` | Read queries only |

### Test guard (mandatory)

`test_answer_assembly_import_guards` — static scan of `answer_assembly/*.py` for prohibited import prefixes (mirror `test_ranking_worker_skeleton.py`).

---

## 8. Worker model (D-06 / OD-021)

### Locked decision: **Direct service only for TASK-009A**

| Item | 009A | Future |
|------|------|--------|
| Entry point | `assemble_answer_package(session, ...)` | Same — worker delegates |
| Worker skeleton | **NOT AUTHORIZED** in 009A | `backend/app/workers/answer_runtime/` — separate bounded task (e.g. U-02) |
| Concurrent workers | **NOT AUTHORIZED** (OD-021 carry-forward) | Explicit governance gate required |

### OD-021 carry-forward

- No `threading.Lock` required in 009A service (stateless ephemeral assembly)
- When worker is authorized: non-blocking single-worker slot (mirror U-01)
- No queue infrastructure (Celery, Redis, etc.)

Worker task **must** call `assemble_answer_package` — no embedded assembly logic.

---

## 9. AnswerPackage construction rules

### Assembly sequence (locked — no narrative, no `answer_text`)

```text
1. resolve_ranking_assembly_inputs(ranking_request_id)
     → terminal completed result
     → accepted result
     → ranked_rows ordered by presentation_order_index

2. validate_ranking_inputs (RL-T-01–RL-T-10)

3. IF terminal.rank_count == 0:
     → build empty evidence_entries
     → add UncertaintyFlag(flag_type=zero_evidence, severity=informational)
     → GOTO step 7

4. FOR each ranked_row in ranked_rows (in order):
     a. load retrieval_evidence_reference by id (read-only)
     b. verify retrieval_result_id scope
     c. load legal_object_version (read-only)
     d. load source_version (read-only) if needed for validation only
     e. build CitationReference:
          - citation_id, citation_hash from evidence row
          - IF include_rendered_citation_text AND citation_id:
                load citations row → CitationFormatter.format → rendered_citation_text
          - ELSE rendered_citation_text = null
          - set citation_reference_status: present | absent | incomplete
     f. append AnswerEvidenceEntry (presentation_order_index from ranked row)

5. validate_evidence_entries (E-01–E-07):
     - count == len(ranked_rows) == terminal.rank_count
     - order matches presentation_order_index
     - no extra/missing retrieval_evidence_reference_id values

6. generate_uncertainty_flags:
     - zero_evidence (if rank_count=0) — step 3
     - incomplete_provenance per entry when join incomplete (warning)
     - conflict/ambiguity: reserved — not inferred in 009A-v1

7. build AnswerPackage:
     - contract_version = "009A-v1"
     - ranking_request_id, retrieval_result_id
     - terminal_ranking_result_id, accepted_ranking_result_id
     - ranking_profile (read from ranking_request)
     - rank_count, evidence_entries, uncertainty_flags
     - assembly_metadata.assembly_mode = "deterministic"
     - answer_status = completed

8. return AnswerAssemblyOutcome(answer_status=completed, answer_package=...)
```

On any validation failure after step 1: `answer_status=failed` with mapped `error_category`.

**Prohibited in sequence:** narrative generation, `answer_text`, reordering, filtering, AI calls.

---

## 10. Implementation test plan (design only)

**Planned test module:** `backend/tests/test_answer_assembly.py`

**No tests implemented by this authorization package.**

### Required test groups

| Group | Key assertions |
|-------|----------------|
| **RL-O-01 resolution** | RL-T-01–RL-T-10 (§3) |
| **Evidence completeness** | E-01–E-07; one entry per ranked row; order preserved |
| **Provenance read-only** | No `session.add`/`flush` on retrieval/ranking/citation models during assembly; join reads only |
| **Citation rendering boundary** | Formatter called only when flag true + `citation_id` present; no `CitationAssembler`; absent citation → null text |
| **Failure mappings** | Each canonical `error_category` triggered by fixture; prohibited categories never emitted |
| **Import guards** | Prohibited prefixes absent in `answer_assembly/` |
| **Zero-evidence package** | `rank_count=0`; empty entries; `zero_evidence` flag |
| **Deterministic assembly** | Same `ranking_request_id` + flags → identical `AnswerPackage` structure (IDs except `answer_package_id`, `assembled_at`) |
| **Append-only lifecycle** | **N/A for 009A** (Option A) — verify **no** answer persistence imports/writes; deferred to 009B |
| **No ranking/retrieval writes** | Patch/monitor ranking_persistence `create_*` — must not be called |

### Supplementary tests (recommended)

- Golden `AnswerPackage` JSON envelope for stable regression
- `citation_reference_status` tristate coverage
- Multiple ranked rows with mixed citation presence

---

## 11. Explicit non-authorization

The following remain **NOT AUTHORIZED** after this package (until separate explicit gates):

| Capability | Status |
|------------|--------|
| Narrative `answer_text` | **NOT AUTHORIZED** |
| Legal conclusions | **NOT AUTHORIZED** |
| Recommendations / tax advice | **NOT AUTHORIZED** |
| AI answer generation | **NOT AUTHORIZED** |
| Semantic reasoning | **NOT AUTHORIZED** |
| Citation creation | **NOT AUTHORIZED** |
| `CitationAssembler` in answer path | **NOT AUTHORIZED** |
| Retrieval re-selection | **NOT AUTHORIZED** |
| Ranking execution / reordering | **NOT AUTHORIZED** |
| Public APIs | **NOT AUTHORIZED** |
| Response runtime | **NOT AUTHORIZED** |
| Answer persistence (Option B) | **NOT AUTHORIZED** — TASK-009B |
| Answer worker skeleton | **NOT AUTHORIZED** |
| Concurrent answer workers | **NOT AUTHORIZED** (OD-021) |
| Queue infrastructure | **NOT AUTHORIZED** |

---

## Explicit prohibitions (this task)

- No `answer_assembly` service code
- No answer worker code
- No API endpoints
- No persistence, migrations, ORM models for answers
- No tests

---

## Authorization checklist (for future acceptance prompt)

- [ ] Architect accepts §1–§11 as implementation boundary
- [ ] Claude review of this package (recommended)
- [ ] Explicit prompt: **AUTHORIZED FOR LIMITED IMPLEMENTATION**
- [ ] Scope: `answer_assembly` service + tests only (ephemeral Option A; no worker; no persistence)

---

## Unresolved questions

| # | Question | Disposition |
|---|----------|-------------|
| U-01 | TASK-009B timing for Option B persistence | **Deferred** — separate pre-auth after 009A accepted |
| U-02 | `citation_reference_incomplete` as hard failure vs warning | **Deferred** — 009A-v1 citation optional; OQ-06 jurisdiction modes |
| U-03 | `conflict` / `ambiguity` uncertainty flag automation | **Deferred** — 009A-v1 manual structural flags only (`zero_evidence`, `incomplete_provenance`) |
| U-04 | Answer worker skeleton task ID (U-02 vs 009C) | **Deferred** — name at worker authorization |
| U-05 | Golden fixtures: DB seeds vs static JSON | **Recommend static JSON** for determinism tests |

---

END OF TASK-009A IMPLEMENTATION AUTHORIZATION PACKAGE (implementation NOT AUTHORIZED)
