# Architecture Review — Parsing Pipeline (TASK-006Q through TASK-006T)

**Reviewer role:** Claude-style architecture review (post-checkpoint `checkpoint-task-006t-controlled-parsing-execution`)  
**Date:** 2026-06-02  
**Scope:** TASK-006Q, 006R, 006S, 006T; upstream TASK-006P/P1 (extraction); TASK-006A (`parsed_structures`); `PARSING_TRIGGER_CONTRACT.md`  
**Verdict:** **PENDING ACKNOWLEDGMENT** — submit for reviewer sign-off before legal-object promotion or parsing automation expansion

---

## Executive summary

The parsing pipeline from canonical `extracted_text` through parsing-trigger governance, persistence, dry-run orchestration, and controlled structural parsing is **architecturally sound and governance-bounded**. It mirrors the hardened extraction pattern (006P1) at the `extracted_text_id` canonical target.

**578 tests pass** at the 006T checkpoint. Dry-run and controlled-structural modes are explicitly gated. Controlled parsing reads **only** `extracted_text` in memory — no file I/O, network, OCR, PDF, or AI.

**Mandatory doctrine enforced in design:** `parsed_structure` ≠ legal meaning. Structural units (headings, articles, sections, schedules, clauses, paragraphs) are persisted as evidence; no tax effect, applicability, obligation, or legal-consequence fields are introduced.

**Primary residual:** OD-021 execution-time race under concurrent parsing workers (creation-time idempotency is DB-enforced; worker skip is `extracted_text`-level). Not a blocker for single-worker orchestration today.

**Gate:** Do **not** start legal-object promotion from parsing artifacts until this review is acknowledged.

---

## 1. Parsing replay / idempotency

### Strengths

| Mechanism | Behavior |
|-----------|----------|
| Default `trigger_hash` | SHA-256(`extracted_text_id`) only — excludes `trigger_reason`, actor, `rerun_allowed`, timestamps |
| DB uniqueness | Partial unique index `uq_parsing_trigger_requests_extracted_text_default` WHERE `force_reparse = false` |
| Service layer | `find_existing_default_trigger_for_extracted_text()` rejects duplicate default triggers |
| Worker skip | `extracted_text_has_completed_parsing()` skips unless `force_reparse=True` |
| Force replay | Unique hash per `force_reparse=True` row; append-only audit preserved |
| `rerun_allowed` | Policy metadata only; does **not** bypass idempotency (aligned with 006P1 extraction doctrine) |
| Tests | Service duplicate rejection, DB constraint bypass, worker completed-skip, force-reparse rerun |

### Risks (non-blocking)

| ID | Risk | Severity | Notes |
|----|------|----------|-------|
| P-01 | **Execution-time race (OD-021)** | LOW now / MEDIUM under concurrency | Two workers may both pass eligibility before either completes; mitigated today by sequential orchestration |
| P-02 | **Eligibility trusts trigger `completed` status** | LOW | Same class as extraction R-03; ops/DB bypass only |
| P-03 | **No DB unique on `parser_run` per `extracted_text`** | INFO | Replays create new `parser_run` rows by design when `force_reparse=True` |

**Comparison to extraction (006P1):** Parsing idempotency parity is **good**. Same three-layer pattern (app + worker + DB).

---

## 2. `parsed_structure` append-only guarantees

### Strengths

- `persist_parsed_structure()` rejects second structure for same `parser_run_id`
- Immutability helper `assert_parsed_structure_immutable` for field updates
- `structure_hash` from `sha256_structure(units)` — volatile metadata excluded from hash payload
- Failed parser runs do **not** create `parsed_structure`
- Force reparse creates new `parser_run` + new `parsed_structure` (append-only history)

### Risks (non-blocking)

| ID | Risk | Severity | Notes |
|----|------|----------|-------|
| A-01 | **Application-layer immutability only** | LOW | Direct SQL could mutate rows; same class as extraction/legal-object |
| A-02 | **No DB UNIQUE on `parsed_structures.parser_run_id` at migration f3b9c2e81a25** | LOW | Service enforces one-per-run; consider DB constraint in future hardening micro-task |

**Verdict:** Append-only doctrine **satisfied** at service boundary for TASK-006T scope.

---

## 3. Structural parsing boundary (no semantic / legal interpretation)

### Allowed (implemented)

- Line/regex structural heuristics: Article, Section, Schedule, numbered clauses, headings, paragraphs
- `structure_json` envelope: `parser_name`, `document`, `units`, `warnings`
- Unit fields: `unit_type`, offsets, `raw_text` spans — formatting/structure only

### Prohibited (verified absent in 006T scope)

