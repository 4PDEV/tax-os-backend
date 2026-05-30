# Legal Object Persistence Integrity & Immutability Contract (TASK-003E)

## Purpose

Enforce legal-memory integrity on the controlled write path established in TASK-003D.
Legal objects are versioned, auditable records — not ordinary mutable database rows.

## Core principle

Allowed lifecycle:

```text
created → active → superseded → archived
```

Not allowed:

```text
created → silently edited → overwritten → deleted
```

## Scope

- Immutability enforcement on version content fields
- Deterministic content integrity hashing
- Source traceability validation
- Status discipline (`draft`, `active`, `superseded`, `archived`, `rejected`)
- Supersession workflow with lineage table writes
- Duplicate table writes on cross-object hash collision (no auto-merge)
- Transaction rollback on persistence failure
- Optional `audit_log` writes for lifecycle events
- Database CHECK and UNIQUE constraints (Alembic `b8d4e1a92c05`)

## Out of scope

- CRUD APIs and public routes
- Ingestion orchestration
- UI, answer engine, embeddings, topic classification
- Duplicate resolution logic (records only; review deferred)

## Modules

| Module | Role |
|--------|------|
| `integrity_hash.py` | Deterministic SHA-256 over stable fields |
| `immutability.py` | Guards against destructive updates and hard delete |
| `traceability.py` | Requires resolvable `source_version_id` / document |
| `status_enums.py` | Governed status values |
| `audit.py` | Appends `audit_log` rows for lifecycle events |
| `integrity_service.py` | `archive_legal_object`, `supersede_legal_object`, guarded `update_legal_object` |
| `service.py` | Enhanced `persist()` with hash, traceability, lineage, duplicates |

## Hash integrity

- `text_hash` must equal `SHA-256(raw_text)` before persistence
- `compute_content_integrity_hash()` hashes stable fields only:
  `source_version_id`, `object_type`, structural identifier, `raw_text`,
  `effective_from`, `effective_to`
- Volatile fields (`created_at`, `updated_at`, database ids) are excluded

## Immutability

Version rows are immutable after creation. Only `legal_objects.status`,
`current_version_id`, and `updated_at` may change through governed service paths.

Hard delete is prohibited at the repository layer.

## Supersession

`supersede_legal_object()`:

1. Persists the superseding converged candidate
2. Marks the prior object `superseded` (prior row unchanged except status)
3. Writes `legal_object_lineage` rows for `supersedes` and `superseded_by`

## Duplicate handling

- Same `legal_object_id` + `text_hash` → `duplicate_detected` (no new version)
- Different `legal_object_id` + same `text_hash` in source version →
  `legal_object_duplicates` row with `resolution_status=pending`; persist continues

No auto-merge.

## Database constraints

- `ck_legal_objects_status`
- `ck_legal_object_versions_version_status`
- `uq_legal_object_versions_object_hash` on (`legal_object_id`, `text_hash`)

## Canonical input rule (unchanged)

Only `ConvergedLegalObjectCandidate` from `legal_object_convergence/` may enter
the persistence write path.
