# Answer Persistence Review (TASK-009B+)

**Review type:** Governance review only — no implementation  
**Date:** 2026-06-02  
**Baseline:** `86076ab` · tag `v0.1.9-answer-persistence`  
**Scope:** Answer persistence migration, ORM, `answer_persistence` service, tests, interaction with 009A assembly  
**Locked decisions:** DEC-010, DEC-011, DEC-012, DEC-013, DEC-014, DEC-015, DEC-016, OD-021  
**Verdict:** **ACCEPTED WITH REMEDIATION** (non-blocking test hygiene)

---

## Executive summary

TASK-009B answer persistence is **accepted as a governed append-only platform layer**. The migration, ORM models, and `answer_persistence` service implement DEC-015/DEC-016 faithfully: four authorized tables, pure-pointer evidence rows, Option A lifecycle orchestration, DEC-011 replay semantics, V-B-02 ranked membership validation, and delegation to `assemble_answer_package` without duplicating RL-O-01 or E-01–E-07 logic.

**All 009B-specific tests pass** (33/33 with `TEST_DATABASE_URL`). Reported failures in the combined 5-file integration suite are **not caused by 009B schema or service defects** — they stem from pre-existing test assertion patterns and shared seed-helper isolation (`countries` duplicate on multi-evidence fixtures). Remediation is recommended before CI hardening but **does not block TASK-009C-PREAUTH**.

**End-to-end chain (persistence slice):**

```text
ranking_request (completed lifecycle)
  → persist_answer_for_ranking_request()
  → answer_request → answer_result(accepted)
  → assemble_answer_package() [009A read-only]
  → answer_evidence_entries + answer_uncertainty_flags
  → answer_result(completed | failed | duplicate_rejected)
```

**Mandatory doctrines enforced:**

| Boundary | Status |
|----------|--------|
| Provenance lives once (DEC-010) | **PASS** — composite FK + pure-pointer columns |
| Append-only (DEC-015) | **PASS** — no `update_*` / `delete_*` |
| Replay semantics (DEC-011) | **PASS** — hash payload + partial unique index |
| 009A preserved (DEC-014) | **PASS** — ephemeral assembly unchanged |
| Ranking ≠ answer persistence | **PASS** — no ranking execution imports |
| Answer ≠ legal conclusion | **PASS** — no narrative or conclusion fields |

**Result:** Answer persistence layer **COMPLETE** (009B). **TASK-009C-PREAUTH** (answer worker governance) **may proceed** — implementation remains **NOT AUTHORIZED**.

---

## Layer status (canonical)

| Layer | Task(s) | Status |
|-------|---------|--------|
| Answer assembly | 009A | **COMPLETE** / **ACCEPTED** — `v0.1.8` |
| Answer persistence pre-auth | 009B-PREAUTH | **ACCEPTED** — DEC-015 |
| Answer persistence impl auth | 009B-IMPL-AUTH | **ACCEPTED** — DEC-016 |
| Answer persistence | 009B | **COMPLETE** / **ACCEPTED** — `86076ab`, `v0.1.9` |
| **Answer persistence review** | 009B+ | **CLOSED** — **ACCEPTED WITH REMEDIATION** |
| Answer worker | 009C | **NOT AUTHORIZED** |

---

## Review areas (AP-01 through AP-10)

### AP-01 — Migration correctness

| Check | Evidence | Status |
|-------|----------|--------|
| Four authorized tables only | `c7e3a1f94d82` creates `answer_requests`, `answer_results`, `answer_evidence_entries`, `answer_uncertainty_flags` | **PASS** |
| Ranked UNIQUE prerequisite | `uq_ranked_evidence_result_id_pk` on `ranked_evidence_references` | **PASS** |
| FK constraints | All parent tables: `ranking_requests`, `ranking_results`, `retrieval_results`, `retrieval_evidence_references`, `ranked_evidence_references` | **PASS** |
| UNIQUE on evidence rows | `uq_answer_evidence_result_order`, `_ranked`, `_retrieval` | **PASS** |
| CHECK constraints | Actor type, answer status, error categories, presentation order, uncertainty enums | **PASS** |
| Partial unique hash index | `uq_answer_requests_hash_default` WHERE `force_replay = false` | **PASS** |
| Retrieval composite FK | `fk_answer_evidence_retrieval_composite` | **PASS** |
| Downgrade/upgrade safety | `test_downgrade_removes_and_upgrade_restores_answer_tables` | **PASS** |
| Downgrade drops prerequisite | `uq_ranked_evidence_result_id_pk` dropped with answer tables | **PASS** |

