# Verification Only — TASK-006P1 Extraction Replay & Idempotency (EXT-01 / F-05)

**Type:** Targeted remediation verification (not a full pipeline re-review)  
**Date:** 2026-06-02  
**Checkpoint:** `checkpoint-task-006p1-extraction-replay-idempotency` (`73cb921` on `main`)  
**Prior review:** [`CLAUDE_REVIEW_EXTRACTION_PIPELINE_006M-P.md`](CLAUDE_REVIEW_EXTRACTION_PIPELINE_006M-P.md)  
**Remediation spec:** [`TASKS/TASK-006P1-EXTRACTION-REPLAY-IDEMPOTENCY-HARDENING.md`](TASKS/TASK-006P1-EXTRACTION-REPLAY-IDEMPOTENCY-HARDENING.md)

---

## Request

Confirm EXT-01 / F-05 and OD-019 are remediated. Acknowledge TASK-006Q gate may open after this verification. Do **not** re-run the full 006M–006P architecture review.

---

## Blocker disposition

| Item | Pre-006P1 risk | Post-006P1 | Verified |
|------|----------------|------------|----------|
| **EXT-01 / F-05** | Idempotency keyed on request metadata; no DB unique on default triggers; race-prone app duplicate check | Canonical identity = `source_version_id`; partial unique index; worker skips completed `source_version` | **REMEDIATED** |
| **OD-019** | `rerun_allowed` implied bypass; worker only honored `force_reprocess` for terminal skip | `rerun_allowed` = policy metadata only; `force_reprocess=True` = explicit bypass | **RESOLVED** |

---

## Evidence checklist (spot-verify)

| # | Requirement | Implementation | Test |
|---|-------------|----------------|------|
| 1 | Default `trigger_hash` excludes `trigger_reason`, actor, `rerun_allowed`, timestamps | `hashing.py` — payload `{"source_version_id": ...}` only | `test_trigger_hash_stable_for_same_source_version` |
| 2 | DB rejects duplicate default trigger | Partial unique index `uq_extraction_trigger_requests_source_version_default` WHERE `force_reprocess = false` | `test_db_rejects_duplicate_default_trigger` (raw insert) |
| 3 | Service rejects duplicate default trigger | `find_default_trigger_for_source_version()` in `create_extraction_trigger_request()` | `test_duplicate_default_trigger_rejected_at_service` |
| 4 | Different `trigger_reason` / `rerun_allowed` cannot re-extract | Second trigger blocked or worker skip; no second `extraction_run` / `extracted_text` | `test_completed_extraction_not_repeated_with_different_trigger_metadata` |
| 5 | Worker eligibility at `source_version` level | `source_version_has_completed_extraction()` in `worker.py` | Same regression + worker skeleton tests |
| 6 | `force_reprocess=True` allows governed replay | Unique force hash + multiple force rows allowed at DB | `test_force_reprocess_allows_new_trigger_and_extraction` |
| 7 | Optional DB hardening | `UNIQUE(extracted_texts.extraction_run_id)`; status CHECK constraints | Alembic migration test `e8c1d4f92a17` |

**Suite at checkpoint:** 531 passed.

---

## Scope confirmation (unchanged)

- No parsing automation, `parsed_structures`, legal objects, citations, or answers added.
- Append-only trigger/request/result history preserved; force replay adds new rows by design.

---

## Deferred (not in 006P1 scope)

| ID | Item |
|----|------|
| OD-020 | `trigger_status=completed` vs text-ready (dry-run semantics) |
| R-01 (residual) | Application immutability only for some tables — unchanged class of ops risk |

---

## Verification verdict (for acknowledgment)

| Decision | Value |
|----------|-------|
| EXT-01 / F-05 | **REMEDIATED** |
| OD-019 | **RESOLVED** |
| TASK-006Q gate | **MAY OPEN** after reviewer acknowledgment of this verification |
| Full 006M–006P re-review | **NOT REQUIRED** |

---

## Sign-off template

| Role | Decision | Date |
|------|----------|------|
| Remediation verification | PENDING ACK | — |
| TASK-006Q | Blocked until row above signed | — |

---

*End of verification-only artifact — TASK-006P1.*
