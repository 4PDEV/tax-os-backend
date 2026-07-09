# Changelog

All notable changes to `tax-os-backend` are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions align with git tags where applicable.

## [task-011a-preauth] - 2026-06-02

### Added

- TASK-011A-PREAUTH — API layer governance contract:
  - [`API_RUNTIME_CONTRACT.md`](API_RUNTIME_CONTRACT.md)
  - [`TASKS/TASK-011A-API-LAYER.md`](TASKS/TASK-011A-API-LAYER.md)
  - G-01–G-12: HTTP transport boundary above response runtime only
  - Conceptual entry: `POST /query/{answer_request_id}` (design only)
  - `ApiDeliveryRequest` / `ApiDeliveryResponse` frozen envelopes
  - API → runtime version mapping (`011A-v1` → `010A-v1`)
  - Deterministic HTTP status mapping and API-only error vocabulary
  - Sole delegate: `build_response` — no reach-around into lower layers
  - API-OQ-01–API-OQ-08 documented with deferred recommendations
  - DEC-021 locked in [`DECISION_LOG.md`](DECISION_LOG.md)

### Notes

- Claude governance review: **ACCEPTED WITH FINDINGS** — 20/20 checks; no blocking findings
- Non-blocking findings recorded for IMPL-AUTH: Finding 4 (`delivery_metadata` mapping); Finding 5 (409 status tradeoff)
- Tag: `v0.2.7-api-layer-preauth`
- Governance/design only — **TASK-011A implementation NOT AUTHORIZED**
- No FastAPI routes, handlers, middleware, auth, workers, queues, or tests
- Next gate: **TASK-011A-IMPL-AUTH**

## [response-runtime-layer-review] - 2026-06-02

### Added

- Response Runtime Layer Review (TASK-010A+) — end-to-end governance closeout:
  - Verdict: **ACCEPTED WITH FINDINGS** — Response Runtime Layer **COMPLETE**
  - F-1 traceability: `dd91441` / `v0.2.4-response-runtime`; `83037b6` / `v0.2.5-response-runtime-governance`; `main` up to date with `origin/main`; working tree clean
  - F-2 README status realigned through TASK-010A

### Changed

- [`README.md`](README.md), [`CURRENT_STATUS.md`](CURRENT_STATUS.md), [`PROJECT_STATE.md`](PROJECT_STATE.md), [`TASK_REGISTRY.md`](TASK_REGISTRY.md), [`TASKS/TASK-010A-RESPONSE-RUNTIME.md`](TASKS/TASK-010A-RESPONSE-RUNTIME.md) — layer acceptance recorded

### Notes

- Tag: `v0.2.6-response-runtime-layer-review`
- Response Runtime Layer may be marked complete
- No API-layer implementation or pre-authorization is opened
- Optional test hardening: expanded `FORBIDDEN_RUNTIME_TOKENS` in `test_response_runtime_skeleton.py`

## [task-010a-response-runtime-governance] - 2026-06-02

### Added

- TASK-010A governance artifacts tracked:
  - [`RESPONSE_RUNTIME_CONTRACT.md`](RESPONSE_RUNTIME_CONTRACT.md)
  - [`TASKS/TASK-010A-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-010A-IMPLEMENTATION-AUTHORIZATION.md)

### Notes

- Tag: `v0.2.5-response-runtime-governance`

## [task-010a-response-runtime] - 2026-06-02

### Added

- TASK-010A response runtime:
  - `backend/app/services/response_runtime/` — `build_response`, frozen DTOs
  - Read-only delivery from completed answer persistence; `CitationFormatter` gate
  - OQ-R-09: `legal_object_id` + `source_version_id` pass-through on `ResponseEvidenceEntry`
  - `backend/tests/test_response_runtime_skeleton.py` — 15/15 tests

### Notes

- Claude implementation review: **ACCEPTED WITH FINDINGS** (non-blocking test hygiene)
- Tag: `v0.2.4-response-runtime`
- Next gate: Response Runtime Layer Review (010A+); public APIs **NOT AUTHORIZED**

## [task-010a-impl-auth] - 2026-06-02

### Added

- TASK-010A-IMPLEMENTATION-AUTHORIZATION — response runtime implementation design package:
  - [`TASKS/TASK-010A-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-010A-IMPLEMENTATION-AUTHORIZATION.md)
  - D-R-01 module boundary (`response_runtime/` — 4 modules)
  - D-R-02 responsibilities; D-R-03 frozen DTOs
  - F-1 / OQ-R-09 Option A: `legal_object_id` + `source_version_id` on `ResponseEvidenceEntry`
  - F-5: `get_answer_request` / `get_answer_result` verified as approved read dependencies
  - D-R-04–D-R-12 validation, imports, behaviour, errors, determinism, non-goals, tests, scope
  - DEC-020 locked in [`DECISION_LOG.md`](DECISION_LOG.md)

### Changed

- [`RESPONSE_RUNTIME_CONTRACT.md`](RESPONSE_RUNTIME_CONTRACT.md) — OQ-R-09 closed; `ResponseEvidenceEntry` updated

### Notes

- Governance/design only — **TASK-010A implementation NOT AUTHORIZED**
- Next gate: Claude review → explicit TASK-010A implementation authorization

## [task-010a-preauth] - 2026-06-02

### Added

- TASK-010A-PREAUTH — response runtime governance contract:
  - [`RESPONSE_RUNTIME_CONTRACT.md`](RESPONSE_RUNTIME_CONTRACT.md)
  - [`TASKS/TASK-010A-RESPONSE-RUNTIME.md`](TASKS/TASK-010A-RESPONSE-RUNTIME.md)
  - G-01 boundary: read + render only — no retrieve, rank, assemble, persist, workers
  - G-02 entry: `build_response` in `response_runtime/` (design frozen)
  - G-03 `ResponseRequest`; G-04 `ResponsePackage` / `ResponseOutcome`
  - G-05 read model; G-06 deterministic rendering; G-07 `CitationFormatter` only
  - G-08 runtime error vocabulary; G-09 import guards; G-10 layer separation
  - G-11 determinism; G-12 readiness checklist
  - DEC-019 locked in [`DECISION_LOG.md`](DECISION_LOG.md)

### Notes

- Governance/design only — **TASK-010A implementation NOT AUTHORIZED**
- No runtime code, APIs, workers, migrations, ORM, or tests
- Next gate: Claude review → TASK-010A-IMPL-AUTH

## [task-009c-answer-worker-skeleton] - 2026-06-02

### Added

- TASK-009C answer worker skeleton:
  - `backend/app/workers/answer_runtime/` — `run_answer_worker`, `AnswerWorkerRequest`, `AnswerWorkerOutcome`
  - Single-worker orchestration (OD-021); delegates to `persist_answer_for_ranking_request` only
  - Documented queue lifecycle (accepted → running → completed | failed) — no broker infrastructure
  - `backend/tests/test_answer_worker_skeleton.py` — 16/16 tests; R-1 mutex release closed

### Notes

- Tag: `v0.2.3-answer-worker-skeleton` — commit `1ec1423`
- Answer stack complete through worker boundary — **response runtime NOT AUTHORIZED**
- Next gate: **TASK-010A-PREAUTH** — Response Runtime Governance

## [task-009c-impl-auth-accepted] - 2026-06-02

### Changed

- Claude review acceptance of TASK-009C-IMPLEMENTATION-AUTHORIZATION — **AUTHORIZED FOR LIMITED IMPLEMENTATION**
- DEC-018 updated — bounded worker skeleton scope
- Governance: `PROJECT_STATE.md`, `TASK_REGISTRY.md`, `CURRENT_STATUS.md`

### Notes

- Remediation R-1 (non-blocking): OD-021 mutex release test in future `test_answer_worker_skeleton.py`
- Tag: `v0.2.2-answer-worker-impl-auth`

## [task-009c-impl-auth] - 2026-06-02

### Added

- TASK-009C-IMPLEMENTATION-AUTHORIZATION — answer worker implementation design package:
  - [`TASKS/TASK-009C-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-009C-IMPLEMENTATION-AUTHORIZATION.md)
  - D-C-01 module boundary (`answer_runtime/` — 3 modules)
  - D-C-02 `run_answer_worker` entry; D-C-03 frozen DTO fields
  - D-C-04 delegation to `persist_answer_for_ranking_request` only
  - D-C-05 failure mapping incl. F-3 duplicate_rejected / F-4 dual status tests
  - D-C-06 OD-021 mutex; D-C-07 queue boundary; D-C-08 import guards
  - D-C-09 test matrix; D-C-10 implementation scope
  - DEC-018 locked in [`DECISION_LOG.md`](DECISION_LOG.md)

### Notes

- Governance/design only — **TASK-009C implementation NOT AUTHORIZED**
- No worker code, queues, migrations, ORM, services, APIs, or tests
- Next gate: Claude review → explicit TASK-009C implementation authorization

## [task-009c-preauth] - 2026-06-02

### Added

- TASK-009C-PREAUTH — answer worker governance contract:
  - [`ANSWER_WORKER_CONTRACT.md`](ANSWER_WORKER_CONTRACT.md)
  - [`TASKS/TASK-009C-ANSWER-WORKER.md`](TASKS/TASK-009C-ANSWER-WORKER.md)
  - Worker boundary: `run_answer_worker` → `persist_answer_for_ranking_request` only
  - DTOs: `AnswerWorkerRequest`, `AnswerWorkerOutcome`
  - Documented lifecycle (no queue); OD-021 single-worker; failure mapping; import guards
  - Response runtime boundary; test plan (design only)
  - DEC-017 locked in [`DECISION_LOG.md`](DECISION_LOG.md)

### Notes

- Governance/design only — **TASK-009C implementation NOT AUTHORIZED**
- No worker code, queues, migrations, APIs, or tests
- Next gate: Claude review → 009C-IMPL-AUTH

## [answer-persistence-review] - 2026-06-02

### Added

- Answer Persistence Review (TASK-009B+) — [`TASKS/ANSWER-PERSISTENCE-REVIEW.md`](TASKS/ANSWER-PERSISTENCE-REVIEW.md)
  - AP-01 through AP-10 review areas documented
  - 009B tests 33/33 pass; combined-suite failures traced to pre-existing test patterns (not 009B defects)
  - Non-blocking remediation AP-R-01 through AP-R-04

### Notes

- **Verdict: ACCEPTED WITH REMEDIATION**
- TASK-009C-PREAUTH authorized to begin (governance only)
- TASK-009C implementation remains **NOT AUTHORIZED**

## [task-009b-answer-persistence] - 2026-06-02

### Added

- TASK-009B answer persistence — append-only lifecycle (DEC-015 / DEC-016):
  - Alembic `c7e3a1f94d82` — `answer_requests`, `answer_results`, `answer_evidence_entries`, `answer_uncertainty_flags`
  - Prerequisite `uq_ranked_evidence_result_id_pk` on `ranked_evidence_references`
  - ORM models under `backend/app/models/answer_*.py`
  - `backend/app/services/answer_persistence/` — `create_*`, read APIs, `persist_answer_for_ranking_request`
  - `backend/tests/test_answer_persistence.py` — hash, replay, RL-O-01, V-B-02, in-flight guard (R-2), pure-pointer guards
  - `backend/tests/test_answer_persistence_alembic_migration.py` — migration contract + upgrade/downgrade

### Notes

- Option A lifecycle: request → accepted → assemble → children → terminal
- No answer worker, response runtime, public APIs, or AI
- Tag: `v0.1.9-answer-persistence`

## [task-009b-impl-auth] - 2026-06-02

### Added

- TASK-009B-IMPLEMENTATION-AUTHORIZATION — answer persistence implementation design package:
  - [`TASKS/TASK-009B-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-009B-IMPLEMENTATION-AUTHORIZATION.md)
  - D-01 frozen schema (4 tables, constraints, indexes)
  - D-02 composite FK: retrieval required; ranked via V-B-02 service validation
  - D-03 single-transaction boundary; D-04 Option A lifecycle ordering
  - D-05 `answer_persistence/` service surface; D-06 import guards; D-07 test matrix
  - D-08 replay/hash; D-09 prohibited-column matrix; D-10 implementation scope
  - DEC-016 locked in [`DECISION_LOG.md`](DECISION_LOG.md)

### Notes

- Governance/design only — **TASK-009B implementation NOT AUTHORIZED**
- No migrations, ORM, services, workers, APIs, or tests
- Next gate: Claude review → explicit TASK-009B implementation authorization

## [task-009b-preauth] - 2026-06-02

### Added