---

### AP-02 — ORM model correctness

| Check | Evidence | Status |
|-------|----------|--------|
| Models match migration columns | Four models in `backend/app/models/answer_*.py` | **PASS** |
| Exported in `models/__init__.py` | `AnswerRequest`, `AnswerResult`, `AnswerEvidenceEntry`, `AnswerUncertaintyFlag` | **PASS** |
| No prohibited fields | `PROHIBITED_TABLE_COLUMNS` tests + schema inspection | **PASS** |
| No `answer_text` / `legal_conclusion` | Absent from all answer tables | **PASS** |
| No citation/provenance duplication on evidence rows | 9 allowed columns only | **PASS** |
| No scoring fields | Absent | **PASS** |

---

### AP-03 — Pure-pointer enforcement

| Check | Evidence | Status |
|-------|----------|--------|
| Evidence rows pointer-only | `ANSWER_EVIDENCE_ALLOWED_COLUMNS` frozen set | **PASS** |
| DEC-010 composite membership | DB composite FK + retrieval scope columns | **PASS** |
| DEC-015 doctrine | No rendered citation / provenance copies persisted | **PASS** |
| V-B-02 service validation | `_validate_ranked_membership_v_b_02()` in `create_answer_evidence_entry` | **PASS** |
| V-B-02 test | `test_v_b_02_ranked_parent_mismatch_rejected` | **PASS** |
| Children on accepted result only | `evidence_must_attach_to_accepted_result` guard | **PASS** |

---

### AP-04 — Lifecycle and transaction behavior

| Check | Evidence | Status |
|-------|----------|--------|
| Option A ordering | `persist_answer_for_ranking_request`: request → accepted → assemble → children → terminal | **PASS** |
| Failed path append-only | `accepted` + terminal `failed`; no children | **PASS** |
| `duplicate_rejected` | Terminal row on existing request; no assembly | **PASS** |
| No partial children on assembly failure | Children loop skipped when `assembly_outcome.failed` | **PASS** |
| No partial children on persist validation failure | Single transaction; unhandled exception rolls back unit | **PASS** |
| No `update_*` / `delete_*` | Static scan + no ORM mutation APIs | **PASS** |
| Explicit `session.commit()` in orchestration | Lines 437, 492, 540 — **by design** per DEC-016 D-03 | **PASS** (see AP-O-02) |

---

### AP-05 — Idempotency and replay

| Check | Evidence | Status |
|-------|----------|--------|
| Hash payload fields | `ranking_request_id`, `contract_version`, `assembly_contract_version`, `include_rendered_citation_text` | **PASS** |
| `force_replay` + `replay_nonce` | Included in payload when `force_replay=true` | **PASS** |
| Partial unique index | Migration + `test_partial_unique_hash_index_exists_at_head` | **PASS** |
| `duplicate_answer` / `duplicate_rejected` | Orchestration path + `test_duplicate_default_request_rejected` | **PASS** |
| In-flight accepted guard (U-B-02) | `_check_duplicate_before_request` + `test_in_flight_accepted_guard` | **PASS** |
| `force_replay` allows second run | `test_force_replay_allows_second_persistence` | **PASS** |

---

### AP-06 — Interaction with 009A

| Check | Evidence | Status |
|-------|----------|--------|
| Delegates assembly | `assemble_answer_package()` called from orchestration only | **PASS** |
| RL-O-01 not duplicated | Uses `resolve_ranking_assembly_inputs()` — same as 009A entry | **PASS** |
| E-01–E-07 not duplicated | Evidence validation remains in 009A `validate_evidence_entries` | **PASS** |
| Ephemeral 009A preserved | `assemble_answer_package` unchanged; callable without persistence | **PASS** |
| No ranking persistence writes from 009B | `test_orchestration_does_not_call_ranking_create_apis` | **PASS** |
| Uncertainty flags from package | Mapped from `AnswerPackage.uncertainty_flags` | **PASS** |

---

### AP-07 — Failure model

| Check | Evidence | Status |
|-------|----------|--------|
| 10 assembly error categories | In `ANSWER_ERROR_CATEGORIES` + migration CHECK | **PASS** |
| 3 persistence-specific categories | `duplicate_answer`, `ranking_request_missing`, `invalid_answer_request` | **PASS** |
| Prohibited ranking categories blocked | `PROHIBITED_ERROR_CATEGORIES` + parametrized test | **PASS** |
| Assembly failures forwarded | `assembly_outcome.error_category` on terminal `failed` row | **PASS** |

