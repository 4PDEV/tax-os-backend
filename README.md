# TAX-OS Backend

Backend for the **Source-Referenced Business & Tax Research Platform**.

## Purpose

This repository provides deterministic backend infrastructure for:

- legal source registry
- immutable source versioning
- effective-date-aware source metadata
- audit logging foundation
- internal admin CRUD APIs for registry entities

The platform is built for operational auditability and source-backed research—not probabilistic outputs.

## Architecture Philosophy

- **Deterministic-first** — behavior is explicit and reproducible.
- **Source-referenced** — conclusions trace to versioned legal sources.
- **Immutable historical versions** — `source_versions` are append-only at the API layer.
- **Effective-date-aware** — temporal fields are first-class on versions.
- **Auditability** — changes must be traceable over time.
- **Bounded execution** — tasks implement only approved scope.

Architecture governance lives in the separate `tax-os-architecture` repository. This repo implements approved tasks only.

## Technology Stack

| Component | Version / tool |
|-----------|----------------|
| Python | 3.14+ (project venv) |
| FastAPI | 0.136.x |
| SQLAlchemy | 2.x |
| Alembic | 1.18.x |
| PostgreSQL | 16 |
| Pytest | 9.x |
| Docker | PostgreSQL / pgAdmin on VM |

## Repository Structure

```
tax-os-backend/
  alembic.ini
  requirements.txt
  pytest.ini
  backend/
    .env                 # local credentials (not committed)
    app/
      api/routes/        # countries, tax-types, source-documents, source-versions
      core/              # settings
      db/                # session, dependencies
      models/
      schemas/
    migrations/
      versions/          # Alembic revisions
    tests/               # baseline API tests (integration marker)
```

## Current Development Status

**Canonical live status:** [CURRENT_STATUS.md](CURRENT_STATUS.md)

| Area | Status |
|------|--------|
| Retrieval layer (007A–007E) | **COMPLETE** |
| Ranking layer (008B–008D, U-01, 008A+) | **COMPLETE** |
| Answer assembly (009A) | **COMPLETE** |
| Answer persistence (009B) | **COMPLETE** |
| Answer worker (009C) | **COMPLETE** |
| Response runtime (010A) | **COMPLETE** — tag `v0.2.4-response-runtime` |
| Response runtime layer review (010A+) | **COMPLETE** — **ACCEPTED WITH FINDINGS** — tag `v0.2.6-response-runtime-layer-review` |
| API layer pre-auth (011A-PREAUTH) | **ACCEPTED WITH FINDINGS** — DEC-021 — tag `v0.2.7-api-layer-preauth` |
| Current next gate | **TASK-011A-IMPL-AUTH** |
| API layer implementation (011A) | **NOT AUTHORIZED** |
| API layer | **NOT AUTHORIZED** |
| FastAPI / public APIs | **NOT AUTHORIZED** |
| Queue infrastructure | **NOT AUTHORIZED** |
| AI answer generation | **NOT AUTHORIZED** |
| CitationAssembler | **NOT AUTHORIZED** |
| Narrative `answer_text` | **NOT AUTHORIZED** |
| Legal conclusions / recommendations | **NOT AUTHORIZED** |

**Repository traceability (confirmed):**

```text
dd91441 — feat: implement TASK-010A response runtime — tag v0.2.4-response-runtime
83037b6 — docs: record TASK-010A response runtime governance — tag v0.2.5-response-runtime-governance
```

`main` is up to date with `origin/main`; working tree clean at closeout.

| Area | Status |
|------|--------|
| Platform phase | Governed evidence → ranking → answer → response delivery stack (see [CURRENT_STATUS.md](CURRENT_STATUS.md)) |
| Alembic head | `c7e3a1f94d82` (answer persistence — TASK-009B) |
| Admin CRUD APIs | Operational (registry phase only) |
| Legal object / citation contracts | Merged on `main` (003A–004D) |
| Temporal governance | Merged (005A–005C); tag `checkpoint-task-005a-spec` |
| Ingestion artifact persistence | TASK-006A on `main` |

Initial jurisdiction focus: **Rwanda**. Initial tax domains: VAT, PAYE/PIT, WHT, corporate tax, capital gains, customs & excise (registry phase only).

## Setup Summary

