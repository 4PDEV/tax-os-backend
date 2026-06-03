# TASK-006W — Legal Object Promotion Worker Skeleton

**Status:** Complete — accepted (review 2026-06-03)  
**Depends on:** TASK-006V  
**Module:** `backend/app/workers/legal_object_promotion/`

## Scope delivered

- `LegalObjectPromotionWorker` — orchestrates requests → append-only results
- `LegalObjectPromotionProvider` + `DryRunLegalObjectPromotionProvider`
- `run_legal_object_promotion_dry_run()` — requires `dry_run=True`
- Dry-run terminal status: **`skipped`** (not `promoted`; `legal_object_id` always null)

### Dry-run `skipped` semantics (reviewer-critical)

`skipped` on a result row means **dry-run orchestration completed without promotion execution** — the worker accepted the request, invoked the provider, and recorded a terminal lifecycle outcome. It does **not** mean the request was ignored or ineligible.

Ineligible or terminal requests are never processed; they increment `requests_skipped` on the worker summary and do not receive a new `skipped` result from this path.
- Tests: `test_legal_object_promotion_worker_skeleton.py`

## Out of scope

- No legal object / version creation
- No citations or answers
- No controlled promotion execution (TASK-006X)

## Follow-on

| Task | Scope |
|------|--------|
| TASK-006X | Controlled legal object promotion execution |
