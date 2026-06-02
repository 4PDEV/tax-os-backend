# TASK-006M–006P — Extraction Pipeline Reviewer Package

**Purpose:** Single index for Claude (or human) architecture review of the governed extraction pipeline from promotion through controlled local extraction.

**Checkpoint tags on `main`:**
- `checkpoint-task-006m-extraction-trigger-contract`
- `checkpoint-task-006n-extraction-trigger-persistence`
- `checkpoint-task-006o-extraction-worker-skeleton`
- `checkpoint-task-006p-controlled-extraction`

**Review type:** Implementation + governance alignment (006M contract through 006P execution).

**Do not start TASK-006Q until this review is accepted.**

---

## 1. Governance contracts (read first)

| # | Artifact | Path |
|---|----------|------|
| 1 | Extraction trigger contract (006M) | [`SOURCE_VERSION_EXTRACTION_TRIGGER_CONTRACT.md`](../SOURCE_VERSION_EXTRACTION_TRIGGER_CONTRACT.md) |
| 2 | Temporal architecture | [`TEMPORAL_VERSIONING_ARCHITECTURE.md`](../TEMPORAL_VERSIONING_ARCHITECTURE.md) |
| 3 | Extraction contract (002A) | [`EXTRACTION_CONTRACT.md`](../EXTRACTION_CONTRACT.md) |
| 4 | Controlled fetch contract (006F) | [`CONTROLLED_SOURCE_FETCH_CONTRACT.md`](../CONTROLLED_SOURCE_FETCH_CONTRACT.md) |

---

## 2. Task records

| Task | Path |
|------|------|
| TASK-006M | [`TASKS/TASK-006M-SOURCE-VERSION-EXTRACTION-TRIGGER-CONTRACT.md`](TASK-006M-SOURCE-VERSION-EXTRACTION-TRIGGER-CONTRACT.md) |
| TASK-006N | *(implementation; see persistence below)* |
| TASK-006O | *(implementation; see worker below)* |
| TASK-006P | *(implementation; see controlled provider below)* |
| TASK-006A | ingestion persistence — [`CHANGELOG.md`](../CHANGELOG.md) `[task-006a-complete]` |
| TASK-006L | promotion — [`backend/app/services/source_promotion/`](../backend/app/services/source_promotion/) |

---

## 3. Implementation map (006N–006P)

### 006N — Trigger persistence

| Artifact | Path |
|----------|------|
| Models | [`backend/app/models/extraction_trigger_request.py`](../backend/app/models/extraction_trigger_request.py), [`extraction_trigger_result.py`](../backend/app/models/extraction_trigger_result.py) |
| Migration | [`backend/migrations/versions/b3d7a9f1c204_create_extraction_trigger_persistence_tables.py`](../backend/migrations/versions/b3d7a9f1c204_create_extraction_trigger_persistence_tables.py) |
| Services | [`backend/app/services/extraction_trigger/`](../backend/app/services/extraction_trigger/) |
| Tests | [`backend/tests/test_extraction_trigger_persistence.py`](../backend/tests/test_extraction_trigger_persistence.py) |

### 006O — Worker skeleton

| Artifact | Path |
|----------|------|
| Worker | [`backend/app/workers/extraction/worker.py`](../backend/app/workers/extraction/worker.py) |
| Dry-run provider | [`backend/app/workers/extraction/dry_run_provider.py`](../backend/app/workers/extraction/dry_run_provider.py) |
| Runner | [`backend/app/workers/extraction/runner.py`](../backend/app/workers/extraction/runner.py) |
| Tests | [`backend/tests/test_extraction_worker_skeleton.py`](../backend/tests/test_extraction_worker_skeleton.py) |

### 006P — Controlled extraction

| Artifact | Path |
|----------|------|
| Controlled provider | [`backend/app/workers/extraction/controlled_local_provider.py`](../backend/app/workers/extraction/controlled_local_provider.py) |
| Safety | [`backend/app/workers/extraction/safety.py`](../backend/app/workers/extraction/safety.py) |
| Content | [`backend/app/workers/extraction/content.py`](../backend/app/workers/extraction/content.py) |
| Tests | [`backend/tests/test_controlled_extraction_execution.py`](../backend/tests/test_controlled_extraction_execution.py) |

### 006A — Ingestion persistence (downstream artifacts)

| Artifact | Path |
|----------|------|
| Extraction run / extracted text | [`backend/app/services/ingestion/extraction_persistence.py`](../backend/app/services/ingestion/extraction_persistence.py) |
| Immutability | [`backend/app/services/ingestion/immutability.py`](../backend/app/services/ingestion/immutability.py) |
| Models | [`backend/app/models/extraction_run.py`](../backend/app/models/extraction_run.py), [`extracted_text.py`](../backend/app/models/extracted_text.py) |

### 006L — Promotion (upstream)

| Artifact | Path |
|----------|------|
| Workflow | [`backend/app/services/source_promotion/workflow.py`](../backend/app/services/source_promotion/workflow.py) |
| Validation | [`backend/app/services/source_promotion/validation.py`](../backend/app/services/source_promotion/validation.py) |
| Tests | [`backend/tests/test_source_promotion_workflow.py`](../backend/tests/test_source_promotion_workflow.py) |

---

## 4. Review focus checklist

- [ ] Idempotency / replay risks (trigger hash, worker skip rules, duplicate runs)
- [ ] Append-only guarantees (requests, results, runs, extracted_text)
- [ ] Extraction rerun governance (`rerun_allowed`, `force_reprocess`)
- [ ] Provenance preservation (promotion → source_version → artifact path)
- [ ] Hidden overwrite risks (DB updates, immutability enforcement gaps)
- [ ] Trigger / extraction_run / extracted_text consistency
- [ ] Temporal leakage (silent date inference, “latest” assumptions)
- [ ] Unsafe promotion-to-extraction assumptions
- [ ] Legal interpretation boundary (HTML/JSON handling ≠ legal parsing)

---

## 5. Review output

| Document | Path |
|----------|------|
| **Architecture review (this cycle)** | [`CLAUDE_REVIEW_EXTRACTION_PIPELINE_006M-P.md`](../CLAUDE_REVIEW_EXTRACTION_PIPELINE_006M-P.md) |
| **006P1 verification (EXT-01 / OD-019)** | [`CLAUDE_VERIFICATION_EXTRACTION_REPLAY_006P1.md`](../CLAUDE_VERIFICATION_EXTRACTION_REPLAY_006P1.md) |

---

## 6. Test evidence

Full suite at 006P checkpoint: **519 passed** (PostgreSQL VM, `TEST_DATABASE_URL`).

Targeted suites:

```bash
pytest backend/tests/test_extraction_trigger_persistence.py backend/tests/test_extraction_trigger_alembic_migration.py
pytest backend/tests/test_extraction_worker_skeleton.py
pytest backend/tests/test_controlled_extraction_execution.py
pytest backend/tests/test_source_promotion_workflow.py
pytest backend/tests/test_ingestion_persistence.py
```