1. Clone repository to VM (e.g. `/opt/tax-os/repos/tax-os-backend`).
2. Create Python venv and install dependencies — see [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md).
3. Configure `backend/.env` and start PostgreSQL (Docker) — see [OPERATIONAL_RUNBOOK.md](OPERATIONAL_RUNBOOK.md).
4. Run migrations: `alembic upgrade head` from repository root.
5. Start API: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000`.
6. Run tests with `TEST_POSTGRES_*` set — see [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md).

## Documentation Index

| Document | Purpose |
|----------|---------|
| [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) | Developer bootstrap |
| [OPERATIONAL_RUNBOOK.md](OPERATIONAL_RUNBOOK.md) | Day-to-day operations |
| [BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md) | Backup and restore |
| [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md) | Alembic discipline |
| [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) | AI-assisted dev governance |
| [TASK_EXECUTION_STANDARD.md](TASK_EXECUTION_STANDARD.md) | Task implementation rules |
| [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md) | Failure handling |
| [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) | Release discipline |
| [CURRENT_STATUS.md](CURRENT_STATUS.md) | **Canonical** high-level platform status (onboarding) |
| [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) | Authoritative task sequencing (COMPLETE / NEXT / DEFERRED) |
| [ARCHITECTURE_PHASE_MAP.md](ARCHITECTURE_PHASE_MAP.md) | Architecture phase evolution map |
| [PROJECT_STATE.md](PROJECT_STATE.md) | Detailed milestone history |
| [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) | Known gaps |
| [OPEN_DECISIONS.md](OPEN_DECISIONS.md) | Pending decisions |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | Test DB safety + deterministic suite commands |
| [TASK_REGISTRY.md](TASK_REGISTRY.md) | Task tracking |
| [TASKS/](TASKS/) | **Authoritative task specs (required for review)** |
| [SOURCE_ATTACHMENT_WORKFLOW.md](SOURCE_ATTACHMENT_WORKFLOW.md) | Source file attachment lifecycle |
| [SOURCE_PROCESSING_WORKFLOW.md](SOURCE_PROCESSING_WORKFLOW.md) | Processing queue and job finalization |
| [WORKER_CONTRACT.md](WORKER_CONTRACT.md) | Worker processor contract and no-op harness |
| [EXTRACTION_CONTRACT.md](EXTRACTION_CONTRACT.md) | Source text extraction contract and extractors |
| [SEGMENTATION_CONTRACT.md](SEGMENTATION_CONTRACT.md) | Structural source segmentation contract and segmenters |
| [LEGAL_OBJECT_CONTRACT.md](LEGAL_OBJECT_CONTRACT.md) | Legal object extraction contract and extractors |
| [CITATION_ANCHOR_CONTRACT.md](CITATION_ANCHOR_CONTRACT.md) | Canonical citation anchor contract and generators |
| [CROSS_REFERENCE_CONTRACT.md](CROSS_REFERENCE_CONTRACT.md) | Cross-reference detection contract and detector |
| [STRUCTURE_PARSER_CONTRACT.md](STRUCTURE_PARSER_CONTRACT.md) | Structural section parser contract and parser |
| [LEGAL_OBJECT_EXTRACTION_CONTRACT.md](backend/app/services/legal_object_extraction/LEGAL_OBJECT_EXTRACTION_CONTRACT.md) | Structural legal object extraction contract (structural units → candidates) |
| [LEGAL_OBJECT_CONVERGENCE_CONTRACT.md](backend/app/services/legal_object_convergence/LEGAL_OBJECT_CONVERGENCE_CONTRACT.md) | Legal object candidate convergence contract (OD-010; canonical shape enforcement) |
| [LEGAL_OBJECT_PERSISTENCE_PLANNING_CONTRACT.md](backend/app/services/legal_object_persistence_planning/LEGAL_OBJECT_PERSISTENCE_PLANNING_CONTRACT.md) | Legal object persistence planning contract (governance only; no implementation) |
| [LEGAL_OBJECT_SCHEMA_CONTRACT.md](backend/app/services/legal_object_schema_contract/LEGAL_OBJECT_SCHEMA_CONTRACT.md) | Canonical legal object persistence schema contract (planning only; no DB code) |
| [LEGAL_OBJECT_PERSISTENCE_REPOSITORY_CONTRACT.md](backend/app/services/legal_object_persistence/LEGAL_OBJECT_PERSISTENCE_REPOSITORY_CONTRACT.md) | Legal object persistence repository contract (controlled write path) |
| [LEGAL_OBJECT_PERSISTENCE_INTEGRITY_CONTRACT.md](backend/app/services/legal_object_persistence/LEGAL_OBJECT_PERSISTENCE_INTEGRITY_CONTRACT.md) | Legal object persistence integrity & immutability enforcement (TASK-003E) |
| [LEGAL_OBJECT_RETRIEVAL_CONTRACT.md](backend/app/services/retrieval/LEGAL_OBJECT_RETRIEVAL_CONTRACT.md) | Legal object retrieval contract — deterministic retrieval (TASK-004A) |
| [EFFECTIVE_DATE_RESOLVER_CONTRACT.md](backend/app/services/effective_date/EFFECTIVE_DATE_RESOLVER_CONTRACT.md) | Effective-date resolver contract — time-aware version resolution (TASK-004B) |
| [CITATION_CANDIDATE_CONTRACT.md](backend/app/services/citation_candidate/CITATION_CANDIDATE_CONTRACT.md) | Citation candidate contract — citation-ready DTO preparation (TASK-004C) |
| [backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md](backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md) | Citation assembler contract — deterministic source-backed citations (TASK-004D) |
| [TEMPORAL_VERSIONING_ARCHITECTURE.md](TEMPORAL_VERSIONING_ARCHITECTURE.md) | Temporal & versioning architecture — authoritative time/version spec (TASK-005A-SPEC) |
| [SOURCE_MONITORING_AGENT_CONTRACT.md](SOURCE_MONITORING_AGENT_CONTRACT.md) | Monitoring-agent governance contract (TASK-006C; contract-only) |
| [TASKS/TASK-006C-SOURCE-MONITORING-AGENT-CONTRACT.md](TASKS/TASK-006C-SOURCE-MONITORING-AGENT-CONTRACT.md) | TASK-006C contract record |
| [CONTROLLED_SOURCE_FETCH_CONTRACT.md](CONTROLLED_SOURCE_FETCH_CONTRACT.md) | Controlled fetch governance contract (TASK-006F; contract-only) |
| [TASKS/TASK-006F-CONTROLLED-SOURCE-FETCH-CONTRACT.md](TASKS/TASK-006F-CONTROLLED-SOURCE-FETCH-CONTRACT.md) | TASK-006F contract record |
| [SOURCE_CHANGE_DETECTION_ENGINE_CONTRACT.md](SOURCE_CHANGE_DETECTION_ENGINE_CONTRACT.md) | Source change-detection governance contract (TASK-006G; contract-only) |
| [TASKS/TASK-006G-SOURCE-CHANGE-DETECTION-ENGINE-CONTRACT.md](TASKS/TASK-006G-SOURCE-CHANGE-DETECTION-ENGINE-CONTRACT.md) | TASK-006G contract record |
| [SOURCE_VERSION_EXTRACTION_TRIGGER_CONTRACT.md](SOURCE_VERSION_EXTRACTION_TRIGGER_CONTRACT.md) | Source-version extraction trigger governance contract (TASK-006M; contract-only) |
| [TASKS/TASK-006M-SOURCE-VERSION-EXTRACTION-TRIGGER-CONTRACT.md](TASKS/TASK-006M-SOURCE-VERSION-EXTRACTION-TRIGGER-CONTRACT.md) | TASK-006M contract record |
| [PARSING_TRIGGER_CONTRACT.md](PARSING_TRIGGER_CONTRACT.md) | Parsing trigger governance contract from `extracted_text` (TASK-006Q; contract-only) |
| [CITATION_ASSEMBLY_CONTRACT.md](CITATION_ASSEMBLY_CONTRACT.md) | Ingestion-pipeline citation assembly governance from `legal_object` (TASK-006Y; contract-only) |
| [TASKS/TASK-006Y-CITATION-ASSEMBLY-CONTRACT.md](TASKS/TASK-006Y-CITATION-ASSEMBLY-CONTRACT.md) | TASK-006Y contract record |
| [ARCHITECTURE_REVIEW_CITATION_PERSISTENCE_006Z-PREAUTH.md](ARCHITECTURE_REVIEW_CITATION_PERSISTENCE_006Z-PREAUTH.md) | 006Z pre-auth review — APPROVED WITH REQUIRED REMEDIATION |
| [CITATION_PERSISTENCE_REMEDIATION_006ZA.md](CITATION_PERSISTENCE_REMEDIATION_006ZA.md) | TASK-006ZA planned persistence remediation |
| [CITATION_PERSISTENCE_006ZA_ACCEPTANCE_REVIEW.md](CITATION_PERSISTENCE_006ZA_ACCEPTANCE_REVIEW.md) | 006ZA acceptance **CLOSED** |
| [TASKS/TASK-006Z-CITATION-PERSISTENCE.md](TASKS/TASK-006Z-CITATION-PERSISTENCE.md) | TASK-006Z persistence record |
| `backend/app/services/citation_assembly_governance/` | TASK-006Z citation assembly governance persistence |
| [ARCHITECTURE_REVIEW_CITATION_WORKER_SKELETON_006AA-PREAUTH.md](ARCHITECTURE_REVIEW_CITATION_WORKER_SKELETON_006AA-PREAUTH.md) | TASK-006AA worker skeleton pre-auth review |
| [TASKS/TASK-006AA-CITATION-WORKER-SKELETON-PREAUTH-REVIEW.md](TASKS/TASK-006AA-CITATION-WORKER-SKELETON-PREAUTH-REVIEW.md) | TASK-006AA record |
| [TASKS/TASK-006AB-CITATION-WORKER-SKELETON.md](TASKS/TASK-006AB-CITATION-WORKER-SKELETON.md) | TASK-006AB dry-run worker |
| `backend/app/workers/citation_assembly_governance/` | TASK-006AB worker |
| [TASKS/TASK-006ZA-CITATION-PERSISTENCE-REMEDIATION-PACKAGE.md](TASKS/TASK-006ZA-CITATION-PERSISTENCE-REMEDIATION-PACKAGE.md) | TASK-006ZA task record |
| [LEGAL_OBJECT_PROMOTION_CONTRACT.md](LEGAL_OBJECT_PROMOTION_CONTRACT.md) | Legal object promotion governance from `parsed_structure` (TASK-006U; contract-only) |
| [TASKS/TASK-006U-LEGAL-OBJECT-PROMOTION-CONTRACT.md](TASKS/TASK-006U-LEGAL-OBJECT-PROMOTION-CONTRACT.md) | TASK-006U contract record |
| [TASKS/TASK-006V-LEGAL-OBJECT-PROMOTION-PERSISTENCE.md](TASKS/TASK-006V-LEGAL-OBJECT-PROMOTION-PERSISTENCE.md) | TASK-006V persistence record |
| [TASKS/TASK-006W-LEGAL-OBJECT-PROMOTION-WORKER-SKELETON.md](TASKS/TASK-006W-LEGAL-OBJECT-PROMOTION-WORKER-SKELETON.md) | TASK-006W worker skeleton record |
| [TASKS/TASK-006X-CONTROLLED-LEGAL-OBJECT-PROMOTION-EXECUTION.md](TASKS/TASK-006X-CONTROLLED-LEGAL-OBJECT-PROMOTION-EXECUTION.md) | TASK-006X controlled promotion execution record |
| [TASKS/TASK-006U-X-LEGAL-OBJECT-PROMOTION-REVIEWER-PACKAGE.md](TASKS/TASK-006U-X-LEGAL-OBJECT-PROMOTION-REVIEWER-PACKAGE.md) | Claude review package (006U–006X) |
| [CLAUDE_REVIEW_LEGAL_OBJECT_PROMOTION_006U-X.md](CLAUDE_REVIEW_LEGAL_OBJECT_PROMOTION_006U-X.md) | Claude review record — **CLOSED** (APPROVED FOR CONTINUE) |
| [CLAUDE_VERIFICATION_LEGAL_OBJECT_VERSION_IDENTITY_006X1.md](CLAUDE_VERIFICATION_LEGAL_OBJECT_VERSION_IDENTITY_006X1.md) | L-02b verification (TASK-006X1) |
| [TASKS/TASK-006X1-LEGAL-OBJECT-VERSION-IDENTITY-HARDENING.md](TASKS/TASK-006X1-LEGAL-OBJECT-VERSION-IDENTITY-HARDENING.md) | TASK-006X1 record |
| [TASKS/TASK-006Q-PARSING-TRIGGER-CONTRACT.md](TASKS/TASK-006Q-PARSING-TRIGGER-CONTRACT.md) | TASK-006Q contract record |
| `backend/app/services/parsing_trigger/` | TASK-006R parsing trigger persistence (append-only requests/results, trigger hash, idempotency) |
| [TASKS/TASK-006R-PARSING-TRIGGER-PERSISTENCE.md](TASKS/TASK-006R-PARSING-TRIGGER-PERSISTENCE.md) | TASK-006R task record |
| `backend/app/workers/parsing/` | TASK-006S/006T parsing worker (dry-run + controlled structural execution) |
| [TASKS/TASK-006S-PARSING-WORKER-SKELETON.md](TASKS/TASK-006S-PARSING-WORKER-SKELETON.md) | TASK-006S task record |
| [TASKS/TASK-006T-CONTROLLED-PARSING-EXECUTION.md](TASKS/TASK-006T-CONTROLLED-PARSING-EXECUTION.md) | TASK-006T task record |
| [TASKS/TASK-006T1A-PARSED-STRUCTURE-IDENTITY-HARDENING.md](TASKS/TASK-006T1A-PARSED-STRUCTURE-IDENTITY-HARDENING.md) | TASK-006T1A P-01 remediation |
| `backend/app/services/extraction_trigger/` | TASK-006N extraction trigger persistence service (append-only requests/results, trigger hash, idempotency checks) |
| `backend/app/workers/extraction/` | TASK-006O/006P extraction worker (dry-run orchestration + controlled local text extraction) |
| [CLAUDE_REVIEW_EXTRACTION_PIPELINE_006M-P.md](CLAUDE_REVIEW_EXTRACTION_PIPELINE_006M-P.md) | Architecture review — extraction pipeline 006M–006P |
| [CLAUDE_VERIFICATION_EXTRACTION_REPLAY_006P1.md](CLAUDE_VERIFICATION_EXTRACTION_REPLAY_006P1.md) | Verification only — 006P1 idempotency remediation (EXT-01 / OD-019) |
| [CLAUDE_REVIEW_PARSING_PIPELINE_006Q-T.md](CLAUDE_REVIEW_PARSING_PIPELINE_006Q-T.md) | Architecture review — parsing pipeline 006Q–006T (pending acknowledgment) |
| [CLAUDE_VERIFICATION_PARSED_STRUCTURE_IDENTITY_006T1A.md](CLAUDE_VERIFICATION_PARSED_STRUCTURE_IDENTITY_006T1A.md) | Verification only — 006T1A P-01 remediation |
| [TASKS/TASK-006Q-T-PARSING-PIPELINE-REVIEWER-PACKAGE.md](TASKS/TASK-006Q-T-PARSING-PIPELINE-REVIEWER-PACKAGE.md) | Reviewer package index for 006Q–006T |
| [TASKS/TASK-006M-P-EXTRACTION-PIPELINE-REVIEWER-PACKAGE.md](TASKS/TASK-006M-P-EXTRACTION-PIPELINE-REVIEWER-PACKAGE.md) | Reviewer package index for 006M–006P |
| `backend/app/services/fetch/` | TASK-006H controlled fetch implementation (dry-run + local fixture mode only) |
| `backend/app/services/fetch/persistence.py` | TASK-006I controlled fetch request/result persistence (append-only artifacts) |
| `backend/app/services/change_detection/` | TASK-006J change detection request/result persistence (append-only artifacts; no engine) |
| `backend/app/services/change_detection/checksum_engine.py` | TASK-006K checksum-only change detection engine skeleton (persisted fetch results only) |
| `backend/app/services/source_promotion/` | TASK-006L controlled source version promotion workflow (explicit review-gated canonical memory bridge) |

## Governance

- No direct database schema changes outside Alembic.
- No unbounded AI-driven architecture changes.
- Implementation follows bounded tasks with explicit acceptance criteria.
