# Canonical Legal Object Persistence Schema Contract

## Purpose

Define the canonical database schema contract for persisted legal objects before
any SQLAlchemy models or Alembic migrations are written.

This task is **schema planning only** — NOT implementation.

## Why this is gated

TASK-002H convergence and TASK-002I persistence planning established governance
boundaries. This contract translates planning into explicit table, constraint,
index, immutability, and lineage specifications for Phase 1 migration work.

## Canonical persistence input

The **only** approved upstream input remains:

`app.services.legal_object_convergence.models.ConvergedLegalObjectCandidate`

No direct persistence from segmentation, structure_parser, legal_object_extraction,
or legacy legal_objects.

## Proposed tables

### legal_objects

Stable identity record for canonical legal objects.

| Field | Purpose |
|-------|---------|
| legal_object_id | Canonical deterministic identity |
| source_document_id | Registry document reference |
| country_id | Jurisdiction |
| tax_type_id | Optional tax domain |
| object_type | Structural type label |
| canonical_path | Deterministic structural path |
| current_version_id | Active version pointer |
| status | Lifecycle status |
| created_at / updated_at | Audit timestamps |

### legal_object_versions

Immutable versioned text and metadata.

| Field | Purpose |
|-------|---------|
| legal_object_version_id | Version row identity |
| legal_object_id | Parent identity |
| source_version_id | Source version reference (required) |
| parent_legal_object_id | Structural parent |
| structural_unit_id | Upstream unit traceability |
| object_label / object_title | Heading metadata |
| start_offset / end_offset | Source text span |
| raw_text / text_hash | Immutable content |
| effective_from / effective_to | Temporal metadata (nullable) |
| version_status / extraction_status | Controlled status |
| created_at | Insert timestamp |

**Rule:** No update after creation except controlled status transitions.

### legal_object_lineage

Parent-child and supersession lineage.

| Field | Purpose |
|-------|---------|
| id | Row identity |
| legal_object_id | Subject object |
| parent_legal_object_id | Parent reference |
| supersedes_legal_object_id | Explicit supersession |
| superseded_by_legal_object_id | Reverse supersession link |
| relationship_type | parent_child / supersedes / etc. |
| source_version_id | Version context |
| created_at | Insert timestamp |

### legal_object_duplicates

Duplicate tracking without silent merge.

| Field | Purpose |
|-------|---------|
| id | Row identity |
| primary_legal_object_id | Canonical survivor |
| duplicate_legal_object_id | Flagged duplicate |
| duplicate_type | Classification label |
| text_hash_match | Hash equality flag |
| canonical_path_match | Path equality flag |
| resolution_status | Review outcome |
| created_at | Insert timestamp |
| notes | Observational notes |

## Constraints

See `constraints.py`. Key requirements:

- `legal_object_id` unique
- `legal_object_version_id` unique
- `source_version_id` required on versions
- `text_hash`, `raw_text`, `canonical_path` required
- offsets valid (`end_offset >= start_offset`)
- application-level: no unconverged persistence, no destructive overwrite

## Indexes

See `indexes.py`. Required indexes:

- `legal_objects(country_id, tax_type_id, object_type, canonical_path)`
- `legal_object_versions(source_version_id, text_hash)`
- `legal_object_versions(effective_from, effective_to)`
- `legal_object_lineage(parent_legal_object_id)`
- `legal_object_duplicates(primary_legal_object_id)`

## Immutability rules

See `immutability.py`. Version content fields are append-only. Corrections create
new version rows or controlled status transitions — never in-place text mutation.

## Lineage rules

See `lineage.py`. Parent-child and supersession must be explicit. Missing parent
lineage flagged. Lineage corruption is high severity. No silent merge.

## Duplicate handling assumptions

Tracked in `legal_object_duplicates` — never silent merge. See `lineage.py`
`DUPLICATE_HANDLING_ASSUMPTIONS`.

## Migration expectations

See `lineage.py` `MIGRATION_EXPECTATIONS`. First Alembic revision requires
approval of this contract. Phased: tables → lineage FKs → effective-date index.

## Module layout

```text
legal_object_schema_contract/
├── contract.py           # governance boundary, proposed table list
├── models.py             # SchemaFieldDefinition, SchemaTableDefinition
├── schema_definition.py  # four proposed table contracts
├── constraints.py        # intended DB and application constraints
├── indexes.py            # intended indexes
├── immutability.py       # immutability rules
└── lineage.py            # lineage rules, duplicate assumptions, migration expectations
```

## Out of scope

SQLAlchemy models, Alembic revisions, repositories, CRUD APIs, persistence
services, ingestion execution, citation persistence, effective-date execution.

## Limitations

- Field SQL types are contract labels only — exact PostgreSQL types deferred to migration task
- Effective-date indexing planned but execution deferred
- Cross-pipeline deduplication resolution deferred to persistence service task
