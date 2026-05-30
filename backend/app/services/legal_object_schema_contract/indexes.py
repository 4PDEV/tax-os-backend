from dataclasses import dataclass
from enum import Enum


class IndexType(str, Enum):
    BTREE = "btree"
    COMPOSITE = "composite"
    UNIQUE = "unique"


@dataclass(frozen=True)
class SchemaIndex:
    name: str
    table: str
    columns: tuple[str, ...]
    index_type: IndexType
    description: str


SCHEMA_INDEXES: tuple[SchemaIndex, ...] = (
    SchemaIndex(
        name="ix_legal_objects_country_id",
        table="legal_objects",
        columns=("country_id",),
        index_type=IndexType.BTREE,
        description="Jurisdiction-scoped legal object lookup.",
    ),
    SchemaIndex(
        name="ix_legal_objects_tax_type_id",
        table="legal_objects",
        columns=("tax_type_id",),
        index_type=IndexType.BTREE,
        description="Tax domain filtering.",
    ),
    SchemaIndex(
        name="ix_legal_objects_object_type",
        table="legal_objects",
        columns=("object_type",),
        index_type=IndexType.BTREE,
        description="Structural type filtering.",
    ),
    SchemaIndex(
        name="ix_legal_objects_canonical_path",
        table="legal_objects",
        columns=("canonical_path",),
        index_type=IndexType.BTREE,
        description="Path-based lookup within jurisdiction scope.",
    ),
    SchemaIndex(
        name="ix_legal_object_versions_source_version_id",
        table="legal_object_versions",
        columns=("source_version_id",),
        index_type=IndexType.BTREE,
        description="Version lookup by source version.",
    ),
    SchemaIndex(
        name="ix_legal_object_versions_text_hash",
        table="legal_object_versions",
        columns=("text_hash",),
        index_type=IndexType.BTREE,
        description="Duplicate and integrity detection.",
    ),
    SchemaIndex(
        name="ix_legal_object_versions_effective_dates",
        table="legal_object_versions",
        columns=("effective_from", "effective_to"),
        index_type=IndexType.COMPOSITE,
        description="Temporal query support (execution deferred).",
    ),
    SchemaIndex(
        name="ix_legal_object_lineage_parent_legal_object_id",
        table="legal_object_lineage",
        columns=("parent_legal_object_id",),
        index_type=IndexType.BTREE,
        description="Parent-child lineage traversal.",
    ),
    SchemaIndex(
        name="ix_legal_object_duplicates_primary_legal_object_id",
        table="legal_object_duplicates",
        columns=("primary_legal_object_id",),
        index_type=IndexType.BTREE,
        description="Duplicate cluster lookup by primary object.",
    ),
)


def indexes_for_table(table_name: str) -> tuple[SchemaIndex, ...]:
    return tuple(idx for idx in SCHEMA_INDEXES if idx.table == table_name)
