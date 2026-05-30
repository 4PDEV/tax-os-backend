from app.services.legal_object_schema_contract.models import (
    SchemaFieldDefinition,
    SchemaFieldType,
    SchemaTableDefinition,
)

LEGAL_OBJECTS_TABLE = SchemaTableDefinition(
    name="legal_objects",
    purpose="Stable identity record for canonical legal objects.",
    fields=[
        SchemaFieldDefinition(
            name="legal_object_id",
            field_type=SchemaFieldType.STRING,
            description="Canonical deterministic identity (lo_<sha256-prefix>).",
        ),
        SchemaFieldDefinition(
            name="source_document_id",
            field_type=SchemaFieldType.UUID,
            description="Registry source document reference.",
        ),
        SchemaFieldDefinition(
            name="country_id",
            field_type=SchemaFieldType.UUID,
            description="Jurisdiction reference.",
        ),
        SchemaFieldDefinition(
            name="tax_type_id",
            field_type=SchemaFieldType.UUID,
            nullable=True,
            description="Optional tax domain reference.",
        ),
        SchemaFieldDefinition(
            name="object_type",
            field_type=SchemaFieldType.ENUM,
            description="Structural legal object type label.",
        ),
        SchemaFieldDefinition(
            name="canonical_path",
            field_type=SchemaFieldType.STRING,
            description="Deterministic structural path from extraction lineage.",
        ),
        SchemaFieldDefinition(
            name="current_version_id",
            field_type=SchemaFieldType.UUID,
            nullable=True,
            description="Pointer to active legal_object_version row.",
        ),
        SchemaFieldDefinition(
            name="status",
            field_type=SchemaFieldType.ENUM,
            description="Lifecycle status (active, superseded, archived).",
        ),
        SchemaFieldDefinition(
            name="created_at",
            field_type=SchemaFieldType.TIMESTAMP,
            description="Row creation timestamp (UTC).",
        ),
        SchemaFieldDefinition(
            name="updated_at",
            field_type=SchemaFieldType.TIMESTAMP,
            description="Last controlled metadata update (not text mutation).",
        ),
    ],
)

LEGAL_OBJECT_VERSIONS_TABLE = SchemaTableDefinition(
    name="legal_object_versions",
    purpose="Immutable versioned text and metadata for legal objects.",
    fields=[
        SchemaFieldDefinition(name="legal_object_version_id", field_type=SchemaFieldType.UUID),
        SchemaFieldDefinition(name="legal_object_id", field_type=SchemaFieldType.STRING),
        SchemaFieldDefinition(name="source_version_id", field_type=SchemaFieldType.UUID),
        SchemaFieldDefinition(
            name="parent_legal_object_id",
            field_type=SchemaFieldType.STRING,
            nullable=True,
        ),
        SchemaFieldDefinition(name="structural_unit_id", field_type=SchemaFieldType.STRING),
        SchemaFieldDefinition(name="object_label", field_type=SchemaFieldType.STRING),
        SchemaFieldDefinition(
            name="object_title",
            field_type=SchemaFieldType.STRING,
            nullable=True,
        ),
        SchemaFieldDefinition(name="start_offset", field_type=SchemaFieldType.INTEGER),
        SchemaFieldDefinition(name="end_offset", field_type=SchemaFieldType.INTEGER),
        SchemaFieldDefinition(name="raw_text", field_type=SchemaFieldType.TEXT),
        SchemaFieldDefinition(name="text_hash", field_type=SchemaFieldType.STRING),
        SchemaFieldDefinition(
            name="effective_from",
            field_type=SchemaFieldType.DATE,
            nullable=True,
        ),
        SchemaFieldDefinition(
            name="effective_to",
            field_type=SchemaFieldType.DATE,
            nullable=True,
        ),
        SchemaFieldDefinition(name="version_status", field_type=SchemaFieldType.ENUM),
        SchemaFieldDefinition(name="extraction_status", field_type=SchemaFieldType.ENUM),
        SchemaFieldDefinition(name="created_at", field_type=SchemaFieldType.TIMESTAMP),
    ],
)

LEGAL_OBJECT_LINEAGE_TABLE = SchemaTableDefinition(
    name="legal_object_lineage",
    purpose="Preserve parent-child and supersession lineage.",
    fields=[
        SchemaFieldDefinition(name="id", field_type=SchemaFieldType.UUID),
        SchemaFieldDefinition(name="legal_object_id", field_type=SchemaFieldType.STRING),
        SchemaFieldDefinition(
            name="parent_legal_object_id",
            field_type=SchemaFieldType.STRING,
            nullable=True,
        ),
        SchemaFieldDefinition(
            name="supersedes_legal_object_id",
            field_type=SchemaFieldType.STRING,
            nullable=True,
        ),
        SchemaFieldDefinition(
            name="superseded_by_legal_object_id",
            field_type=SchemaFieldType.STRING,
            nullable=True,
        ),
        SchemaFieldDefinition(name="relationship_type", field_type=SchemaFieldType.ENUM),
        SchemaFieldDefinition(name="source_version_id", field_type=SchemaFieldType.UUID),
        SchemaFieldDefinition(name="created_at", field_type=SchemaFieldType.TIMESTAMP),
    ],
)

LEGAL_OBJECT_DUPLICATES_TABLE = SchemaTableDefinition(
    name="legal_object_duplicates",
    purpose="Track duplicate or near-duplicate candidates without silently merging.",
    fields=[
        SchemaFieldDefinition(name="id", field_type=SchemaFieldType.UUID),
        SchemaFieldDefinition(name="primary_legal_object_id", field_type=SchemaFieldType.STRING),
        SchemaFieldDefinition(name="duplicate_legal_object_id", field_type=SchemaFieldType.STRING),
        SchemaFieldDefinition(name="duplicate_type", field_type=SchemaFieldType.ENUM),
        SchemaFieldDefinition(name="text_hash_match", field_type=SchemaFieldType.BOOLEAN),
        SchemaFieldDefinition(name="canonical_path_match", field_type=SchemaFieldType.BOOLEAN),
        SchemaFieldDefinition(name="resolution_status", field_type=SchemaFieldType.ENUM),
        SchemaFieldDefinition(name="created_at", field_type=SchemaFieldType.TIMESTAMP),
        SchemaFieldDefinition(name="notes", field_type=SchemaFieldType.TEXT, nullable=True),
    ],
)

SCHEMA_TABLES: tuple[SchemaTableDefinition, ...] = (
    LEGAL_OBJECTS_TABLE,
    LEGAL_OBJECT_VERSIONS_TABLE,
    LEGAL_OBJECT_LINEAGE_TABLE,
    LEGAL_OBJECT_DUPLICATES_TABLE,
)


def get_table_definition(name: str) -> SchemaTableDefinition | None:
    for table in SCHEMA_TABLES:
        if table.name == name:
            return table
    return None
