# TASK-006V — Legal Object Promotion Persistence

**Status:** Complete — accepted at `checkpoint-task-006v-legal-object-promotion-persistence`  
**Depends on:** TASK-006U (contract)  
**Migration:** `b5c3e9a04d47`

## Scope delivered

- Tables: `legal_object_promotion_requests`, `legal_object_promotion_results`
- Service: `backend/app/services/legal_object_promotion/` (`hashing`, `validation`, `persistence`)
- Default idempotency: `parsed_structure_id`; partial unique index WHERE `force_repromotion = false`
- `promotion_hash` deterministic; force replay uses replay nonce (006P1/006R pattern)
- Tests: `test_legal_object_promotion_persistence.py`, `test_legal_object_promotion_alembic_migration.py`

## Out of scope (unchanged)

- No `legal_object` creation
- No promotion workers or execution
- No citations or answers

## Follow-on

| Task | Scope |
|------|--------|
| TASK-006W | Promotion worker skeleton (dry-run) |
| TASK-006X | Controlled promotion execution |