- Legal interpretation, tax effect, applicability, amendment meaning
- Legal-object, citation, answer automation
- NLP/LLM/semantic classifiers, network, file reads, OCR, PDF parsing
- Forbidden-import scan in `test_controlled_parsing_execution.py`

### Risks (non-blocking)

| ID | Risk | Severity | Notes |
|----|------|----------|-------|
| B-01 | **Heuristic labels may imply legal semantics to humans** | INFO | e.g. `unit_type=article` is structural label only; document in operator training |
| B-02 | **`structure_json_extra` merges envelope at persistence** | INFO | Envelope is metadata; hash remains units-only — correct separation |

**Verdict:** Structural-only boundary **preserved**. Do not label 006T output as “parsed law” in downstream docs.

---

## 4. Provenance continuity

### Chain

```text
source_version → extraction_run → extracted_text
  → parsing_trigger_request → parser_run → parsed_structure
```

### Strengths

- `parsed_structure.source_version_id` derived from extraction run lineage
- `extracted_text_id` on all trigger requests/results
- Actor, reason, rerun/force flags on trigger requests
- `parser_run_id` on completed trigger results
- Pipeline state transition to `parsed` only after successful structure persist (requires prior `extracted` state)

### Gaps (non-blocking)

| ID | Gap | Severity | Notes |
|----|-----|----------|-------|
| PR-01 | **Trigger does not verify extraction trigger provenance** | LOW | Eligibility checks extraction run success + text presence only |
| PR-02 | **`structure_hash` ≠ `extracted_text.content_hash`** | INFO | Must not conflate text checksum with structure checksum |

**Verdict:** Provenance **adequate** for current phase.

---

## 5. OD-021 concurrency

| Layer | Parsing status |
|-------|----------------|
| Creation-time duplicate triggers | **DB + service enforced** (006R) |
| Worker eligibility skip | **`extracted_text_has_completed_parsing()`** (006S/006T) |
| Execution-time duplicate runs | **Not locked** — document before concurrent workers |

**Recommendation:** Before enabling concurrent parsing workers, add row/advisory locking or execution-level uniqueness aligned with 006P1 extraction hardening patterns.

---

## 6. Hidden overwrite risks

| Area | Risk | Finding |
|------|------|---------|
| `extracted_text.raw_text` | Immutable after create | Unchanged by parsing pipeline |
| `parsed_structure` rows | Append via new `parser_run` | No in-place overwrite in controlled flow |
| Trigger results | Append-only | Multiple results per request by design |
| Dry-run mode | No `parsed_structure` | Correct — lifecycle proof only |
| `source_versions` | Registry immutability | Unchanged |

**Verdict:** No **CRITICAL** hidden overwrite identified in 006Q–006T.

---

## 7. Task-by-task alignment

| Task | Intent | Implementation | Alignment |
|------|--------|----------------|-----------|
| **006Q** | Parsing trigger contract | `PARSING_TRIGGER_CONTRACT.md` | **YES** |
| **006R** | Trigger persistence + DB idempotency | Tables + services + partial unique index | **YES** |
| **006S** | Dry-run worker skeleton | `ParsingWorker` + `DryRunParsingProvider` | **YES** |
| **006T** | Controlled structural parsing | `ControlledStructuralParsingProvider` + `structural.py` | **YES** |

---

## 8. Blocker scan

| Severity | Count | Items |
|----------|-------|-------|
| CRITICAL | 0 | — |
| HIGH | 0 | — |
| MEDIUM | 0 | — (OD-021 deferred; not blocking single-worker) |
| LOW | 4 | P-01, P-02, A-01, A-02 |
| INFO | 3 | P-03, B-01, PR-02 |

---

## 9. Verdict and gate

### Recommended verdict: **APPROVED FOR CONTINUE** (pending acknowledgment)

The parsing pipeline is suitable to proceed **past the 006Q–006T review gate** for continued ingestion work, subject to:

1. **Do not** start legal-object promotion from `parsed_structure` until this review is acknowledged.
2. Record any new follow-ups in `OPEN_DECISIONS.md` (e.g. optional `UNIQUE(parsed_structures.parser_run_id)` if desired).
3. Keep consumer rule: `trigger_status=completed` ≠ legal meaning known; require `parsed_structure` join for structural evidence.

### Test confidence

- Full suite: **578 passed** at `checkpoint-task-006t-controlled-parsing-execution`
- Focus tests: `test_parsing_trigger_persistence.py`, `test_parsing_worker_skeleton.py`, `test_controlled_parsing_execution.py`

---

## 10. Sign-off template

| Role | Decision | Date |
|------|----------|------|
| Architecture review (006Q–006T) | PENDING ACK | — |
| Legal-object promotion gate | **BLOCKED** until row above signed | — |

---

*End of review — parsing pipeline TASK-006Q through TASK-006T.*