**Observation:** `ranking_request_missing` wraps any `resolve_ranking_assembly_inputs` exception — acceptable for v1; assembly categories surface correctly on assembly failure path.

---

### AP-08 — Forbidden capability scan

| Prohibited | Status |
|------------|--------|
| Answer worker / `answer_runtime` | **ABSENT** |
| Response runtime | **ABSENT** |
| Public APIs / FastAPI routes in 009B | **ABSENT** |
| AI / semantic / vector imports | **ABSENT** — `test_answer_persistence_import_guards` |
| `CitationAssembler` | **ABSENT** |
| `answer_text` / legal conclusions / recommendations | **ABSENT** from schema |
| Concurrent workers | **ABSENT** |
| `update_*` / `delete_*` persistence APIs | **ABSENT** |

---

### AP-09 — Test failure analysis

#### 009B tests (authoritative)

| Suite | Result |
|-------|--------|
| `test_answer_persistence.py` + `test_answer_persistence_alembic_migration.py` | **33 passed**, 0 failed (with `TEST_DATABASE_URL`) |

#### Combined 4-file suite (reported regression)

| Suite | Result |
|-------|--------|
| `test_answer_persistence` + `test_answer_persistence_alembic` + `test_answer_assembly` + `test_controlled_ranking_execution` | **65 passed**, **11 failed** |

#### Exact failing tests

| Test | Root cause | Caused by 009B? |
|------|------------|-----------------|
| `test_controlled_ranking_execution::test_duplicate_default_request_rejected` | `pytest.raises(..., match="duplicate_ranking")` matches exception **message**, but `RankingExecutionError` uses message=`duplicate_default_request_for_hash` | **NO** — pre-existing 008D test pattern |
| `test_controlled_ranking_execution::test_in_flight_accepted_guard` | Same category-vs-message match issue | **NO** |
| `test_controlled_ranking_execution::test_retrieval_result_missing` | Match expects `retrieval_result_missing`; message is `retrieval_result not found: …` | **NO** |
| `test_controlled_ranking_execution::test_retrieval_not_completed` | Match expects category; message is `retrieval_status=accepted` | **NO** |
| `test_controlled_ranking_execution::test_profile_not_allowed` | Match expects category; message is `invalid ranking_profile: SEMANTIC_RANK` | **NO** |
| `test_controlled_ranking_execution::test_evidence_count_mismatch` | Match expects `evidence_reference_missing`; message is `evidence_count=0 result_count=2` | **NO** |
| `test_controlled_ranking_execution::test_determinism_same_inputs_same_order` | `countries_code_key` duplicate — `_seed_citation` inserts `RW` per evidence row in multi-evidence fixture | **NO** — pre-existing seed helper |
| `test_answer_assembly::test_rl_t04_presentation_order_preserved` | `countries_code_key` duplicate (multi-evidence) | **NO** |
| `test_answer_assembly::test_rl_t10_retrieval_scope_mismatch_fails` | `countries_code_key` duplicate | **NO** |
| `test_answer_assembly::test_evidence_completeness_one_to_one` | `countries_code_key` duplicate (multi-evidence) | **NO** |
| `test_answer_assembly::test_deterministic_assembly_structure` | `countries_code_key` duplicate (multi-evidence) | **NO** |

#### 009B-adjacent amplification (non-defect)

`persist_answer_for_ranking_request` calls `session.commit()` per DEC-016 D-03. Integration tests using the nested-transaction `db_session` fixture may **commit data outside the per-test savepoint**, amplifying cross-test pollution when 009B orchestration tests precede ranking/assembly tests in the same session. This is **test harness interaction**, not a production lifecycle defect.

#### Remediation recommendation (non-blocking)

| ID | Item | Priority | Gate |
|----|------|----------|------|
| AP-R-01 | Fix `_seed_legal_object_version` / `_seed_citation` to get-or-create `countries` row `RW` | Medium | Before CI full-suite hardening |
| AP-R-02 | Update 008D ranking tests to assert `exc_info.value.category` instead of `match=` on message | Medium | Before CI full-suite hardening |
| AP-R-03 | Document orchestration `commit()` in test guide; consider `persist_answer_for_ranking_request` test helper with rollback wrapper or dedicated DB session | Low | Optional |
| AP-R-04 | Run 009B closeout CI with isolated `taxos_test` + `TEST_DATABASE_URL` env vars (`TEST_POSTGRES_*` required alongside URL) | Low | Ops hygiene |