- TASK-009B-PREAUTH — answer persistence governance contract:
  - [`ANSWER_PERSISTENCE_CONTRACT.md`](ANSWER_PERSISTENCE_CONTRACT.md)
  - [`TASKS/TASK-009B-ANSWER-PERSISTENCE.md`](TASKS/TASK-009B-ANSWER-PERSISTENCE.md)
  - Option B recommended: append-only `answer_requests`, `answer_results`, `answer_evidence_entries`, `answer_uncertainty_flags`
  - `answer_request_hash` + DEC-011 replay; RL-O-01 preserved; pure-pointer evidence doctrine (DEC-010)
  - Citation non-persistence; uncertainty flag schema; failure model; zero-evidence path
  - DEC-015 locked in [`DECISION_LOG.md`](DECISION_LOG.md)

### Notes

- Governance/design only — **TASK-009B implementation NOT AUTHORIZED**
- No migrations, ORM, services, workers, APIs, or tests
- Next gate: Claude review → 009B-IMPL-AUTH

## [answer-layer-review] - 2026-06-02

### Added

- Answer Layer Review (TASK-009A+) — end-to-end governance review:
  - [`TASKS/ANSWER-LAYER-REVIEW.md`](TASKS/ANSWER-LAYER-REVIEW.md)
  - AL-01–AL-10 verified: retrieval→ranking→answer boundary, RL-O-01, evidence completeness, DEC-010, citation boundary, failure model, determinism, layer boundaries, forbidden capability scan
  - Verdict: **ACCEPTED** — answer layer **COMPLETE** (ephemeral 009A)

### Notes

- TASK-009B-PREAUTH **authorized to begin** (governance only)
- TASK-009B implementation remains **NOT AUTHORIZED**
- Non-blocking observations AL-O-01–AL-O-05 documented; no remediation required

## [task-009a-impl-auth] - 2026-06-02

### Added

- TASK-009A-IMPLEMENTATION-AUTHORIZATION — answer assembly implementation design package:
  - [`TASKS/TASK-009A-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-009A-IMPLEMENTATION-AUTHORIZATION.md)
  - OQ-01 locked: **Option A** ephemeral `AnswerPackage` only (no persistence)
  - OQ-03 locked: **CitationFormatter** read-only permitted; **CitationAssembler** prohibited
  - RL-O-01 mandatory tests RL-T-01–RL-T-10
  - Service boundary: `backend/app/services/answer_assembly/` (`assembly.py`, `validation.py`, `models.py`)
  - Ephemeral lifecycle, failure mapping, import guards, OD-021 carry-forward (direct service only)
  - AnswerPackage construction sequence; test plan (design only)
  - DEC-014 locked in [`DECISION_LOG.md`](DECISION_LOG.md)

### Notes

- Claude review: **ACCEPTED**
- Governance/design only — **TASK-009A implementation NOT AUTHORIZED** until explicit bounded prompt
- TASK-009B persistence (Option B) deferred
- Tag: `v0.1.7-answer-impl-auth`

## [task-009a-preauth] - 2026-06-02

### Added

- TASK-009A-PREAUTH — answer assembly governance contract:
  - [`ANSWER_ASSEMBLY_CONTRACT.md`](ANSWER_ASSEMBLY_CONTRACT.md)
  - [`TASKS/TASK-009A-ANSWER-ASSEMBLY.md`](TASKS/TASK-009A-ANSWER-ASSEMBLY.md)
  - Answer layer boundary, evidence rules E-01–E-08, provenance read model (DEC-010), citation reference rules, `AnswerPackage` schema (009A-v1), answer failure vocabulary, layer separation, AI boundary, implementation readiness criteria
  - DEC-013 locked in [`DECISION_LOG.md`](DECISION_LOG.md)
  - Ranking result resolution rule (accepted vs terminal — closes RL-O-01)

### Notes

- Governance/design only — **TASK-009A implementation NOT AUTHORIZED**
- No services, workers, APIs, persistence, models, migrations, or tests
- Next gate: Claude review → 009A-IMPL-AUTH

## [ranking-layer-review] - 2026-06-02

### Added

- Ranking Layer Review (TASK-008A+) — end-to-end governance review:
  - [`TASKS/RANKING-LAYER-REVIEW.md`](TASKS/RANKING-LAYER-REVIEW.md)
  - RL-01–RL-10 verified: retrieval boundary, DEC-010 provenance-once, permutation integrity, determinism (four profiles), DEC-011 replay, error vocabulary, OD-021, layer boundaries, forbidden capability scan
  - Verdict: **ACCEPTED** — ranking layer **COMPLETE**

### Notes

- TASK-009A pre-authorization **authorized to begin** (governance only)
- TASK-009A implementation remains **NOT AUTHORIZED**
- Non-blocking observations RL-O-01–RL-O-04 documented; no remediation required

## [u-01-ranking-worker-skeleton] - 2026-06-02

### Added

- U-01 ranking worker skeleton:
  - `backend/app/workers/ranking_runtime/` — `run_ranking_worker`, `RankingWorkerRequest`, `RankingWorkerOutcome`
  - Single-worker orchestration (OD-021); delegates to `execute_controlled_ranking` only
  - Documented queue lifecycle (accepted → running → completed | failed) — no broker infrastructure
  - [`TASKS/U-01-RANKING-WORKER-SKELETON.md`](TASKS/U-01-RANKING-WORKER-SKELETON.md)

### Notes

- Claude review: **ACCEPTED** (20/20)
- Skeleton only — **TASK-009A NOT AUTHORIZED**; no queue infrastructure

## [task-008d-implementation-authorization] - 2026-06-02

### Added

- TASK-008D-IMPLEMENTATION-AUTHORIZATION — ranking execution implementation design package:
  - [`TASKS/TASK-008D-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-008D-IMPLEMENTATION-AUTHORIZATION.md)
  - Locks: service boundary (`ranking_execution`), inputs, profile algorithms, permutation validation, zero-evidence path, 008C persistence integration, replay/idempotency (DEC-011), failure mapping, worker model (OD-021), test plan

### Notes

- Governance/design only — **TASK-008D implementation NOT AUTHORIZED**

## [task-008d-preauth] - 2026-06-02

### Added

- TASK-008D-PREAUTH — ranking execution governance contract:
  - [`RANKING_EXECUTION_CONTRACT.md`](RANKING_EXECUTION_CONTRACT.md)
  - [`TASKS/TASK-008D-RANKING-EXECUTION.md`](TASKS/TASK-008D-RANKING-EXECUTION.md)
  - DEC-012 — ranking execution determinism and boundary

### Notes

- Governance only — **TASK-008D implementation NOT AUTHORIZED**
- **TASK-009A answer runtime NOT AUTHORIZED**

## [task-008c-ranking-persistence] - 2026-06-02

### Added

- TASK-008C ranking persistence (limited implementation):
  - Migration `a8c1e4f92b37` — `ranking_requests`, `ranking_results`, `ranked_evidence_references`
  - Composite membership `UNIQUE(retrieval_result_id, id)` on `retrieval_evidence_references`
  - Append-only ORM models and `ranking_persistence` service
  - Persistence tests: pure-pointer guards, FK/composite membership, duplicate rejection, zero-result success, canonical errors
- DEC-011 — force replay hash interpretation (Claude F-10 documentation closure)

### Notes

- Claude review: **ACCEPTED** (F-10 closed via DEC-011)
- Persistence only — **TASK-008D execution and TASK-009A answer runtime NOT AUTHORIZED**

## [v0.1.2-ranking-preauth-reconciled] - 2026-06-02

### Added

- TASK-008C-PREAUTH-RECONCILIATION: ranking persistence pre-authorization reconciliation — **accepted**.
  - Commit: `cc170aa` — `docs: accept TASK-008C preauth reconciliation`
  - Tag: `v0.1.2-ranking-preauth-reconciled`
  - [`TASKS/TASK-008C-PREAUTH-RECONCILIATION.md`](TASKS/TASK-008C-PREAUTH-RECONCILIATION.md)
  - [`TASKS/TASK-008C-RANKING-PERSISTENCE.md`](TASKS/TASK-008C-RANKING-PERSISTENCE.md) (placeholder — not authorized)

### Changed

- [`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md) — explicit FK targets (`retrieval_results.id`, `retrieval_evidence_references.id`); pure-pointer column table; preauth verification record

### Notes

- Pushed `origin/main`. Governance only — **TASK-008C implementation NOT AUTHORIZED**

## [task-008c-remediation-ranking-contract-reconciliation] - 2026-06-02

### Changed

- TASK-008C-REMEDIATION: reconcile ranking contract to provenance-once pure-pointer shape (008B-v2).
  - [`RANKING_PERSISTENCE_REMEDIATION_008C-REMEDIATION.md`](RANKING_PERSISTENCE_REMEDIATION_008C-REMEDIATION.md)
  - [`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md) — removed copied provenance on ranked rows; canonical error vocabulary; composite FK
  - [`DECISION_LOG.md`](DECISION_LOG.md) — DEC-010 locked

### Notes

- Governance only — TASK-008C persistence **not authorized**

## [task-008b-ranking-runtime-contract] - 2026-06-02

### Added

