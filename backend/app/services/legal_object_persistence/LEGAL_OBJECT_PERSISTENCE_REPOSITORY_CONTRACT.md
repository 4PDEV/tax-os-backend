# Legal Object Persistence Repository Contract

## Purpose

Define the controlled write-path for persisting `ConvergedLegalObjectCandidate`
records into canonical legal object PostgreSQL tables (TASK-003C).

This is the first **persistence execution** boundary — repository and service only.
No CRUD APIs, ingestion wiring, or UI.

## Canonical input rule

The **only** permitted input is:

`app.services.legal_object_convergence.models.ConvergedLegalObjectCandidate`

Enforced by `assert_converged_persistence_input()` in `contract.py`.

Direct writes from `segmentation`, `structure_parser`, `legal_object_extraction`,
or legacy `legal_objects` are **prohibited**.

## Write-path boundary

```text
ConvergedLegalObjectCandidate
→ LegalObjectPersistenceService.persist()
→ LegalObjectPersistenceRepository
→ legal_objects / legal_object_versions
```

## Persistence result

`LegalObjectPersistenceResult` reports:

- `persistence_status`: `created`, `version_created`, `duplicate_detected`, `rejected`, `failed`
- `created_legal_object` / `created_version` flags
- `duplicate_detected` and `warnings`

## Duplicate handling

| Condition | Behavior |
|-----------|----------|
| Same `legal_object_id` + `text_hash` | `duplicate_detected` — no new version |
| Same `canonical_path`, different hash | New version allowed with warning — no auto-merge |
| Duplicate resolution | **Out of scope** — no merge logic |

## Immutability handling

**Never updated** on existing version rows:

- `raw_text`, `text_hash`, offsets, `source_version_id`

**Allowed updates** on `legal_objects`:

- `current_version_id` — only after a new version is created
- `updated_at` — metadata timestamp only

## Rejected candidate handling

- Invalid input type → `rejected`
- `convergence_status=rejected` → `rejected`
- Missing `source_version` → `failed`

## Out of scope

- CRUD APIs / FastAPI routes
- Ingestion pipeline wiring
- Batch jobs
- Citation persistence
- Topic classification
- Answer generation / AI

## Module layout

```text
legal_object_persistence/
├── contract.py      # input governance
├── enums.py         # PersistenceStatus
├── models.py        # LegalObjectPersistenceResult
├── repository.py    # SQLAlchemy data access
└── service.py       # persist() orchestration
```

## Limitations

- `legal_object_lineage` and `legal_object_duplicates` tables not written yet
- Batch parent resolution deferred
- No cross-pipeline deduplication at persist time