**Remediation required before 009C implementation?** **NO** — governance-only 009C-PREAUTH may proceed.

---

### AP-10 — Readiness for TASK-009C-PREAUTH

| Criterion | Assessment |
|-----------|------------|
| Persistence contract stable | **YES** — DEC-015/DEC-016 implemented |
| Assembly boundary preserved | **YES** — 009A unchanged |
| Worker hook point identifiable | **YES** — `persist_answer_for_ranking_request` is orchestration entry; worker would delegate (not implement) |
| Forbidden capabilities absent | **YES** |
| Test coverage for 009B behavior | **YES** — 33/33 |
| Cross-layer test hygiene | **NEEDS REMEDIATION** — non-blocking |

**TASK-009C-PREAUTH (Answer Worker Governance) is authorized to begin.**

---

## Non-blocking observations

| ID | Observation | Impact | Remediation |
|----|-------------|--------|-------------|
| AP-O-01 | `duplicate_rejected` appends to **existing** request without new `answer_request` row | Correct idempotency semantics; audit trail shows repeat attempts on same hash | Document in 009C worker contract |
| AP-O-02 | Orchestration `session.commit()` breaks nested savepoint test isolation | Combined-suite flakes; production behavior correct | AP-R-03 |
| AP-O-03 | Ranked composite FK deferred; V-B-02 service-only for ranked parent | Acceptable per D-02; DB enforces retrieval composite only | Future hardening optional |
| AP-O-04 | `skipped` status reserved; no worker dry-run path yet | Expected — 009C scope | 009C-PREAUTH |

---

## Architectural risks (monitoring)

| Risk | Likelihood | Mitigation in place |
|------|------------|---------------------|
| Provenance duplication creep on answer rows | Low | Migration allowlist + `PROHIBITED_TABLE_COLUMNS` tests |
| Partial child rows on orchestration fault | Low | Single transaction + no child loop on assembly failure |
| Duplicate persistence without terminal detection | Low | In-flight accepted guard + partial unique index |
| Worker bypasses persistence APIs | Medium (future) | 009C must mandate `persist_answer_for_ranking_request` or equivalent governed entry |
| Test suite false negatives mask regressions | Medium | AP-R-01, AP-R-02 recommended |

---

## Gate closure record

| Item | Status |
|------|--------|
| TASK-009B migration + ORM | **CLOSED** — **ACCEPTED** |
| TASK-009B `answer_persistence` service | **CLOSED** — **ACCEPTED** |
| TASK-009B tests | **CLOSED** — **ACCEPTED** (33/33) |
| Answer persistence review (009B+) | **CLOSED** — **ACCEPTED WITH REMEDIATION** |
| Answer persistence phase | **COMPLETE** |
| TASK-009C-PREAUTH | **AUTHORIZED TO BEGIN** (governance only) |
| TASK-009C implementation | **NOT AUTHORIZED** |
| Answer worker / APIs / response runtime | **NOT AUTHORIZED** |

---

## Next valid gate

**TASK-009C-PREAUTH — Answer Worker Governance** — design envelope for single-worker orchestration over `persist_answer_for_ranking_request`. No worker code, APIs, response runtime, or AI until explicit implementation authorization.

---

## Files inspected

| Area | Paths |
|------|-------|
| Migration | `backend/migrations/versions/c7e3a1f94d82_create_answer_persistence_tables.py` |
| ORM | `backend/app/models/answer_*.py`, `backend/app/models/__init__.py` |
| Service | `backend/app/services/answer_persistence/` |
| Upstream assembly | `backend/app/services/answer_assembly/` |
| Tests | `backend/tests/test_answer_persistence.py`, `test_answer_persistence_alembic_migration.py`, `test_answer_assembly.py`, `test_controlled_ranking_execution.py` |
| Governance | `ANSWER_PERSISTENCE_CONTRACT.md`, `TASKS/TASK-009B-*.md`, `DECISION_LOG.md`, `PROJECT_STATE.md` |

---

## Review verdict

**ACCEPTED WITH REMEDIATION**

TASK-009B answer persistence satisfies all ten required review areas. Implementation is architecturally sound and boundary-compliant. Test failures in the combined integration suite are **not attributable to 009B defects**; recommended remediation (AP-R-01, AP-R-02) is **non-blocking** for TASK-009C-PREAUTH.