- TASK-008B: ranking runtime contract (governance only).
  - [`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md)
  - [`TASKS/TASK-008B-RANKING-RUNTIME-CONTRACT.md`](TASKS/TASK-008B-RANKING-RUNTIME-CONTRACT.md)

### Changed

- 008A1 forward conditions resolved: inter-group ordering, 008C binding constraints, `EFFECTIVE_DATE_DESC` sort-only, `presentation_order_index`
- Platform state: ranking contract **complete**; TASK-008C **not authorized**

### Notes

- Contract only — no persistence, workers, answers, or AI ranking

## [task-008a1-acceptance-ranking-runtime-authorized] - 2026-06-02

### Added

- TASK-008A1 acceptance review — **CLOSED** — **ACCEPTED**; TASK-008B **authorized with conditions**.
  - [`RANKING_RUNTIME_008A1_ACCEPTANCE_REVIEW.md`](RANKING_RUNTIME_008A1_ACCEPTANCE_REVIEW.md)
  - [`TASKS/TASK-008A1-ACCEPTANCE-REVIEW.md`](TASKS/TASK-008A1-ACCEPTANCE-REVIEW.md)

### Changed

- RK-01 through RK-11 findings **CLOSED** at acceptance
- Option A (separate ranking layer) **selected**; Option B rejected
- Platform state: TASK-008B ranking contract **authorized with conditions**; 008C+ **not authorized**

### Notes

- Acceptance only — no ranking persistence, workers, execution, answers, or AI. Forward conditions bind 008B deliverable.

## [task-008a1-ranking-runtime-remediation] - 2026-06-02

### Added

- TASK-008A1: ranking runtime remediation package (governance only).
  - [`RANKING_RUNTIME_REMEDIATION_008A1.md`](RANKING_RUNTIME_REMEDIATION_008A1.md)
  - [`TASKS/TASK-008A1-RANKING-RUNTIME-REMEDIATION.md`](TASKS/TASK-008A1-RANKING-RUNTIME-REMEDIATION.md)

### Changed

- RK-01 resolved: **Option A** (separate ranking layer) recommended; Option B rejected

### Notes

- Governance only — TASK-008B **not authorized** until 008A1 acceptance (superseded by acceptance entry above).

## [checkpoint-task-007a-007e-retrieval-pipeline-review] - 2026-06-02

### Added

- Retrieval pipeline review closure (TASK-007A through TASK-007E).
  - [`CLAUDE_REVIEW_RETRIEVAL_PIPELINE_007A-007E.md`](CLAUDE_REVIEW_RETRIEVAL_PIPELINE_007A-007E.md)
  - [`TASKS/TASK-007A-007E-RETRIEVAL-PIPELINE-REVIEWER-PACKAGE.md`](TASKS/TASK-007A-007E-RETRIEVAL-PIPELINE-REVIEWER-PACKAGE.md)

### Changed

- Verdict: **CLOSED** — **APPROVED FOR CONTINUE**; RET-01–RET-09 verified; no remediation required
- TASK-007E implementation acceptance **CLOSED**
- Retrieval layer phase marked **COMPLETE**; next gate **TASK-008A** ranking pre-auth (**NOT AUTHORIZED**)

### Notes

- Ranking, answers, AI retrieval, concurrent workers **not authorized**

## [task-007e-controlled-retrieval-execution] - 2026-06-02

### Added

- TASK-007E: controlled retrieval execution.
  - `backend/app/services/retrieval_execution/` — selection, ordering, citation lookup, execution
  - `ControlledRetrievalRuntimeProvider` — `backend/app/workers/retrieval_runtime/controlled_provider.py`
  - `run_controlled_retrieval_execution(controlled_execution=True)` — mandatory flag
  - [`TASKS/TASK-007E-CONTROLLED-RETRIEVAL-EXECUTION.md`](TASKS/TASK-007E-CONTROLLED-RETRIEVAL-EXECUTION.md)
  - Tests: `test_controlled_retrieval_execution.py`

### Changed

- Retrieval worker: controlled execution mode (`accepted` → `completed` / `failed`); dry-run unchanged (`accepted` → `skipped`)
- Full suite: 777 tests passing

### Notes

- First authorized evidence selection and `retrieval_evidence_references` creation. Citation read-only attach only; no `CitationAssembler`. Ranking / answers / AI / concurrent workers **not authorized**.

## [task-007d1-acceptance-retrieval-execution-authorized] - 2026-06-02

### Added

- TASK-007D1 acceptance review — **CLOSED**; TASK-007E **authorized with conditions**.
  - [`RETRIEVAL_EXECUTION_007D1_ACCEPTANCE_REVIEW.md`](RETRIEVAL_EXECUTION_007D1_ACCEPTANCE_REVIEW.md)
  - [`TASKS/TASK-007E-CONTROLLED-RETRIEVAL-EXECUTION.md`](TASKS/TASK-007E-CONTROLLED-RETRIEVAL-EXECUTION.md)

### Changed

- RW-01 through RW-06 findings **CLOSED** at acceptance
- Platform state: controlled retrieval execution **authorized for implementation**

### Notes

- Authorization only — no 007E implementation until bounded delivery task. Ranking / answers / AI **not authorized**.

## [task-007d1-retrieval-execution-remediation] - 2026-06-02

### Added

- TASK-007D execution pre-authorization review — APPROVED WITH REQUIRED REMEDIATION BEFORE CONTROLLED EXECUTION.
  - [`ARCHITECTURE_REVIEW_RETRIEVAL_EXECUTION_007D-PREAUTH.md`](ARCHITECTURE_REVIEW_RETRIEVAL_EXECUTION_007D-PREAUTH.md)
- TASK-007D1: retrieval execution remediation package (governance only).
  - [`RETRIEVAL_EXECUTION_REMEDIATION_007D1.md`](RETRIEVAL_EXECUTION_REMEDIATION_007D1.md)
  - [`TASKS/TASK-007D1-RETRIEVAL-EXECUTION-REMEDIATION.md`](TASKS/TASK-007D1-RETRIEVAL-EXECUTION-REMEDIATION.md)

### Changed

- RW-01 through RW-06 remediated at spec level — AS_OF_DATE ambiguity, no silent latest fallback, citation behavior, deterministic ordering, execution leakage guards, staging sequence
- Planned TASK-007E controlled execution flow documented

### Notes

- Governance only — no execution implementation, no worker changes. TASK-007E **not authorized** until 007D1 acceptance review.

## [task-007d-retrieval-worker-skeleton] - 2026-06-02

### Added

- TASK-007D: dry-run retrieval worker skeleton.
  - `backend/app/workers/retrieval_runtime/` — worker, runner, dry-run provider, result types
  - `run_retrieval_runtime_dry_run()` — `dry_run=True` mandatory
  - [`TASKS/TASK-007D-RETRIEVAL-WORKER-SKELETON.md`](TASKS/TASK-007D-RETRIEVAL-WORKER-SKELETON.md)
  - Tests: `test_retrieval_worker_skeleton.py`

### Changed

- Retrieval persistence: `get_latest_result_for_request`, `list_results_for_request`
- Full suite: 759 tests passing

### Notes

- Dry-run lifecycle only (`accepted` → `skipped`). No evidence references, execution, ranking, or answers. Controlled execution requires TASK-007D1.

## [task-007c-retrieval-persistence] - 2026-06-02

### Added

- TASK-007C: append-only retrieval persistence.
  - Migration `f9e4d2a87c10` — `retrieval_requests`, `retrieval_results`, `retrieval_evidence_references`
  - Models: `RetrievalRequest`, `RetrievalResult`, `RetrievalEvidenceReference`
  - Service: `backend/app/services/retrieval_persistence/` (hashing, validation, persistence)
  - Tests: `test_retrieval_persistence.py`, `test_retrieval_persistence_alembic_migration.py`

### Changed

- RP-01 through RP-08 implemented — request hash canonicalization, FK constraints, citation consistency, CHECK constraints, metadata whitelist, order index, zero-result semantics, prohibited-field guards
- Full suite: 744 tests passing

### Notes

- Persistence only — no retrieval execution, workers, ranking, answers, or AI. TASK-007D **not authorized**.

## [task-007c1-acceptance-retrieval-persistence-authorized] - 2026-06-02

### Added

- TASK-007C1 acceptance review — **CLOSED**; TASK-007C **authorized with conditions**.
  - [`RETRIEVAL_PERSISTENCE_007C1_ACCEPTANCE_REVIEW.md`](RETRIEVAL_PERSISTENCE_007C1_ACCEPTANCE_REVIEW.md)
  - [`TASKS/TASK-007C-RETRIEVAL-PERSISTENCE.md`](TASKS/TASK-007C-RETRIEVAL-PERSISTENCE.md)

### Changed

- RP-01 through RP-08 findings **CLOSED** at acceptance
- Platform state: retrieval persistence **authorized for implementation**; 007D / ranking / answers / AI **not authorized**

### Notes

- Persistence-only authorization envelope — no workers, execution, or APIs in 007C scope.

## [task-007c1-retrieval-persistence-remediation] - 2026-06-02

### Added

- TASK-007C pre-authorization review — APPROVED WITH REQUIRED REMEDIATION BEFORE TASK-007C.
  - [`ARCHITECTURE_REVIEW_RETRIEVAL_PERSISTENCE_007C-PREAUTH.md`](ARCHITECTURE_REVIEW_RETRIEVAL_PERSISTENCE_007C-PREAUTH.md)
- TASK-007C1: retrieval persistence remediation package (governance only).
  - [`RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md`](RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md)
  - [`TASKS/TASK-007C1-RETRIEVAL-PERSISTENCE-REMEDIATION.md`](TASKS/TASK-007C1-RETRIEVAL-PERSISTENCE-REMEDIATION.md)

### Changed

- RP-01 through RP-08 remediated at spec level — request_hash canonicalization, FK constraints, citation consistency, CHECK constraints, metadata whitelist, order index, zero-result semantics, prohibited-field tests
- Planned TASK-007C schema documented (`retrieval_requests`, `retrieval_results`, `retrieval_evidence_references`)

### Notes

- Governance only — no migrations, models, services, workers, or APIs. TASK-007C **not authorized** until 007C1 acceptance review.

## [task-007b-retrieval-runtime-contract] - 2026-06-02

### Added

- TASK-007A1 acceptance review — **CLOSED**; TASK-007B authorized with conditions.
  - [`RETRIEVAL_RUNTIME_007A1_ACCEPTANCE_REVIEW.md`](RETRIEVAL_RUNTIME_007A1_ACCEPTANCE_REVIEW.md)
- TASK-007B: retrieval runtime governance contract.
  - [`RETRIEVAL_RUNTIME_CONTRACT.md`](RETRIEVAL_RUNTIME_CONTRACT.md)
  - [`TASKS/TASK-007B-RETRIEVAL-RUNTIME-CONTRACT.md`](TASKS/TASK-007B-RETRIEVAL-RUNTIME-CONTRACT.md)

### Changed

- R-01 through R-06 findings **CLOSED** at acceptance
- Governed pipeline registered: 007B → 007C → 007D → retrieval layer review

### Notes

- Contract only — no persistence, workers, or execution. 007C/007D **not authorized**.

## [task-007a1-retrieval-runtime-remediation] - 2026-06-02

### Added

- TASK-007A1: retrieval runtime remediation package (governance only).
  - [`RETRIEVAL_RUNTIME_REMEDIATION_007A1.md`](RETRIEVAL_RUNTIME_REMEDIATION_007A1.md)
  - [`TASKS/TASK-007A1-RETRIEVAL-RUNTIME-REMEDIATION.md`](TASKS/TASK-007A1-RETRIEVAL-RUNTIME-REMEDIATION.md)

### Changed

- R-01 through R-06 remediated at spec level — temporal modes, version pins, evidence references, persistence, citation lookup, deterministic ordering
- Ranking boundary and OD-021 carry-forward documented

### Notes

- TASK-007B remains **NOT AUTHORIZED** — awaits remediation acceptance review. No 004A code changes.

## [task-007a-retrieval-runtime-preauth-review] - 2026-06-02

### Added

- TASK-007A: retrieval runtime pre-authorization architecture review.
  - [`ARCHITECTURE_REVIEW_RETRIEVAL_RUNTIME_007A-PREAUTH.md`](ARCHITECTURE_REVIEW_RETRIEVAL_RUNTIME_007A-PREAUTH.md)
  - [`TASKS/TASK-007A-RETRIEVAL-RUNTIME-PREAUTH-REVIEW.md`](TASKS/TASK-007A-RETRIEVAL-RUNTIME-PREAUTH-REVIEW.md)

### Changed

- Verdict: **APPROVED WITH REQUIRED REMEDIATION BEFORE TASK-007B**
- Findings R-01–R-10 documented; next gate TASK-007A1 remediation package

### Notes

- Review-only; no retrieval runtime implementation. Ranking / answers **not authorized**.

## [checkpoint-task-006y-006ad-citation-pipeline-review] - 2026-06-02

### Added

- Citation pipeline review closure (TASK-006Y through TASK-006AD).
  - [`CLAUDE_REVIEW_CITATION_PIPELINE_006Y-006AD.md`](CLAUDE_REVIEW_CITATION_PIPELINE_006Y-006AD.md)
  - [`TASKS/TASK-006Y-006AD-CITATION-PIPELINE-REVIEWER-PACKAGE.md`](TASKS/TASK-006Y-006AD-CITATION-PIPELINE-REVIEWER-PACKAGE.md)

### Changed

- Verdict: **CLOSED** — **APPROVED FOR CONTINUE**
- Citation layer phase marked complete; next gate **TASK-007A** retrieval pre-auth review

### Notes

- Retrieval, ranking, answers, concurrent citation workers **not authorized**

## [task-006ad-controlled-citation-execution] - 2026-06-02

### Added

- TASK-006AD: controlled citation execution.
  - `citations` table with `UNIQUE(citation_hash)` (migration `d8f2c4a19b63`)
  - `backend/app/services/citation_execution/` — hashing, validation, persistence, renderer, execution
  - `ControlledCitationAssemblyGovernanceProvider` + `run_controlled_citation_execution()`
  - Tests: `test_controlled_citation_execution.py`, `test_citations_alembic_migration.py`

### Changed

- Governance worker: dry-run unchanged (`skipped`); controlled mode terminal `assembled` with `citation_id`
- Boundary tests updated for `citations` schema at head

### Notes

- **703 tests passed**. Retrieval / answers **not authorized**. OD-021 concurrent workers not implemented.

## [task-006ac-controlled-citation-execution-preauth-review] - 2026-06-02

### Added

- TASK-006AC-GOV: permanent pre-authorization review record (governance documentation repair).
  - [`TASKS/TASK-006AC-CONTROLLED-CITATION-EXECUTION-PREAUTH-REVIEW.md`](TASKS/TASK-006AC-CONTROLLED-CITATION-EXECUTION-PREAUTH-REVIEW.md)

### Changed

- References updated from missing `ARCHITECTURE_REVIEW_CONTROLLED_CITATION_EXECUTION_006AC.md` to canonical review record.
- Decision chain documented: 006AC → 004E → 006AC1 → 006AC1 acceptance → 006AD authorized with conditions.
- Governance docs aligned: TASK-006AD authorized with conditions; implementation not yet started; retrieval/answers not authorized.

### Notes

- No code changes. Review record reconstructs AC-01 through AC-07 for auditability.

## [task-006ac1-citation-execution-remediation] - 2026-06-02

### Added

- TASK-006AC1: controlled citation execution remediation package (governance only).
  - [`CITATION_EXECUTION_REMEDIATION_006AC1.md`](CITATION_EXECUTION_REMEDIATION_006AC1.md)
  - [`TASKS/TASK-006AC1-CONTROLLED-CITATION-EXECUTION-REMEDIATION.md`](TASKS/TASK-006AC1-CONTROLLED-CITATION-EXECUTION-REMEDIATION.md)

### Changed

- AC-02 remediated at spec level — canonical `citation_hash` = 004D provenance tuple; identity independent of rendering.
- AC-03 remediated at spec level — future `UNIQUE(citation_hash)` + service lookup; execution idempotency on `citation_hash`.
- Governance result boundary, planned citation entity shape, OD-021 carry-forward, and planned 006AD flow documented.

### Notes

- AC-01 closed by TASK-004E. TASK-006AD authorized with conditions following 006AC1 acceptance (implementation not yet started).

## [task-004e-citation-temporal-compliance] - 2026-06-02

### Changed

- TASK-004E: citation temporal compliance remediation — AC-01 closed.
- `CitationAssembler`: removed silent `source_version.effective_*` fallback for legal-object applicability.
- `CitationResult`: added `source_version_effective_from` / `source_version_effective_to` as explicitly labeled source metadata only.
- `CitationFormatter`: source-version dates render as "Source version metadata:" lines — never as legal-object applicability.
- Contract: `backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md` updated for Addendum V6 compliance.

### Notes

- AC-02/AC-03 carry-forward documented; remediated at spec level in TASK-006AC1.
- TASK-006AD controlled citation execution remains **NOT AUTHORIZED**.

## [checkpoint-task-006ab-citation-worker-skeleton] - 2026-06-03

### Changed

- TASK-006AB accepted at checkpoint; dry-run citation worker skeleton complete.
- Next gate: TASK-006AC controlled citation execution pre-authorization review.

## [task-006ab-citation-worker-skeleton] - 2026-06-03

### Added

- TASK-006AB: dry-run `CitationAssemblyGovernanceWorker` — `accepted` → `skipped`; no 004D assembler.
- Module: `backend/app/workers/citation_assembly_governance/`
- Tests: `test_citation_worker_skeleton.py`

### Notes

- **678 tests passed**. Citation execution not authorized.

## [task-006aa-citation-worker-skeleton-preauth-review] - 2026-06-03

### Added

- TASK-006AA: citation worker skeleton pre-authorization architecture review.
  - `ARCHITECTURE_REVIEW_CITATION_WORKER_SKELETON_006AA-PREAUTH.md`
  - Verdict: **APPROVED FOR IMPLEMENTATION** of dry-run worker skeleton (TASK-006AB).
  - Preserves: governance result ≠ rendered citation; citation ≠ retrieval ≠ answer.

### Notes

- Review-only; no worker code. Citation execution not authorized.

## [checkpoint-task-006z-citation-persistence] - 2026-06-03

### Changed

- TASK-006Z accepted at checkpoint; citation persistence governance complete on `main`.
- Next gate: TASK-006AA citation worker skeleton pre-authorization review.

## [task-006z-citation-persistence] - 2026-06-03

### Added

- TASK-006Z: citation assembly governance persistence.
  - Tables: `citation_assembly_governance_requests`, `citation_assembly_governance_results`
  - Migration `c6d4f0b15e58`; partial unique on `legal_object_version_id` WHERE `force_reassembly = false`
  - Service: `backend/app/services/citation_assembly_governance/` (`request_hash`, validation, append-only results)
  - ORM: `CitationAssemblyGovernanceRequest` / `Result` (namespace separate from TASK-004D)
  - Tests: persistence + Alembic migration

### Notes

- **667 tests passed** (PostgreSQL `taxos_test`).
- No citation execution, 004D assembler calls, retrieval, or answers.
- Citation worker/execution remains behind future review gate.

## [governance-006za-acceptance-006z-authorized] - 2026-06-03

### Changed

- TASK-006ZA acceptance review: **CLOSED** — findings Z-01–Z-05, Z-07, Z-14 closed.
- TASK-006Z: **AUTHORIZED FOR IMPLEMENTATION** (append-only `citation_assembly_requests` / `citation_assembly_results` only).
- `CITATION_PERSISTENCE_006ZA_ACCEPTANCE_REVIEW.md` — authorization envelope recorded.

### Notes

- Citation execution, workers, retrieval, answers, legal advice — **not authorized**.
- Doctrine chain unchanged: `parsed_structure` ≠ legal object · `legal_object` ≠ citation · `citation` ≠ answer.

## [task-006za-citation-persistence-remediation-package] - 2026-06-03

### Added

- TASK-006ZA: citation persistence pre-auth remediation package.
  - `CITATION_PERSISTENCE_REMEDIATION_006ZA.md` — planned 006Z shape (Z-01–Z-05, Z-07, Z-14).
  - `TASKS/TASK-006ZA-CITATION-PERSISTENCE-REMEDIATION-PACKAGE.md` — task record.
  - Governance naming: `CitationAssemblyGovernanceRequest` / `Result`; `request_hash` vs 004D rendered hash.

### Notes

- 006Z pre-auth review remediated; TASK-006Z remains **NOT AUTHORIZED**.
- No tables, migrations, or implementation.

## [checkpoint-task-006y-citation-assembly-contract] - 2026-06-03

### Changed

- Governance status: **Citation governance layer ESTABLISHED**; persistence not started; TASK-006Z planned — not yet authorized.
- Pre-006Z gate: recommend architecture review of citation persistence shape (identity + provenance).

## [task-006y-citation-assembly-contract] - 2026-06-03

### Added

- TASK-006Y: ingestion-pipeline citation assembly governance contract.
  - `CITATION_ASSEMBLY_CONTRACT.md` — `legal_object` → citation boundary; request/result/status/error taxonomies; idempotency on `legal_object_version_id`; `force_reassembly`; provenance through citation; answer/retrieval boundaries.
  - `TASKS/TASK-006Y-CITATION-ASSEMBLY-CONTRACT.md` — task record.

### Notes

- Governance-only: no citation tables, workers, execution, retrieval, or answers.
- Complements TASK-004D assembler contract at `backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md`.
- TASK-006Z (persistence) remains planned, not authorized.

## [governance-legal-object-promotion-review-closed-citation-open] - 2026-06-03

### Changed

- Claude review TASK-006U–006X: **CLOSED** — verdict **APPROVED FOR CONTINUE**.
- Findings L-01, L-02, L-02b: **CLOSED** (L-02b via TASK-006X1).
- Canonical Legal Memory phase: **CLOSED**.
- Citation layer: **OPEN**.
- TASK-006Y: **AUTHORIZED** (citation assembly contract; governance-only).

### Notes

- OD-021 remains open/informational (concurrent worker race; single-worker acceptable).
- No citation persistence, answer generation, or retrieval runtime authorized.

## [task-006x1-legal-object-version-identity-hardening] - 2026-06-03

### Changed

- TASK-006X1: Claude review blocker L-02b — verified existing `UNIQUE(legal_object_id, text_hash)` as `uq_legal_object_versions_object_hash` (`b8d4e1a92c05`).
- Added tests: `test_legal_object_version_identity_hardening.py`, `test_legal_object_version_identity_alembic_migration.py`.
- Artifacts: `CLAUDE_VERIFICATION_LEGAL_OBJECT_VERSION_IDENTITY_006X1.md`, `TASKS/TASK-006X1-LEGAL-OBJECT-VERSION-IDENTITY-HARDENING.md`.

### Notes

- No new Alembic migration (constraint pre-existing).
- Full suite: **639 passed** (PostgreSQL `taxos_test`).
- Claude review 006U–006X remains **PENDING**; citation layer **NOT OPEN**; TASK-006Y **HOLD**.

## [task-006x-controlled-legal-object-promotion-execution] - 2026-06-03

### Added

- TASK-006X: controlled legal object promotion execution — first canonical legal memory from `parsed_structure`.
  - `ControlledLegalObjectPromotionProvider`, `materialize_legal_object_from_parsed_structure()`.
  - `run_controlled_legal_object_promotion()` requires `controlled_promotion=True`.
  - Identity `ps-{parsed_structure_id}`; replay appends `legal_object_version` with deterministic replay hash.
  - Tests: `test_controlled_legal_object_promotion_execution.py`.

### Notes

- Full suite: **633 passed** (PostgreSQL `taxos_test`).
- No citations, answers, AI, or legal interpretation.
- Dry-run worker (006W) regression preserved.

## [task-006w-legal-object-promotion-worker-skeleton] - 2026-06-03

### Added

- TASK-006W: legal object promotion worker skeleton (dry-run only).
  - `backend/app/workers/legal_object_promotion/` — worker, runner, dry-run provider, result types.
  - `run_legal_object_promotion_dry_run()` requires `dry_run=True`; non-dry-run rejected.
  - Dry-run terminal lifecycle: `accepted` → `skipped` with `legal_object_id` null (never `promoted`).
  - Tests: `test_legal_object_promotion_worker_skeleton.py`.

### Notes

- Full suite: **622 passed** (PostgreSQL `taxos_test`).
- OD-021: execution-time multi-worker race remains deferred to TASK-006X+.
- No legal objects, versions, citations, or answers created.

## [task-006v-legal-object-promotion-persistence] - 2026-06-02

### Added

- TASK-006V: legal object promotion persistence (governance records only; no execution).
  - Migration `b5c3e9a04d47`: `legal_object_promotion_requests`, `legal_object_promotion_results`, partial unique index on `parsed_structure_id` WHERE `force_repromotion = false`.
  - Service `backend/app/services/legal_object_promotion/`: deterministic `promotion_hash`, eligibility validation, append-only result history.
  - Tests: `test_legal_object_promotion_persistence.py`, `test_legal_object_promotion_alembic_migration.py`.

### Notes

- `legal_object_id` on results is nullable `String(64)` FK to `legal_objects.legal_object_id` (future handoff only).
- Full suite: **611 passed** (PostgreSQL `taxos_test`).
- No legal objects, citations, or answers created by this task.

## [task-006u-legal-object-promotion-contract] - 2026-06-02

### Added

- TASK-006U: legal object promotion governance contract (contract-only).
  - `LEGAL_OBJECT_PROMOTION_CONTRACT.md` — eligibility, request/result shapes, status/error taxonomy, idempotency on `parsed_structure_id`, `force_repromotion`, provenance, temporal alignment, citation boundary.
  - `TASKS/TASK-006U-LEGAL-OBJECT-PROMOTION-CONTRACT.md` — task record.

### Notes

- Doctrine: `parsed_structure` ≠ legal object; promotion is governed, not automatic parsing output.
- No persistence, workers, citations, or answers in this task.

## [governance-parsing-phase-closed-legal-memory-open] - 2026-06-02

### Changed

- Claude review TASK-006Q–006T: **CLOSED**.
- Claude verification TASK-006T1A: **VERIFIED**; P-01 and P-02 closed.
- **Legal-object promotion gate OPEN** after 006T1A verification.
- **TASK-006U** recorded as approved next — Legal Object Promotion Contract.
- Informational findings V-1, V-2 deferred; OD-021 carry-forward documented.

### Governance

- Doctrine: `parsed_structure` ≠ legal object (next phase); `parsed_structure` ≠ legal meaning (parsing phase).

## [task-006t1a-parsed-structure-identity-hardening] - 2026-06-02

### Changed

- TASK-006T1A: remediate Claude review P-01 — one `parsed_structure` per `parser_run`.
  - Migration `a4d2e8f93b36`: `UNIQUE(parsed_structures.parser_run_id)`
  - Service duplicate rejection in `persist_parsed_structure()` preserved and tested
  - Tests: `test_parsed_structure_identity_hardening.py`, `test_parsed_structure_identity_alembic_migration.py`

### Notes

- `sha256_structure()` reviewed; no redesign required.
- Legal-object promotion remains gated pending 006Q–006T review acknowledgment.

## [task-006t-controlled-parsing-execution-review-prep] - 2026-06-02

### Added

- `CLAUDE_REVIEW_PARSING_PIPELINE_006Q-T.md` — architecture review artifact for parsing pipeline 006Q–006T.
- `TASKS/TASK-006Q-T-PARSING-PIPELINE-REVIEWER-PACKAGE.md` — reviewer package index.

### Notes

- Legal-object promotion blocked until Claude review acknowledgment.

## [task-006t-controlled-parsing-execution] - 2026-06-02

### Added

- TASK-006T: controlled structural parsing execution.
  - `ControlledStructuralParsingProvider`, `structural.py` deterministic segmentation
  - `run_controlled_structural_parsing()` with explicit `controlled_structural=True` guard
  - Persists `parsed_structure` on success via existing ingestion persistence
  - Tests: `backend/tests/test_controlled_parsing_execution.py`

### Notes

- Structural evidence only; `parsed_structure` ≠ legal meaning.
- No legal object, citation, or answer side effects.

## [task-006s-parsing-worker-skeleton] - 2026-06-02

### Added

- TASK-006S: parsing worker skeleton (dry-run only).
  - `backend/app/workers/parsing/` — `ParsingWorker`, `DryRunParsingProvider`, `run_parsing_dry_run()`
  - Orchestrates parsing trigger → `parser_run` lifecycle + append-only trigger results
  - `extracted_text_has_completed_parsing()` replay guard unless `force_reparse=True`
  - Tests: `backend/tests/test_parsing_worker_skeleton.py`

### Notes

- No real parsing, `parsed_structure`, legal object, citation, or answer side effects.
- `dry_run=True` required for runner entrypoint.

## [task-006r-parsing-trigger-persistence] - 2026-06-02

### Added

- TASK-006R: parsing trigger persistence.
  - Tables: `parsing_trigger_requests`, `parsing_trigger_results`
  - Migration `f3b9c2e81a25` with partial unique index on `extracted_text_id` WHERE `force_reparse = false`
  - Service: `backend/app/services/parsing_trigger/` (hashing, validation, persistence)
  - Default `trigger_hash` from `extracted_text_id` only; `force_reparse` replay nonce pattern
  - Tests: `test_parsing_trigger_persistence.py`, `test_parsing_trigger_alembic_migration.py`

### Notes

- No parsing execution, parser worker, `parsed_structure`, legal object, citation, or answer side effects.
- `rerun_allowed` is policy metadata only; does not bypass idempotency.

## [task-006q-parsing-trigger-contract] - 2026-06-02

### Added

- TASK-006Q: parsing trigger governance contract (contract-only).
  - `PARSING_TRIGGER_CONTRACT.md` — eligibility, request/result shapes, status/error taxonomy, idempotency on `extracted_text_id`, rerun/force-reparse doctrine, handoff to `parser_run`, temporal alignment, OD-021 concurrency doctrine.
  - `TASKS/TASK-006Q-PARSING-TRIGGER-CONTRACT.md` — task record and acceptance checklist.

### Notes

- No parsing execution, parser worker, `parsed_structure` creation, legal-object/citation/answer generation, or temporal/legal interpretation.
- Doctrine: `parsed_structure` ≠ legal meaning.

## [task-006b-stability] - 2026-06-02

### Changed

- TASK-006B: test isolation and full-suite stability hardening.
  - `backend/tests/conftest.py`: explicit `TEST_DATABASE_URL` safety guard for destructive integration tests, test-DB name safety check, and nested transaction/savepoint fixture isolation.
  - `backend/app/services/legal_object_persistence/integrity_service.py`: removed broad rollback on expected rejected flows to avoid wiping test setup state.
  - `backend/app/services/legal_object_persistence/service.py`: duplicate-record creation moved after legal object creation to satisfy FK discipline.
  - `backend/app/services/effective_date/resolver.py`: deterministic ordering aligned with effective-date semantics.
  - `backend/tests/test_legal_object_alembic_migration.py`: downgrade assertion updated for post-006A head.

### Validation

- Ingestion suite: 12 passed.
- Legal-object integrity + retrieval focus: 27 passed.
- Full suite: 390 passed in 3 consecutive runs.
- Alembic head verified: `c9a2f3b81d06`.

## [0.2.1-task-002b] - 2026-05-30

### Added

- TASK-002B: structural source segmentation contract. New `backend/app/services/segmentation/` package with:
  - `Segment` / `SegmentationResult` / `SegmentMetadata` / `SegmentationMetadata` strict Pydantic models (`extra="forbid"`).
  - `SegmentType` enum (`document`, `part`, `chapter`, `section`, `article`, `clause`, `subclause`, `paragraph`, `schedule`, `unknown`) and `SegmentationStatus` enum (`pending` / `success` / `failed` / `partial`).
  - `BaseSegmenter` interface (`can_handle`, `segment`) with mandatory `name` / `version`.
  - Fully implemented deterministic `GenericSegmenter` with offset tracking, structural typing, and parent/child hierarchy.
  - Skeleton `LegislativeSegmenter` raising `NotImplementedError`.
  - `SEGMENTATION_CONTRACT.md` documentation.
- No database persistence introduced (contract + segmentation behavior only).

## [0.2.0-task-002a] - 2026-05-30

### Added

- TASK-002A: source text extraction contract. New `backend/app/services/extraction/` package with:
  - `ExtractionResult` / `ExtractionMetadata` Pydantic models (`extra="forbid"`, non-interpretive).
  - `ExtractionStatus` enum restricted to `pending` / `success` / `failed` / `partial`.
  - `sha256_text` integrity hashing over raw extracted text.
  - `BaseExtractor` interface (`can_handle`, `extract`) with mandatory `name` / `version`.
  - Fully implemented `TxtExtractor` (faithful, deterministic; `PARTIAL` degrade on invalid UTF-8).
  - Skeleton `PdfExtractor` / `HtmlExtractor` raising `NotImplementedError`.
  - `EXTRACTION_CONTRACT.md` documentation.
- No database persistence introduced (contract + pipeline structure only).

## [0.2.3-task-002c] - 2026-05-30

### Added

- TASK-002C: legal object extraction contract. New `backend/app/services/legal_objects/` package with:
  - `LegalObjectCandidate` / `LegalObjectExtractionResult` / `LegalObjectMetadata` / `LegalObjectExtractionMetadata` strict Pydantic models (`extra="forbid"`).
  - `LegalObjectType` enum (structural only: `act`, `regulation`, `order`, `notice`, `judgment`, `treaty`, `part`, `chapter`, `section`, `article`, `clause`, `subclause`, `paragraph`, `schedule`, `definition`, `unknown`) and `ExtractionStatus` enum (`pending` / `success` / `failed` / `partial`).
  - `BaseLegalObjectExtractor` interface (`can_handle`, `extract`) with mandatory `name` / `version`.
  - Fully implemented deterministic `GenericLegalObjectExtractor` (segment→object surface mapping, preserving offsets, sequencing, and parent/child hierarchy).
  - Skeleton `LegislativeLegalObjectExtractor` raising `NotImplementedError`.
  - `LEGAL_OBJECT_CONTRACT.md` documentation.
- No database persistence, migrations, or registry storage introduced (contract + deterministic extraction only).

## [0.2.4-task-002d] - 2026-05-30

### Added

- TASK-002D: canonical citation anchor contract. New `backend/app/services/citation_anchors/` package with:
  - `CanonicalCitationAnchor` / `CitationAnchorGenerationResult` / `CitationAnchorMetadata` / `CitationAnchorGenerationMetadata` strict Pydantic models (`extra="forbid"`).
  - `CitationAnchorType` enum (structural only) and `GenerationStatus` enum (`pending` / `success` / `failed` / `partial`).
  - `BaseCitationAnchorGenerator` interface (`can_handle`, `generate`) with mandatory `name` / `version`.
  - Fully implemented deterministic `GenericCitationAnchorGenerator`: structure-based canonical anchors (`<TYPE>:<normalized>` joined by `/` along ancestor lineage), SHA-256 `citation_anchor_id` over `source_version_id|legal_object_id|canonical_anchor|start_offset|end_offset`, deterministic `display_label`, and missing-parent fallback with observational warnings.
  - Skeleton `LegislativeCitationAnchorGenerator` raising `NotImplementedError`.
  - `CITATION_ANCHOR_CONTRACT.md` documentation.
- Anchors derive only from stable structural inputs (no DB IDs, UUID randomness, timestamps, AI, or raw-text hashing as primary anchor).
- No database persistence, migrations, or registry storage introduced (contract + deterministic generation only).

## [task-002e-complete] - 2026-05-30

### Added

- TASK-002E: cross-reference detection contract. New `backend/app/services/cross_reference/` package with:
  - `CrossReferenceResult` strict Pydantic model (`extra="forbid"`) with `source_version_id`, `source_location`, `reference_text`, `reference_type`, `target_candidate`, `confidence`, `detected_at`, `detector_version`.
  - `ReferenceType` enum (`section`, `article`, `regulation`, `schedule`, `part`, `chapter`, `act`, `law`, `guidance`, `case`, `treaty`, `unknown`) and deterministic `ReferenceConfidence` (`high`, `medium`, `low`).
  - `CrossReferenceDetector` with regex-based `detect()` — Section/Article/Regulation/Schedule/Part/Chapter patterns, range patterns (medium confidence), vague phrase patterns (low confidence), and surface `target_candidate` extraction from ``of the X Act`` phrases.
  - `CROSS_REFERENCE_CONTRACT.md` documentation.
- No database persistence, graph storage, or interpretation layer introduced (identify/record/link only).

## [task-002f-complete] - 2026-05-30

### Added

- TASK-002F: structural section parser contract. New `backend/app/services/structure_parser/` package with:
  - `StructuralUnit` strict Pydantic model (`extra="forbid"`) with hierarchy, offsets, heading fields, and `parser_version`.
  - `StructuralUnitType` enum (`act`, `law`, `title`, `part`, `chapter`, `section`, `article`, `regulation`, `schedule`, `paragraph`, `subparagraph`, `unknown`).
  - `StructuralParser.parse()` — regex-based line-start detection (Roman/Arabic numerals, lettered schedules), deterministic parent/child hierarchy, heading label/title split, offset and raw-text preservation.
  - `STRUCTURE_PARSER_CONTRACT.md` documentation.
- No database persistence or semantic interpretation introduced (document structure detection only).

## [task-002g-complete] - 2026-05-30

### Added

- TASK-002G: structural legal object extraction contract (proto-legal intelligence boundary). New `backend/app/services/legal_object_extraction/` package with:
  - `LegalObjectCandidate` strict Pydantic model (`extra="forbid"`) with `source_version_id`, deterministic `legal_object_id`, `canonical_path`, `parent_legal_object_id`, `structural_unit_id`, offsets, `raw_text`, SHA-256 `text_hash`, and extraction metadata.
  - `LegalObjectType` enum (`act`, `law`, `title`, `part`, `chapter`, `section`, `article`, `regulation`, `schedule`, `paragraph`, `subparagraph`, `definition`, `unknown`) and `LegalObjectExtractionStatus` enum (`success`, `partial`, `failed`, `unknown`).
  - `LegalObjectExtractor.extract()` — one candidate per `StructuralUnit`, deterministic type mapping, canonical path from structural lineage (` > ` separator), SHA-256 identity (`lo_<32-hex>`), parent resolution via prior candidates, `PARTIAL` on missing structural parent.
  - `LEGAL_OBJECT_EXTRACTION_CONTRACT.md` documentation.
- Consumes `StructuralUnit` from `structure_parser` only; no interpretation, persistence, or AI.
- Merged to main — tag `task-002g-merged`.

## [task-002h-complete] - 2026-05-30

### Added

- TASK-002H: legal object candidate convergence contract (OD-010 contract-level resolution). New `backend/app/services/legal_object_convergence/` package with:
  - `ConvergedLegalObjectCandidate` strict Pydantic model wrapping canonical `legal_object_extraction.models.LegalObjectCandidate`.
  - `ConvergenceSource` enum (`structural_unit`, `segment`, `legacy`, `unknown`) and `ConvergenceStatus` enum (`canonical`, `mapped`, `partial`, `rejected`).
  - `LegalObjectCandidateMapper` — structural pass-through as `CANONICAL`; segment/legacy mapping with canonical identity regeneration via `generate_legal_object_id`; explicit `REJECTED` for unmappable inputs.
  - `LegalObjectCandidateValidator` — required-field, text-hash, identity, offset, and duplicate-ID checks.
  - `LEGAL_OBJECT_CONVERGENCE_CONTRACT.md` documentation.
- Establishes persistence gate: all future legal object candidates must converge to one canonical shape before persistence planning.
- No database persistence, migrations, or CRUD introduced.
- Merged to main — tag `task-002h-merged`.

## [task-002i-complete] - 2026-05-30

### Added

- TASK-002I: legal object persistence planning contract (architecture governance only). New `backend/app/services/legal_object_persistence_planning/` package with:
  - `PlannedLegalObjectPersistenceModel` — Pydantic planning model (`extra="forbid"`); no DB bindings.
  - `contract.py` — canonical input rule: only `ConvergedLegalObjectCandidate`; blocked direct sources documented.
  - `rules.py` — explicit NEVER / ALWAYS persistence rules.
  - `duplicate_strategy.py`, `lineage_strategy.py`, `migration_plan.py`, `risks.py` — planning-only strategies, phased migration sequence, risk register, blocked assumptions.
  - `LEGAL_OBJECT_PERSISTENCE_PLANNING_CONTRACT.md` documentation.
- Establishes persistence governance boundary; **no tables, migrations, repositories, or CRUD**.
- Persistence implementation may not proceed until planning contract is architecturally approved.
- Merged to main — tag `task-002i-merged`.

## [task-003a-complete] - 2026-05-30

### Added

- TASK-003A: canonical legal object persistence schema contract (planning only). New `backend/app/services/legal_object_schema_contract/` package with:
  - Proposed table contracts: `legal_objects`, `legal_object_versions`, `legal_object_lineage`, `legal_object_duplicates`.
  - `schema_definition.py` — field-level Pydantic contract definitions (`extra="forbid"`).
  - `constraints.py`, `indexes.py`, `immutability.py`, `lineage.py` — intended DB constraints, indexes, immutability rules, lineage and duplicate assumptions, migration expectations.
  - `LEGAL_OBJECT_SCHEMA_CONTRACT.md` documentation.
- Input remains `ConvergedLegalObjectCandidate` only; **no SQLAlchemy, Alembic, repositories, or CRUD**.
- Merged to main — tag `task-003a-merged`.

## [task-003b-complete] - 2026-05-30

### Added

- TASK-003B: canonical legal object SQLAlchemy ORM models (definitions only). New `backend/app/models/` files:
  - `LegalObject`, `LegalObjectVersion`, `LegalObjectLineage`, `LegalObjectDuplicate`
  - Aligned with TASK-003A schema contract; `legal_object_id` externally supplied (no random PK default)
  - Models registered in `backend/app/models/__init__.py` for future Alembic discovery
- **No Alembic migrations**, repositories, CRUD APIs, or persistence services introduced.
- Merged to main — tag `task-003b-merged`.

## [task-003c-complete] - 2026-05-30

### Added

- TASK-003C: canonical legal object Alembic migration (`f7c2d9e41a83`). Creates PostgreSQL tables:
  - `legal_objects`, `legal_object_versions`, `legal_object_lineage`, `legal_object_duplicates`
  - Indexes per TASK-003A schema contract; `ck_legal_object_versions_offsets` check constraint
  - Circular FK (`current_version_id`) resolved via deferred FK after versions table creation
  - Downgrade drops tables in reverse dependency order
  - Legal object models imported in `backend/migrations/env.py`
  - `backend/tests/test_legal_object_alembic_migration.py` — migration structure and integration verification
- **No repositories, CRUD APIs, persistence services, or ingestion wiring.**
- Merged to main — tag `task-003c-merged`.

## [task-003d-complete] - 2026-05-30

### Added

- TASK-003D: legal object persistence repository contract. New `backend/app/services/legal_object_persistence/` package with:
  - `LegalObjectPersistenceService.persist()` — controlled write path from `ConvergedLegalObjectCandidate` only
  - `LegalObjectPersistenceRepository` — SQLAlchemy session pattern; creates `legal_objects` and `legal_object_versions` rows
  - `LegalObjectPersistenceResult` and `PersistenceStatus` enum (`created`, `version_created`, `duplicate_detected`, `rejected`, `failed`)
  - Duplicate detection by `legal_object_id` + `text_hash`; no auto-merge; immutable version fields preserved
  - `current_version_id` updated only after new version creation
  - `LEGAL_OBJECT_PERSISTENCE_REPOSITORY_CONTRACT.md` documentation
- **No CRUD APIs, ingestion wiring, batch jobs, or UI.**

## [task-003d-merged] - 2026-05-30

### Added

- TASK-003D merged to `main` — merge commit `82e2e79`.
- Controlled repository/service write path active: `LegalObjectPersistenceService.persist()` from `ConvergedLegalObjectCandidate` only.
- **`legal_object_lineage` and `legal_object_duplicates` table writes remain deferred** (explicit in project state; targeted by TASK-003E).

## [task-003e-complete] - 2026-05-30

### Added

- TASK-003E: legal object persistence integrity & immutability enforcement. Extends `backend/app/services/legal_object_persistence/` with:
  - `integrity_hash.py` — deterministic SHA-256 over stable fields; `text_hash` verification against `raw_text`
  - `immutability.py` — prohibits destructive updates and hard delete at repository layer
  - `traceability.py` — requires resolvable `source_version_id` and `source_document`
  - `status_enums.py` — governed statuses (`draft`, `active`, `superseded`, `archived`, `rejected`)
  - `LegalObjectIntegrityService` — `archive_legal_object`, `supersede_legal_object`, guarded `update_legal_object`
  - `audit.py` — lifecycle events written to `audit_log`
  - Enhanced `persist()` — lineage writes, cross-object duplicate records, transaction rollback
  - Alembic `b8d4e1a92c05` — status CHECK constraints + `UNIQUE (legal_object_id, text_hash)`
  - `LEGAL_OBJECT_PERSISTENCE_INTEGRITY_CONTRACT.md` documentation
- Feature branch: `feature/task-003e-legal-object-persistence-integrity` @ `52994a4`
- Tests: 225 passed, 91 skipped
- **No CRUD APIs, ingestion orchestration, UI, or answer engine.**

### Fixed

- Supersession trust-layer guards: reject when `persist()` does not return `CREATED`; reject self-referential `legal_object_id` supersession; rollback on rejection to prevent invalid lineage.

## [checkpoint-task-003e] - 2026-05-30

### Added

- TASK-003E merged to `main` — merge commit `0213fb1`.
- **Legal Object Persistence Integrity baseline frozen** at tag `checkpoint-task-003e`.
- Full persistence stack on `main`: 003A → 003B → 003C → 003D → 003E.
- **Next gate:** VM snapshot before TASK-004 series.

## [task-004a-complete] - 2026-05-30

### Added

- TASK-004A: legal object retrieval contract. New `backend/app/services/retrieval/` package with:
  - `LegalObjectRetrievalService` — `retrieve()`, `retrieve_by_id()`, `retrieve_active()`, `retrieve_effective()`
  - `LegalObjectRetrievalRequest` / `LegalObjectRetrievalResult` strict Pydantic models
  - Deterministic effective-date and status filtering; integrity verification on read
  - Source traceability preserved on every result (`source_document_id`, `source_version_id`, hashes)
  - `LEGAL_OBJECT_RETRIEVAL_CONTRACT.md` documentation
- Feature branch: `feature/task-004a-legal-object-retrieval-contract` @ `d604d96`
- Tests: 230 passed, 104 skipped
- **No AI, semantic retrieval, embeddings, pgvector, RAG, answer generation, or CRUD APIs.**

## [checkpoint-task-004a] - 2026-05-30

### Added

- TASK-004A merged to `main` — merge commit `90357ff`.
- **Deterministic legal object retrieval** active at tag `checkpoint-task-004a`.
- Stack on `main`: 003A → 003B → 003C → 003D → 003E → 004A.

### Deferred

- Deterministic ordering hardening for `retrieve_by_id()` when `effective_on` is set and multiple version rows match.

### Notes

- VM snapshot not required before TASK-004B unless schema or persistence behavior changes.

## [task-004b-complete] - 2026-05-30

### Added

- TASK-004B: effective-date resolver contract. New `backend/app/services/effective_date/` package with:
  - `EffectiveDateResolver` — `resolve()`, `resolve_by_legal_object_id()`
  - `EffectiveDateResolutionRequest` / `EffectiveDateResolutionResult` strict Pydantic models
  - `ResolutionStatus` enum — applicable, not_applicable, ambiguous_overlap, missing_effective_date, integrity_failed
  - Deterministic date rule; ambiguous overlap flagged (addresses TASK-004A deferred hardening at resolver layer)
  - Reuses TASK-004A status filters and integrity verification on read
  - `EFFECTIVE_DATE_RESOLVER_CONTRACT.md` documentation
- Feature branch: `feature/task-004b-effective-date-resolver-contract` @ `e569d57`
- Tests: 232 passed, 115 skipped
- **No AI, RAG, embeddings, pgvector, citation assembly, answer generation, or API routes.**

## [checkpoint-task-004b] - 2026-05-30

### Added

- TASK-004B merged to `main` — merge commit `08efa3b`.
- **Effective-date resolver** active at tag `checkpoint-task-004b`.
- Stack on `main`: 003A → 003B → 003C → 003D → 003E → 004A → 004B.

### Deferred

- Overlap result metadata enrichment for `AMBIGUOUS_OVERLAP` results.
- Outer sort `created_at` parity hardening in resolver result ordering.
- TASK-004A: deterministic ordering hardening for `retrieve_by_id()` when `effective_on` is set.

### Notes

- VM snapshot not required before next TASK-004 task unless schema or persistence behavior changes.

## [task-004c-complete] - 2026-05-30

### Added

- TASK-004C: citation candidate contract. New `backend/app/services/citation_candidate/` package with:
  - `CitationCandidateBuilder` — `build()`, `build_from_retrieval_result()`, `build_from_resolution_result()`
  - `CitationCandidateRequest` / `CitationCandidate` strict Pydantic models
  - `CandidateStatus` enum — `ready`, `source_traceability_failed`, `integrity_failed`, `date_ambiguous`, `date_not_applicable`, `missing_effective_date`
  - Conservative resolution status mapping from TASK-004B (`APPLICABLE` → `ready`; ambiguous/missing-date cases never silently promoted)
  - Source traceability from `source_documents`, `source_versions`, `countries`, `tax_types`
  - Integrity verification reused from TASK-004A hash verification
  - Deterministic ordering inherited from retrieval/resolution — no ranking or authority weighting
  - `CITATION_CANDIDATE_CONTRACT.md` documentation
- Feature branch: `feature/task-004c-citation-candidate-contract` @ `2e419d8`
- Tests: 11 citation candidate tests; full suite 350 passed (PostgreSQL VM)
- **No final citation formatting, persistence, API routes, AI, RAG, embeddings, or schema changes.**

## [checkpoint-task-004c] - 2026-05-30

### Added

- TASK-004C merged to `main` — merge commit `1349eb7`.
- **Citation candidate preparation baseline frozen** at tag `checkpoint-task-004c`.
- Architectural review: **APPROVED FOR MERGE** (seven confirmations; blocker scan: NONE).
- Stack on `main`: 003A → 003B → 003C → 003D → 003E → 004A → 004B → 004C.

### Notes

- Forward-governance notes for TASK-004D recorded in `KNOWN_LIMITATIONS.md`.
- VM snapshot not required before TASK-004D unless schema or persistence behavior changes.

- VM snapshot not required before TASK-004D unless schema or persistence behavior changes.

## [task-004d-complete] - 2026-06-01

### Added

- TASK-004D: citation assembly contract. New `backend/app/services/citation/` package with:
  - `CitationAssembler` — `assemble()`, `assemble_by_request()` with explicit `legal_object_version_id` pin (no implicit latest)
  - `CitationFormatter` — deterministic display text, separate from assembly logic
  - `CitationResult` / `CitationAssemblyRequest` strict Pydantic models
  - `AuthorityType` enum — statute, regulation, guidance, public_ruling, private_ruling, case, tribunal, treaty, accounting_standard, other
  - Location reference construction — Section, Article, Regulation, Part, Chapter, Schedule, Paragraph, Clause, Subsection
  - `citation_hash` — SHA-256 over `source_version_id`, `legal_object_id`, `legal_object_version_id`, `location_reference` (AMENDMENT-A)
  - Source traceability enforcement — fails on missing source version or location reference
  - `CITATION_ASSEMBLY_CONTRACT.md` documentation
- Feature branch: `feature/task-004d-citation-assembly-contract` @ `e008fe7`
- Tests: 16 passed (PostgreSQL VM)
- **No answer generation, citation ranking, legal reasoning, AI, retrieval, persistence, API routes, or schema changes.**

### Pending

- ~~Architectural review, merge, tag (`checkpoint-task-004d`)~~ — **closed** (see `[checkpoint-task-004d]`)

## [task-004d-amendment-a] - 2026-06-01

### Changed

- TASK-004D-AMENDMENT-A: citation identity hardening (pre-merge, feature branch).
  - `CitationResult.legal_object_version_id` — mandatory output field
  - `citation_hash` includes `legal_object_version_id` (same `legal_object_id`, different version → different hash/id)
  - `SourceDocumentMismatchError` when `source_version.source_document_id` ≠ `legal_object.source_document_id`
  - Contract doc updated; 4 new tests (20 total citation tests on VM)
- **Merged with TASK-004D** — see `[checkpoint-task-004d]`

## [checkpoint-task-004d] - 2026-06-01

### Added

- TASK-004D merged to `main` — merge commit `0588637`.
- **Citation assembly governance checkpoint frozen** at tag `checkpoint-task-004d`.
- Citation assembly contract completed (`CitationAssembler`, `CitationFormatter`, `CitationResult`).
- Version-aware citation identity — `legal_object_version_id` on input and output; hash includes version pin (AMENDMENT-A).
- Lineage validation enforcement — `SourceDocumentMismatchError` for source document consistency.
- Deterministic citation hashing — reproducible `citation_hash` / `citation_id`.
- Architectural review completed — Claude verdict: **APPROVED FOR MERGE**.
- Stack on `main`: 003A → 003B → 003C → 003D → 003E → 004A → 004B → 004C → 004D.

### Notes

- Non-blocking citation follow-ups recorded in `OPEN_DECISIONS.md`.
- VM snapshot not required — no schema or persistence behavior changes.

- VM snapshot not required — no schema or persistence behavior changes.

## [task-005a-spec-complete] - 2026-06-01

### Added

- TASK-005A-SPEC: temporal & versioning architecture specification (documentation only).
  - `TEMPORAL_VERSIONING_ARCHITECTURE.md` — authoritative temporal architecture
  - `TASKS/TASK-005A-TEMPORAL-VERSIONING-ARCHITECTURE-SPEC.md` — approved task spec
  - Temporal philosophy, versioning philosophy, amendment chains, future law, as-of query model
  - Answer-date resolution contract `resolve_authorities_as_of()` — specified, not implemented
  - Conflict preservation rules; version selection governance (never assume latest)
- Feature branch: `feature/task-005a-temporal-versioning-architecture-spec`
- **No code, migrations, APIs, answer engine, or AI.**

### Pending

- Review and merge (documentation-only)

## [task-005b-complete] - 2026-06-01

### Changed

- TASK-005B: temporal resolution governance amendments following Claude architecture review (documentation only).
  - `ADDENDUM_V6_TEMPORAL_RESOLUTION_AND_VERSION_PINNING.md` — no silent inheritance, derived temporal status, transaction vs knowledge date, answer disclosure, `current_version_id` governance, citation temporal doctrine
  - `TEMPORAL_VERSIONING_ARCHITECTURE.md` v1.1.0 — cross-references and clarifications
  - `CITATION_ASSEMBLY_CONTRACT.md` — C1 governance resolution (no silent source-version date inheritance)
  - `TASK-005A-TEMPORAL-VERSIONING-ARCHITECTURE-SPEC.md` — Addendum V6 cross-reference
  - Known gap documented: `CitationAssembler` date fallback requires future code task
- **No code, schema, API, or test changes.**

## [task-005a-pre-merge-cleanup] - 2026-06-01

### Changed

- Pre-merge cleanup per final architectural assessment (documentation only):
  - **IMP-1:** Status vocabulary reconciliation — `source_versions`, `ingestion_status`, legal object statuses, derived temporal status
  - **IMP-2:** Total derived-status matrix (single-null-bound cases; default unknown with disclosure)
  - **IMP-3:** Terminology — transaction/applicability date only; removed "query date" from derivation semantics
  - **IMP-5:** TASK-004E registered — Citation Temporal Compliance Remediation (`TASK_REGISTRY`, `OPEN_DECISIONS` OD-016)
  - **Deferred tracked:** IMP-4 (OD-017), IMP-6 (OD-018)
- Architectural review: **APPROVED FOR MERGE**

## [task-doc-001] - 2026-06-01

### Added

- TASK-DOC-001: master status document realignment.
  - [CURRENT_STATUS.md](CURRENT_STATUS.md) — canonical high-level status
  - [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) — COMPLETE / APPROVED NEXT / DEFERRED / FUTURE
  - [ARCHITECTURE_PHASE_MAP.md](ARCHITECTURE_PHASE_MAP.md) — phase evolution for onboarding
  - TASK-006B resequencing documented (test stability supersedes draft Source Monitoring Agent 006B)
  - Temporal (005A–C), ingestion (006A), TEST-GAP-001, deferred TASK-004E

### Changed

- [PROJECT_STATE.md](PROJECT_STATE.md) — phase label corrected; pointers to canonical status docs
- [README.md](README.md) — documentation index and development status table updated

## [task-006a-complete] - 2026-06-01

### Added

- TASK-006A: source ingestion persistence layer.
  - Tables: `extraction_runs`, `extracted_texts`, `parser_runs`, `parsed_structures`, `ingestion_state_transitions`
  - Services: `backend/app/services/ingestion/` (append-only, SHA-256, governed pipeline artifact states)
  - Alembic: `c9a2f3b81d06`
  - Ingestion tests: 12/12 passed (PostgreSQL VM)

### Notes

- **TEST-GAP-001:** full-suite instability in legal-object integrity / retrieval tests during validation — see `OPEN_DECISIONS.md`. Next: **TASK-006B**.

## [task-006c-contract] - 2026-06-02

### Added

- TASK-006C: Source Monitoring Agent Contract (governance-only).
  - `SOURCE_MONITORING_AGENT_CONTRACT.md` — canonical monitoring boundary contract.
  - `TASKS/TASK-006C-SOURCE-MONITORING-AGENT-CONTRACT.md` — task-governance contract record.
  - Allowed/prohibited monitoring behavior, source allowlist contract shape, monitoring event contract, candidate-state model, confidence model, failure taxonomy.
  - Temporal no-inference alignment and explicit workflow boundary (`monitoring event` must not directly mutate production source truth).

### Changed

- Status/roadmap/phase docs aligned for TASK-006C:
  - `CURRENT_STATUS.md`
  - `IMPLEMENTATION_ROADMAP.md`
  - `ARCHITECTURE_PHASE_MAP.md`
  - `TASK_REGISTRY.md`
  - `PROJECT_STATE.md`

### Notes

- TASK-006C introduces no live agents, schedulers, crawlers, scraping, queues, persistence tables, or external traffic.

## [task-006d-monitoring-persistence] - 2026-06-02

### Added

- TASK-006D: source monitoring candidate persistence (no live monitoring).
  - Models/tables for:
    - `source_allowlist_entries`
    - `monitoring_attempts`
    - `monitoring_events`
    - `monitoring_candidates`
    - `monitoring_candidate_state_transitions`
  - Alembic migration: `d4b7f91e62a1` (revises `c9a2f3b81d06`)
  - Services: `backend/app/services/monitoring/`
    - `create_allowlist_entry()`
    - `create_monitoring_attempt()` / `complete_monitoring_attempt()` / `fail_monitoring_attempt()`
    - `create_monitoring_event()`
    - `create_monitoring_candidate()`
    - `transition_candidate_state()` / `get_candidate_current_state()`

### Governance

- Enforced explicit enum/status contracts from TASK-006C.
- Candidate transitions are append-only with actor/time/reason metadata.
- FK chain enforced: allowlist -> attempt -> event -> candidate -> transitions.
- No live monitoring, scraping, scheduling, external traffic, or ingestion auto-approval.

### Validation

- Monitoring targeted tests: 9 passed
- Full suite regression: 399 passed

## [task-006e-monitoring-worker-skeleton] - 2026-06-02

### Added

- TASK-006E: source monitoring worker skeleton (dry-run only).
  - `backend/app/workers/monitoring/`:
    - `worker.py` (`SourceMonitoringWorker`)
    - `runner.py` (`run_monitoring_dry_run`)
    - `dry_run_provider.py` (`MonitoringProvider`, `DryRunMonitoringProvider`)
    - `result.py` summary/result dataclasses
    - `__init__.py`

### Governance

- Dry-run safety guard enforced (`dry_run=True` required).
- Non-dry-run execution is rejected.
- Worker orchestrates persistence lifecycle only:
  - allowlist entry -> monitoring attempt -> synthetic event -> candidate
- No auto-approval to `approved_for_ingestion`.
- No external HTTP libraries/crawler/scraper logic introduced.

### Validation

- Monitoring worker + persistence targeted tests: 15 passed
- Full suite regression: 405 passed

## [task-006f-controlled-source-fetch-contract] - 2026-06-02

### Added

- TASK-006F: controlled source fetch contract (governance-only).
  - `CONTROLLED_SOURCE_FETCH_CONTRACT.md` — canonical fetch governance contract.
  - `TASKS/TASK-006F-CONTROLLED-SOURCE-FETCH-CONTRACT.md` — task governance record.
  - Fetch request/result contract fields, fetch statuses, error taxonomy, content-type policy, checksum doctrine, redirect governance, robots/terms discipline, security constraints, and review-before-ingestion workflow.

### Changed

- Status/roadmap/phase docs aligned for TASK-006F:
  - `CURRENT_STATUS.md`
  - `IMPLEMENTATION_ROADMAP.md`
  - `ARCHITECTURE_PHASE_MAP.md`
  - `TASK_REGISTRY.md`
  - `PROJECT_STATE.md`

### Notes

- TASK-006F introduces no live fetching, no external HTTP calls, no crawler/scraper/scheduler, and no ingestion automation.

## [task-006g-source-change-detection-contract] - 2026-06-02

### Added

- TASK-006G: source change detection engine contract (governance-only).
  - `SOURCE_CHANGE_DETECTION_ENGINE_CONTRACT.md` — canonical detection governance contract.
  - `TASKS/TASK-006G-SOURCE-CHANGE-DETECTION-ENGINE-CONTRACT.md` — task governance record.
  - Request/result contracts, detection status/change/confidence values, checksum doctrine, metadata/structural diff doctrine, duplicate and false-positive handling, temporal no-inference alignment, and review-before-source-version workflow.

### Changed

- Status/roadmap/phase docs aligned for TASK-006G:
  - `CURRENT_STATUS.md`
  - `IMPLEMENTATION_ROADMAP.md`
  - `ARCHITECTURE_PHASE_MAP.md`
  - `TASK_REGISTRY.md`
  - `PROJECT_STATE.md`

### Notes

- TASK-006G introduces no change-detection engine implementation, no live fetching, and no legal amendment/temporal interpretation.

## [task-006h-controlled-fetch-implementation] - 2026-06-02

### Added

- TASK-006H: controlled fetch implementation (dry-run + local fixture mode only).
  - New bounded fetch package: `backend/app/services/fetch/`
    - `contract.py` (`FetchRequest`, `ControlledFetcher`)
    - `result.py` (`FetchResult`)
    - `dry_run_fetcher.py` (`DryRunFetcher`)
    - `local_fixture_fetcher.py` (`LocalFixtureFetcher`)
    - `safety.py` (scheme guards, mode guard, fixture-root/path traversal protection, max-size guard)
    - `checksum.py` (`sha256_bytes`)
    - `content_type.py` (approved content-type mapping/detection)
    - `fetcher.py` (`execute_fetch`)
  - New fixture files under `backend/tests/fixtures/fetch/` (`sample.txt`, `sample.html`, `sample.json`, `sample.xml`, `sample.bin`).
  - New targeted tests: `backend/tests/test_fetch_controlled_local_dry_run.py`.

### Validation

- `backend/tests/test_fetch_controlled_local_dry_run.py`: **13 passed**.

### Notes

- TASK-006H introduces no live HTTP/HTTPS fetching, no crawling/scraping, no source-version creation, and no legal-object creation.

## [task-006i-controlled-fetch-persistence] - 2026-06-02

### Added

- TASK-006I: controlled fetch result persistence (append-only).
  - New models:
    - `backend/app/models/fetch_request.py` (`fetch_requests`)
    - `backend/app/models/fetch_result.py` (`fetch_results`)
  - New Alembic revision:
    - `backend/migrations/versions/e2f4a1b9c8d7_create_fetch_persistence_tables.py`
  - New persistence service:
    - `backend/app/services/fetch/persistence.py`
    - `create_fetch_request()`, `persist_fetch_result()`, `get_fetch_request()`, `list_fetch_results_for_request()`, `get_latest_fetch_result_for_request()`
    - contract mappers: `create_persisted_fetch_request_from_contract()`, `persist_result_from_contract()`
  - Integrated model metadata:
    - `backend/app/models/__init__.py`
    - `backend/migrations/env.py`
  - New tests:
    - `backend/tests/test_fetch_persistence.py`
    - `backend/tests/test_fetch_alembic_migration.py`

### Validation

- `backend/tests/test_fetch_persistence.py backend/tests/test_fetch_alembic_migration.py`: **16 passed**.

### Notes

- TASK-006I introduces no live HTTP/HTTPS fetching, no source-version/extracted-text/legal-object creation, and no monitoring candidate auto-transition/auto-approval.

## [task-006j-change-detection-persistence] - 2026-06-02

### Added

- TASK-006J: source change detection persistence (append-only).
  - New models:
    - `backend/app/models/change_detection_request.py` (`change_detection_requests`)
    - `backend/app/models/change_detection_result.py` (`change_detection_results`)
  - New Alembic revision:
    - `backend/migrations/versions/f4c3b2a190de_create_change_detection_persistence_tables.py`
  - New persistence service package:
    - `backend/app/services/change_detection/persistence.py`
    - `backend/app/services/change_detection/__init__.py`
    - API: `create_change_detection_request()`, `persist_change_detection_result()`, `get_change_detection_request()`, `list_change_detection_results_for_request()`, `get_latest_change_detection_result_for_request()`
  - New tests:
    - `backend/tests/test_change_detection_persistence.py`
    - `backend/tests/test_change_detection_alembic_migration.py`

### Governance

- Review-required doctrine enforced in persistence validation:
  - `checksum_changed`, `metadata_changed`, `content_changed`, `structure_changed`, `removed_or_unavailable`, `new_artifact`, `unknown` **must** set `review_required=True`.
  - `no_change` and `duplicate_detected` may set `review_required=False`.
  - Invalid `review_required=False` for review-required types is **rejected**.

### Validation

- `backend/tests/test_change_detection_persistence.py backend/tests/test_change_detection_alembic_migration.py`: **14 passed**.

### Notes

- TASK-006J introduces no change-detection engine, no amendment/legal/temporal inference, no source-version creation, and no candidate auto-transition/auto-approval.

## [task-006k-change-detection-engine-skeleton] - 2026-06-02

### Added

- TASK-006K: source change detection engine skeleton (checksum-only).
  - New engine files in `backend/app/services/change_detection/`:
    - `engine.py` (`ChangeDetectionEngine` interface)
    - `checksum_engine.py` (`ChecksumChangeDetectionEngine`)
    - `result.py` (`ChecksumChangeDetectionRequest`, `ChangeDetectionEngineResult`)
  - Engine behavior:
    - compares persisted fetch-result checksums only
    - persists request/result using TASK-006J persistence service
    - bounded outcomes: `new_artifact`, `no_change`, `checksum_changed`, `unknown`
    - deterministic confidence: high/medium/low by checksum availability path
  - New tests:
    - `backend/tests/test_change_detection_engine_skeleton.py`

### Governance

- Checksum difference is acquisition-level change only; no legal interpretation.
- No textual/metadata/structural diff engine implemented.
- No source-version/extracted-text/legal-object/citation/answer creation side effects.

### Validation

- `backend/tests/test_change_detection_engine_skeleton.py`: **14 passed**.

### Notes

- TASK-006K introduces no live fetching/crawling/scraping and no amendment or temporal inference.

## [task-006l-controlled-source-version-promotion] - 2026-06-02

### Added

- TASK-006L: controlled source version promotion workflow.
  - New append-only model/table:
    - `backend/app/models/source_version_promotion.py` (`source_version_promotions`)
    - migration: `backend/migrations/versions/a7e6c9b4d201_create_source_version_promotions_table.py`
  - New promotion workflow package:
    - `backend/app/services/source_promotion/request.py`
    - `backend/app/services/source_promotion/result.py`
    - `backend/app/services/source_promotion/validation.py`
    - `backend/app/services/source_promotion/workflow.py`
    - `backend/app/services/source_promotion/errors.py`
    - `backend/app/services/source_promotion/__init__.py`
  - Workflow capabilities:
    - explicit review-gated promotion request handling
    - validation of fetch/source/provenance prerequisites
    - deterministic duplicate protection (`source_document_id + checksum_sha256`)
    - canonical `source_versions` creation only when validations pass
    - append-only promotion-history preservation for approved/rejected/duplicate paths (where FK-valid)
  - New tests:
    - `backend/tests/test_source_promotion_workflow.py`
    - `backend/tests/test_source_promotion_alembic_migration.py`

### Governance

- Promotion creates canonical source memory only; no automatic extraction, parsing, legal-object, or citation creation.
- Temporal no-inference preserved: no silent effective-date inference; absent dates remain null.
- Provenance references preserved in promotion history and source-version promotion notes.

### Validation

- `backend/tests/test_source_promotion_workflow.py backend/tests/test_source_promotion_alembic_migration.py`: **14 passed**.

### Notes

- TASK-006L introduces no live fetching, no autonomous approval/publication, and no legal interpretation.

## [task-006m-source-version-extraction-trigger-contract] - 2026-06-02

### Added

- TASK-006M: source-version extraction trigger contract (governance-only).
  - `SOURCE_VERSION_EXTRACTION_TRIGGER_CONTRACT.md` — canonical extraction-trigger governance contract.
  - `TASKS/TASK-006M-SOURCE-VERSION-EXTRACTION-TRIGGER-CONTRACT.md` — task governance record.
  - Trigger role definition, eligibility rules, request/result contracts, trigger statuses, error taxonomy, idempotency doctrine, rerun/force-reprocess doctrine, trigger-hash doctrine, handoff boundary, temporal no-inference alignment, and auditability/failure handling expectations.

### Changed

- Status/roadmap/phase docs aligned for TASK-006M:
  - `CURRENT_STATUS.md`
  - `IMPLEMENTATION_ROADMAP.md`
  - `ARCHITECTURE_PHASE_MAP.md`
  - `TASK_REGISTRY.md`
  - `PROJECT_STATE.md`
  - `README.md`

### Notes

- TASK-006M introduces no extraction execution, no queue/worker automation, and no parsing/legal-object/citation/answer generation.

## [task-006p1-extraction-replay-idempotency-hardening] - 2026-06-02

### Changed

- TASK-006P1: extraction replay and idempotency hardening (EXT-01 / OD-019).
  - `trigger_hash` for default triggers uses `source_version_id` only (not `trigger_reason`, actor, or `rerun_allowed`).
  - Partial unique DB index prevents duplicate default triggers per `source_version`.
  - Worker skips re-extraction when `source_version` already has a completed trigger result unless `force_reprocess=True`.
  - `rerun_allowed` documented/enforced as policy-only; does not bypass idempotency.
  - Optional DB hardening: unique `extracted_texts.extraction_run_id`, status CHECK constraints.

### Added

- Migration `e8c1d4f92a17`
- Tests: `test_extraction_replay_idempotency_hardening.py`, `test_extraction_replay_idempotency_alembic_migration.py`
- Task record: `TASKS/TASK-006P1-EXTRACTION-REPLAY-IDEMPOTENCY-HARDENING.md`

## [task-006p-controlled-extraction-execution] - 2026-06-02

### Added

- TASK-006P: controlled local extraction execution.
  - `ControlledLocalExtractionProvider` in `backend/app/workers/extraction/`
  - `safety.py` — artifact-root path resolution, traversal blocking, content-type validation, max-size guard
  - `content.py` — text/html/json/xml controlled text extraction (no PDF/OCR/browser)
  - `run_controlled_local_extraction()` runner with explicit `controlled_local=True` guard
  - Worker mode support: `dry_run` and `controlled_local`
  - On success: `extraction_run` + `extracted_text` persistence with checksum/provenance
  - On failure: failed `extraction_run` + failed trigger result, no `extracted_text`
  - New tests: `backend/tests/test_controlled_extraction_execution.py`

### Governance

- Supported types only: `text/plain`, `text/html`, `application/json`, `application/xml`.
- No external network access, PDF extraction, OCR, browser automation, or AI calls.
- No parsed_structure, legal_object, citation, or answer side effects.

### Validation

- `backend/tests/test_controlled_extraction_execution.py`: **16 passed** (including parametrized format cases).
- Full suite: **519 passed**.

### Notes

- TASK-006P produces raw text evidence only; it does not interpret legal meaning.

## [task-006o-extraction-worker-skeleton] - 2026-06-02

### Added

- TASK-006O: extraction worker skeleton (dry-run only).
  - New worker package: `backend/app/workers/extraction/`
    - `worker.py` (`ExtractionWorker`)
    - `runner.py` (`run_extraction_dry_run`)
    - `dry_run_provider.py` (`ExtractionProvider`, `DryRunExtractionProvider`)
    - `result.py` (`ExtractionProviderResult`, `ExtractionRunSummary`)
  - Worker behavior:
    - processes eligible extraction trigger requests only
    - orchestrates accepted → queued → started → completed/failed trigger results
    - creates `extraction_runs` via ingestion persistence in dry-run mode
    - enforces idempotency (skip completed unless `force_reprocess=True`)
    - skips rejected/duplicate_rejected latest statuses
  - New tests: `backend/tests/test_extraction_worker_skeleton.py`

### Governance

- `dry_run=True` required; non-dry-run execution rejected.
- No network IO, OCR, PDF/HTML parsing, AI calls, or source content extraction.
- No `extracted_text`, `parsed_structure`, `legal_object`, or citation side effects.

### Validation

- `backend/tests/test_extraction_worker_skeleton.py`: **9 passed**.
- Full suite: **503 passed**.

### Notes

- TASK-006O introduces no real extractor execution and no ingestion automation beyond lifecycle orchestration records.

## [task-006n-extraction-trigger-persistence] - 2026-06-02

### Added

- TASK-006N: extraction trigger persistence (append-only).
  - New models:
    - `backend/app/models/extraction_trigger_request.py` (`extraction_trigger_requests`)
    - `backend/app/models/extraction_trigger_result.py` (`extraction_trigger_results`)
  - New Alembic revision:
    - `backend/migrations/versions/b3d7a9f1c204_create_extraction_trigger_persistence_tables.py`
  - New persistence service package:
    - `backend/app/services/extraction_trigger/hashing.py`
    - `backend/app/services/extraction_trigger/validation.py`
    - `backend/app/services/extraction_trigger/persistence.py`
    - `backend/app/services/extraction_trigger/__init__.py`
    - API: `create_extraction_trigger_request()`, `persist_extraction_trigger_result()`, `get_extraction_trigger_request()`, `list_trigger_results_for_request()`, `get_latest_trigger_result_for_request()`, `find_existing_trigger_by_hash()`
  - New tests:
    - `backend/tests/test_extraction_trigger_persistence.py`
    - `backend/tests/test_extraction_trigger_alembic_migration.py`

### Governance

- Deterministic trigger hash uses only stable fields (`source_version_id`, `trigger_reason`, `requested_by_actor_type`, `rerun_allowed`, `force_reprocess`).
- Duplicate request protection enforced by trigger hash when `force_reprocess=False`.
- `force_reprocess=True` explicitly bypasses duplicate prevention while preserving append-only audit history.
- No extraction execution or downstream artifact creation side effects.

### Notes

- TASK-006N introduces no worker/queue orchestration, no auto creation of `extraction_runs`, and no parsed/legal/citation/answer artifact generation.

## [checkpoint-task-005a-spec] - 2026-06-01

### Merged

- TASK-005A-SPEC + TASK-005B + pre-merge cleanup (TASK-005C consistency) merged to `main` via `--no-ff` merge `43c6ad0`.
- Checkpoint tag: `checkpoint-task-005a-spec`.
- `MERGE_SUMMARY_TASK-005A.md` — merge record (documentation only; no implementation).
- Stack on `main` extended: 005A-SPEC → temporal/versioning governance; 005B → Addendum V6 alignment.
- **No code, migrations, APIs, or resolver implementation.**

### Next

- TASK-004E — Citation Temporal Compliance Remediation (planned code task).

## [Unreleased]

### Added

- TASK-001L: `ingestion_status` on `source_versions`, governed transition service, `POST /source-versions/{id}/ingestion-status`, auto `queued` on upload, `superseded` on supersede.
- TASK-001M: `source_processing_jobs` table, queue service, internal enqueue/list/get/status APIs.
- TASK-001N: `POST /source-processing-jobs/claim-next`, lock metadata, concurrency-safe claim via `FOR UPDATE SKIP LOCKED`.
- TASK-001O: job complete/fail endpoints, `result_json`/`completed_by`/`failed_by`, ingestion status sync.
- TASK-001P: worker contract, `NoopProcessor`, `run_next_job_once` one-shot harness.

### Added (prior unreleased)

- TASK-001G: operational and governance documentation set (README, runbooks, workflows, project state).
- TASK-001F: pytest foundation, integration marker, skip guard, baseline API tests for registry CRUD and `source_versions` immutability.
- TASK-001H: storage abstraction, local filesystem backend, SHA-256 checksum utilities.
- TASK-001J: `POST /source-versions/{id}/upload` internal upload API.
- TASK-001K: attachment state helpers, `file_attached` / `attachment_status` on API responses, `SOURCE_ATTACHMENT_WORKFLOW.md`.

### Changed

- README consolidated and linked to documentation index.
- TASK-001I: `datetime.utcnow` replaced with timezone-aware `utc_now()`.
- Upload workflow enforces attachment state validation and rejects duplicate or inconsistent attachment.

## [0.1.1-crud-foundation] - 2026-05-27

### Added

- Internal admin CRUD APIs: `countries`, `tax-types`, `source-documents`, `source-versions`.
- Pydantic schemas and SQLAlchemy models for source registry entities.
- `source_versions` governance: create/list/retrieve only; PUT/DELETE return 405.

## [0.1.0] - 2026-05-27 (foundation)

### Added

- FastAPI application skeleton and health endpoint.
- PostgreSQL models and Alembic migration `fd6be8e34b7b` (source registry tables).
- Alembic migration infrastructure and discipline.

## v0.1.2 — Storage Foundation

Added:
- storage abstraction layer
- local filesystem storage backend
- SHA-256 checksum utilities
- safe path normalization
- overwrite protection
- storage unit tests

Verified:
42 tests passing
0 skipped
