# Architecture Review — Extraction Pipeline (TASK-006M through TASK-006P)

**Reviewer role:** Claude-style architecture review (post-checkpoint `checkpoint-task-006p-controlled-extraction`)  
**Date:** 2026-06-02  
**Scope:** TASK-006M, 006N, 006O, 006P, 006A (ingestion artifacts), 006L (promotion upstream), `SOURCE_VERSION_EXTRACTION_TRIGGER_CONTRACT.md`  
**Verdict:** **APPROVED FOR CONTINUE** — no CRITICAL blockers; bounded follow-ups recorded before TASK-006Q

---

## Executive summary

The extraction pipeline from canonical `source_version` through trigger persistence, dry-run orchestration, and controlled local text extraction is **architecturally sound and governance-bounded**. Append-only discipline is consistently applied. The platform does not auto-create legal objects, citations, or answers. Controlled extraction produces **raw text evidence only**.

519 tests pass at the 006P checkpoint. Dry-run and controlled-local modes are explicitly gated. Safety guards block network paths, traversal, and unsupported binary/PDF types.

**Primary gap:** `rerun_allowed` is persisted and hashed but **not yet enforced** at worker eligibility (only `force_reprocess` bypasses terminal `completed` skip). This is a contract–implementation drift, not an immediate safety failure, because default behavior remains conservative (skip completed).

---

## 1. Idempotency and replay risks

### Strengths

| Mechanism | Behavior |
|-----------|----------|
| `trigger_hash` | Deterministic SHA-256 over stable fields (`source_version_id`, `trigger_reason`, `requested_by_actor_type`, `rerun_allowed`, `force_reprocess`); excludes timestamps and IDs |
| Duplicate trigger requests | `create_extraction_trigger_request()` rejects duplicate hash when `force_reprocess=False` |
| Worker skip | Latest `completed` / `failed` / `skipped` triggers skipped unless `force_reprocess=True` |
| `extracted_text` | One row per `extraction_run_id`; reruns create new runs |
| Tests | Duplicate trigger rejection, completed-not-reprocessed, force-reprocess rerun covered |

### Risks (non-blocking)

| ID | Risk | Severity | Notes |
|----|------|----------|-------|
| R-01 | **No DB unique constraint on `trigger_hash`** | LOW | Concurrent requests could race past application check; mitigated by single-worker orchestration today |
| R-02 | **`rerun_allowed` not enforced in worker** | MEDIUM | Contract 006M §Rerun: completed extraction may rerun when `rerun_allowed=true`; worker only honors `force_reprocess` for terminal skip |
| R-03 | **Eligibility trusts latest trigger status, not artifact truth** | LOW | If status were manually corrupted to `completed` without `extracted_text`, worker would skip; ops/DB bypass risk only |
| R-04 | **Multiple results per request on replay** | LOW | By design (append-only audit); consumers must use `get_latest_trigger_result_for_request()` |

**Recommendation before 006Q:** Implement worker check: if latest is `completed` and `request.rerun_allowed`, treat as eligible (still append-only new run/results).

---

## 2. Append-only guarantees

### Strengths

- `extraction_trigger_requests` / `extraction_trigger_results`: insert-only via services; no update/delete APIs
- `extraction_runs` / `extracted_texts`: created through ingestion persistence; immutability helpers for extracted text fields
- Failed runs and results preserved (not deleted)
- Promotion history (`source_version_promotions`) append-only

### Risks (non-blocking)

| ID | Risk | Severity | Notes |
|----|------|----------|-------|
| A-01 | **Application-layer immutability only** | LOW | Direct SQL could mutate rows; same class of risk as 003E |
| A-02 | **`extraction_runs` content_hash/raw_text_length backfilled on persist_extracted_text** | LOW | Single write path in controlled flow; not a silent overwrite of `raw_text` |

**Verdict:** Append-only doctrine **satisfied** at service boundary.

---

## 3. Extraction rerun governance

| Flag | Persistence | Worker behavior | Assessment |
|------|-------------|-----------------|------------|
| `force_reprocess` | In hash; allows duplicate trigger request | Bypasses terminal skip | **Correct** |
| `rerun_allowed` | In hash; stored on request | **Not read in `is_eligible()`** | **Drift from 006M** |

Force-reprocess audit trail is preserved: new trigger request row, new results, new `extraction_run`, new `extracted_text`.

**Verdict:** Rerun governance **mostly correct**; close R-02 before expanding automation.

---

## 4. Provenance preservation

### Chain

```text
monitoring → fetch → change detection → promotion (006L)
  → source_version (checksum, storage_path, mime_type)
  → extraction_trigger_request (006N)
  → extraction_run + extracted_text (006A / 006P)
```

### Strengths

- Promotion requires successful fetch, checksum, storage_path
- Controlled extraction resolves paths only under explicit `artifact_root`
- `extracted_text` stores `source_version_id`, `content_hash`, `extraction_run_id`
- Extractor identity recorded (`controlled_local_extraction_provider` / `dry_run_extraction_provider`)

### Gaps (non-blocking)

| ID | Gap | Severity | Notes |
|----|-----|----------|-------|
| P-01 | **Trigger does not FK-verify promotion/fetch** | LOW | Eligibility checks `source_version` only; deferred complex eligibility per 006N |
| P-02 | **`source_version.checksum_sha256` (artifact bytes) ≠ `extracted_text.content_hash` (text)** | INFO | Must not conflate; no automatic cross-check today |
| P-03 | **Storage path conventions** (`/fixtures/...`) require artifact_root alignment | LOW | Documented in tests; production root must be governed config |

**Verdict:** Provenance **adequate for current phase**; strengthen P-01 in a bounded eligibility task if needed.

