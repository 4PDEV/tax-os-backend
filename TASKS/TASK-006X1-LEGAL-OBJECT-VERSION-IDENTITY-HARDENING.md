# TASK-006X1 — Legal Object Version Identity Hardening

**Status:** Complete  
**Prerequisite:** Claude review blocker L-02b  
**Migration added:** No — constraint already present

## Finding

`UNIQUE(legal_object_id, text_hash)` already exists on `legal_object_versions` from migration `b8d4e1a92c05` (`add_legal_object_integrity_constraints`).

| Property | Value |
|----------|--------|
| Constraint name | `uq_legal_object_versions_object_hash` |
| Columns | `legal_object_id`, `text_hash` |
| Introduced | TASK-003E era (`b8d4e1a92c05`) |

Claude suggested name `uq_legal_object_versions_object_text_hash` — semantically equivalent; **not renamed** to avoid redundant migration.

## Verification

- `backend/tests/test_legal_object_version_identity_hardening.py`
- `backend/tests/test_legal_object_version_identity_alembic_migration.py`
- [CLAUDE_VERIFICATION_LEGAL_OBJECT_VERSION_IDENTITY_006X1.md](../CLAUDE_VERIFICATION_LEGAL_OBJECT_VERSION_IDENTITY_006X1.md)

## Repository behavior (unchanged)

- `create_version()` — INSERT-only
- `get_version_by_text_hash()` — lookup helper; DB enforces under concurrency
- `set_current_version()` — repoints `current_version_id` only
- 006X `force_repromotion` — distinct replay `text_hash` via `sha256(structure_hash:request_id)`

## Gates after 006X1

- L-02b: **remediated / verified**
- Claude review 006U–006X: remains **PENDING** until targeted verification sign-off
- TASK-006Y: **HOLD**
