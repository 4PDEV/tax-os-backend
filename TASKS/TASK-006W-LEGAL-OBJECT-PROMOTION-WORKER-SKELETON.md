# TASK-006W — Legal Object Promotion Worker Skeleton

**Status:** Complete  
**Depends on:** TASK-006V  
**Module:** `backend/app/workers/legal_object_promotion/`

## Scope delivered

- `LegalObjectPromotionWorker` — orchestrates requests → append-only results
- `LegalObjectPromotionProvider` + `DryRunLegalObjectPromotionProvider`
- `run_legal_object_promotion_dry_run()` — requires `dry_run=True`
- Dry-run terminal status: **`skipped`** (not `promoted`; `legal_object_id` always null)
- Tests: `test_legal_object_promotion_worker_skeleton.py`

## Out of scope

- No legal object / version creation
- No citations or answers
- No controlled promotion execution (TASK-006X)

## Follow-on

| Task | Scope |
|------|--------|
| TASK-006X | Controlled legal object promotion execution |