---

## 5. Hidden overwrite risks

| Area | Overwrite risk | Finding |
|------|----------------|---------|
| `source_versions` | API immutability (405 on PUT/DELETE) | Unchanged by extraction pipeline |
| `extracted_text.raw_text` | Immutable after create | Enforced in persistence layer |
| Trigger results | Append-only | No update service |
| `extraction_run` | New row per attempt | Prior runs preserved |
| Dry-run SUCCESS without text | Pipeline state may not reach EXTRACTED | **Intentional** — no false “extracted” state without text |

**Verdict:** No **CRITICAL** hidden overwrite identified.

---

## 6. Trigger / extraction_run / extracted_text consistency

### Success path (controlled local)

1. Trigger results: `accepted` → `queued` → `started` → `completed`
2. `extraction_run`: `success` or `partial`, with `content_hash` / `raw_text_length` set when text persisted
3. `extracted_text`: one row linked to run; triggers `ingestion_state_transitions` → `extracted`

### Failure path

1. `extraction_run`: `failed` with `error_message`
2. Trigger result: `failed` with `error_category`
3. No `extracted_text`

### Dry-run path

1. `extraction_run`: `success` without `extracted_text`
2. Trigger: `completed` — lifecycle proof only

**Minor inconsistency (INFO):** Dry-run `completed` trigger implies lifecycle completion, not text availability. Consumers must not treat `trigger_status=completed` as “text ready” without checking `extracted_text` / `extraction_run.extractor_name`.

**Verdict:** **Consistent** if consumers gate on `extracted_text` presence.

---

## 7. Temporal leakage risks

| Check | Result |
|-------|--------|
| Silent effective-date inference in extraction | **None observed** |
| “Latest source_version” assumption | **None** — explicit `source_version_id` on all records |
| Temporal fields modified during extraction | **None** |
| Promotion temporal no-inference | **Preserved** (006L tests; null dates remain null) |

**Verdict:** Temporal governance **not violated** by 006M–006P.

---

## 8. Promotion-to-extraction assumptions

| Assumption | Safe? | Notes |
|------------|-------|-------|
| Promotion auto-triggers extraction | **No** — not implemented | Correct |
| Any promoted version extractable | **Partially** | Worker checks `version_status`; not fetch-review gate |
| Artifact at `storage_path` exists | **Runtime check** | Fails with `provenance_missing` / file not found |
| PDF promoted sources | **Fail controlled extraction** | `unsupported_source_type` — correct |

**Verdict:** No unsafe **automatic** promotion→extraction bridge. Manual/operational triggers still require valid artifact paths.

---

## 9. Legal interpretation boundary

| Component | Interpretation risk | Assessment |
|-----------|-------------------|------------|
| HTML handling | Tag stripping / `HTMLParser` text collection | **Formatting only** — not legal structure parsing |
| JSON | `json.dumps` canonicalization | **Serialization only** |
| XML | UTF-8 decode | **No semantic parse** |
| `extracted_text` | Raw text storage | **Non-interpretive** per 002A |
| Downstream | No `parsed_structure` / `legal_object` in 006M–006P | **Boundary intact** |

**Verdict:** Legal interpretation boundary **preserved**. HTML/JSON handling must not be labeled “parsing” in future docs.

---

## 10. Task-by-task alignment

| Task | Contract intent | Implementation | Alignment |
|------|-----------------|----------------|-----------|
| **006M** | Governance-only trigger boundary | Contract doc + enums in 006N | **YES** |
| **006N** | Persist requests/results, hash, idempotency | Tables + services + tests | **YES** (minus R-02) |
| **006O** | Dry-run orchestration only | `ExtractionWorker` + `DryRunExtractionProvider` | **YES** |
| **006P** | Controlled local text extraction | `ControlledLocalExtractionProvider` + safety | **YES** |
| **006A** | Append-only ingestion artifacts | Reused correctly | **YES** |
| **006L** | Review-gated promotion | Upstream; no auto-extraction | **YES** |

---

## 11. Blocker scan

| Severity | Count | Items |
|----------|-------|-------|
| CRITICAL | 0 | — |
| HIGH | 0 | — |
| MEDIUM | 1 | R-02 `rerun_allowed` worker enforcement |
| LOW | 5 | R-01, R-03, R-04, A-01, P-01, P-03 |
| INFO | 2 | P-02, dry-run completed semantics |

---

## 12. Verdict and gate

### Verdict: **APPROVED FOR CONTINUE**

The extraction pipeline is suitable to proceed **past the 006M–006P review gate**. Do **not** block on follow-ups, but **do not start TASK-006Q** until this review is acknowledged and R-02 is either implemented or explicitly deferred in `OPEN_DECISIONS.md`.

### Recommended actions (ordered)

1. **Record R-02** in `OPEN_DECISIONS.md` as OD-019 (or implement worker `rerun_allowed` check in a micro-task before 006Q).
2. **Document consumer rule:** `trigger_status=completed` ≠ answer-ready; require `extracted_text` join.
3. **006Q planning:** Any queue/scheduling must preserve explicit modes, append-only writes, and provenance checks.

### Test confidence

- Full suite: **519 passed** at `checkpoint-task-006p-controlled-extraction`
- Governance tests: no side effects on legal_object / parsed_structure / citations
- Forbidden import scans on worker package

---

## 13. Sign-off template

| Role | Decision | Date |
|------|----------|------|
| Architecture review | APPROVED FOR CONTINUE | 2026-06-02 |
| TASK-006Q gate | **OPEN** until R-02 disposition recorded | — |

---

*End of review — extraction pipeline TASK-006M through TASK-006P.*
