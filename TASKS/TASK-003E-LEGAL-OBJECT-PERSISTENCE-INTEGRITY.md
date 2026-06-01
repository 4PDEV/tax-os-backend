# TASK-003E — LEGAL OBJECT PERSISTENCE INTEGRITY & IMMUTABILITY ENFORCEMENT

## STATUS

**COMPLETE / MERGED**

Merge commit: `0213fb1`  
Checkpoint tag: `checkpoint-task-003e`  
Feature branch (historical): `feature/task-003e-legal-object-persistence-integrity` @ `52994a4`

---

## 1. OBJECTIVE

Enforce legal-memory integrity and immutability on the controlled write path established in TASK-003D.

Legal objects are versioned, auditable records — not ordinary mutable database rows. This task closes the trust gap between “data was written” and “data can be trusted for retrieval, citation, and future answers.”

## 2. CORE PRINCIPLE

Allowed lifecycle:

```text
created → active → superseded → archived
```

Not allowed:

```text
created → silently edited → overwritten → deleted
```

## 3. POSITION IN ARCHITECTURE

```text
003A Schema Contract
003B SQLAlchemy ORM Models
003C Alembic Materialization
003D Controlled Write Path (repository)
003E Integrity & Immutability Enforcement  ← this task
004A+ Retrieval, effective-date, citation layers build on trusted persistence
```

**Canonical input rule (unchanged from 003D):** only `ConvergedLegalObjectCandidate` from `legal_object_convergence/` may enter the persistence write path.

## 4. CREATE / EXTEND MODULE

Extend:

```text
backend/app/services/legal_object_persistence/
```

Required additions:

| File | Role |
|------|------|
| `integrity_hash.py` | Deterministic SHA-256 over stable fields; `text_hash` verification |
| `immutability.py` | Prohibits destructive updates and hard delete at repository layer |
| `traceability.py` | Requires resolvable `source_version_id` and `source_document` |
| `status_enums.py` | Governed statuses |
| `audit.py` | Lifecycle events to `audit_log` |
| `integrity_service.py` | `LegalObjectIntegrityService` — archive, supersede, guarded update |
| `service.py` (enhanced) | `persist()` with hash, traceability, lineage, duplicates, rollback |
| `LEGAL_OBJECT_PERSISTENCE_INTEGRITY_CONTRACT.md` | Runtime contract documentation |

## 5. INTEGRITY HASHING

### Text hash

- `text_hash` must equal `SHA-256(raw_text)` before persistence is accepted.

### Content integrity hash

`compute_content_integrity_hash()` hashes **stable fields only**:

- `source_version_id`
- `object_type`
- structural identifier
- `raw_text`
- `effective_from`
- `effective_to`

**Excluded:** volatile fields (`created_at`, `updated_at`, database UUIDs).

Integrity hash is computed for verification; dedicated DB column persistence was deferred.

## 6. IMMUTABILITY RULES

### Version rows (`legal_object_versions`)

Immutable after creation:

- `raw_text`, `text_hash`, offsets, `source_version_id`, structural fields

### Legal object rows (`legal_objects`)

Governed updates only:

- `status` — via `LegalObjectIntegrityService` lifecycle paths
- `current_version_id` — only after a new version is created
- `updated_at` — metadata timestamp only

### Prohibited

- Hard delete at repository layer
- Destructive in-place edits to version content

## 7. STATUS DISCIPLINE

Governed `legal_objects.status` values:

- `draft`
- `active`
- `superseded`
- `archived`
- `rejected`

Enforced at application layer and database layer (Alembic `b8d4e1a92c05` CHECK constraints).

## 8. SOURCE TRACEABILITY

Before persistence:

- `source_version_id` must resolve to an existing `source_versions` row
- linked `source_document` must be resolvable

No orphan legal objects without source linkage.

## 9. SUPERSESSION WORKFLOW

`LegalObjectIntegrityService.supersede_legal_object()`:

1. Persists the superseding `ConvergedLegalObjectCandidate`
2. Marks the prior object `superseded` (prior version rows unchanged except object status)
3. Writes `legal_object_lineage` rows for `supersedes` and `superseded_by`

### Supersession trust-layer guards

- Reject when `persist()` does not return `CREATED`
- Reject self-referential `legal_object_id` supersession
- Rollback transaction on rejection to prevent invalid lineage

## 10. DUPLICATE HANDLING

| Condition | Behavior |
|-----------|----------|
| Same `legal_object_id` + same `text_hash` | `duplicate_detected` — no new version |
| Different `legal_object_id` + same `text_hash` in source version | `legal_object_duplicates` row with `resolution_status=pending`; persist may continue |

**No auto-merge.** Duplicate resolution logic remains out of scope (records only).

## 11. LINEAGE PERSISTENCE

TASK-003D deferred `legal_object_lineage` and `legal_object_duplicates` writes.

TASK-003E **implements** writes to:

- `legal_object_lineage` — `parent_child`, `supersedes`, `superseded_by`
- `legal_object_duplicates` — cross-object hash collision records

## 12. AUDIT LOGGING

Lifecycle events append to `audit_log`:

- create
- duplicate detected
- archive
- supersede

## 13. DATABASE MIGRATION

Alembic revision: `b8d4e1a92c05`

- `ck_legal_objects_status`
- `ck_legal_object_versions_version_status`
- `uq_legal_object_versions_object_hash` on (`legal_object_id`, `text_hash`)

## 14. TRANSACTION DISCIPLINE

On persistence failure:

- transaction rollback
- `PersistenceStatus.FAILED` returned
- no partial lineage or duplicate rows left in inconsistent state

## 15. TEST REQUIREMENTS

Integration tests covering:

- integrity hash verification on persist
- immutability / destructive update rejection
- supersession guards and rollback
- cross-object duplicate recording
- lineage writes on supersede
- migration constraint presence

Post-merge baseline: **225 passed, 91 skipped** (VM PostgreSQL).

## 16. OUT OF SCOPE

Do NOT add:

- CRUD APIs / FastAPI public routes
- ingestion orchestration or batch jobs
- UI or answer engine
- embeddings, semantic search, AI
- duplicate auto-merge or resolution workflows
- citation persistence
- topic classification

## 17. DOCUMENTED DEFERRALS (POST-MERGE)

Acceptable at this phase:

- direct SQL bypass risk (application-layer enforcement only)
- `audit_log.entity_id` UUID type mismatch for string `legal_object_id`
- integrity hash not stored as dedicated DB column
- secondary enum DB constraints (`extraction_status`, duplicate enums)
- duplicate resolution logic (records only; human review deferred)

## 18. ACCEPTANCE CRITERIA

TASK-003E complete when:

- integrity hashing operational on write path
- immutability enforced at repository layer
- source traceability validated before persist
- status discipline enforced (app + DB)
- supersession workflow with lineage writes and trust-layer guards
- duplicate and lineage tables written per rules
- Alembic constraints applied
- tests passing on VM
- contract documentation published
- merged to `main` with checkpoint tag `checkpoint-task-003e`

## 19. FINAL PRINCIPLE

Retrieval (004A), effective-date resolution (004B), citation candidates (004C), and citation assembly (004D) all assume **trusted, immutable, traceable legal memory**.

TASK-003E freezes that assumption into enforceable code and schema constraints.

Without integrity at the write boundary, every downstream layer inherits silent corruption risk.

---

## Related documents

| Document | Path |
|----------|------|
| Runtime integrity contract | `backend/app/services/legal_object_persistence/LEGAL_OBJECT_PERSISTENCE_INTEGRITY_CONTRACT.md` |
| Repository contract (003D) | `backend/app/services/legal_object_persistence/LEGAL_OBJECT_PERSISTENCE_REPOSITORY_CONTRACT.md` |
| Schema contract (003A) | `backend/app/services/legal_object_schema_contract/LEGAL_OBJECT_SCHEMA_CONTRACT.md` |

---

END OF TASK-003E
