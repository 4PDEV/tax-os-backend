# Claude Verification — Legal Object Version Identity (TASK-006X1)

**Date:** 2026-06-03  
**Issue:** L-02b — DB-level uniqueness backstop for `legal_object_versions`  
**Verdict:** **VERIFIED** — `UNIQUE(legal_object_id, text_hash)` present at Alembic head

---

## Issue summary

Claude review 006U–006X required confirmation that duplicate authoritative versions cannot share the same `legal_object_id` and `text_hash` under concurrency. Service-level `get_version_by_text_hash()` alone is insufficient.

**Required:** `UNIQUE(legal_object_id, text_hash)` on `legal_object_versions`.

---

## Schema evidence

| Item | Detail |
|------|--------|
| Table | `legal_object_versions` |
| Constraint | `uq_legal_object_versions_object_hash` |
| Columns | `(legal_object_id, text_hash)` |
| Migration | `b8d4e1a92c05_add_legal_object_integrity_constraints.py` |
| Alembic head chain | … → `b8d4e1a92c05` → … → `b5c3e9a04d47` (promotion tables) |

**No new migration in 006X1** — constraint pre-existed; duplicate constraint not added.

---

## Repository behavior

| Function | Behavior |
|----------|----------|
| `create_version()` | Append-only INSERT |
| `get_version_by_text_hash()` | Pre-insert lookup; not a concurrency lock |
| `set_current_version()` | Updates `legal_objects.current_version_id` only |
| `materialize_legal_object_from_parsed_structure()` | Replay uses distinct `text_hash` when `force_repromotion=True` |

Duplicate `(legal_object_id, text_hash)` inserts fail at DB with `IntegrityError`.

---

## Tests executed

| Test file | Coverage |
|-----------|----------|
| `test_legal_object_version_identity_hardening.py` | DB duplicate rejection; repository lookup; force-repromotion distinct hashes |
| `test_legal_object_version_identity_alembic_migration.py` | Migration source evidence; constraint at head; downgrade/upgrade |
| `test_legal_object_integrity_migration.py` | Existing integrity migration contract |
| `test_legal_object_persistence_repository.py` | Service duplicate detection (pre-existing) |
| `test_controlled_legal_object_promotion_execution.py` | Promotion replay path (pre-existing) |

Full suite run at task completion (see CHANGELOG).

---

## L-02b status

| Finding | Status |
|---------|--------|
| L-02b DB uniqueness `(legal_object_id, text_hash)` | **VERIFIED / REMEDIATED** (pre-existing constraint + 006X1 tests) |

---

## Remaining risks

| ID | Risk | Notes |
|----|------|-------|
| OD-021 | Execution-time promotion race under multi-worker | Unchanged; separate from L-02b |

---

## Gate impact

- **Does not** close full Claude review 006U–006X by itself
- **Does** satisfy L-02b prerequisite for targeted Claude verification
- **Citation layer:** remains **NOT OPEN**
- **TASK-006Y:** **HOLD**

**Next:** Claude targeted verification of 006X1 artifact, then formal `APPROVED FOR CONTINUE` on 006U–006X review if no other blockers remain.
