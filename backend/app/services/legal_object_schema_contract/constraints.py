from dataclasses import dataclass
from enum import Enum


class ConstraintType(str, Enum):
    UNIQUE = "unique"
    NOT_NULL = "not_null"
    CHECK = "check"
    FOREIGN_KEY = "foreign_key"
    APPLICATION = "application"


@dataclass(frozen=True)
class SchemaConstraint:
    name: str
    constraint_type: ConstraintType
    table: str
    columns: tuple[str, ...]
    description: str


SCHEMA_CONSTRAINTS: tuple[SchemaConstraint, ...] = (
    SchemaConstraint(
        name="uq_legal_objects_legal_object_id",
        constraint_type=ConstraintType.UNIQUE,
        table="legal_objects",
        columns=("legal_object_id",),
        description="legal_object_id must be globally unique.",
    ),
    SchemaConstraint(
        name="uq_legal_object_versions_legal_object_version_id",
        constraint_type=ConstraintType.UNIQUE,
        table="legal_object_versions",
        columns=("legal_object_version_id",),
        description="legal_object_version_id must be globally unique.",
    ),
    SchemaConstraint(
        name="nn_legal_object_versions_source_version_id",
        constraint_type=ConstraintType.NOT_NULL,
        table="legal_object_versions",
        columns=("source_version_id",),
        description="source_version_id is required on every version row.",
    ),
    SchemaConstraint(
        name="nn_legal_object_versions_text_hash",
        constraint_type=ConstraintType.NOT_NULL,
        table="legal_object_versions",
        columns=("text_hash",),
        description="text_hash is required for integrity verification.",
    ),
    SchemaConstraint(
        name="nn_legal_object_versions_canonical_path",
        constraint_type=ConstraintType.NOT_NULL,
        table="legal_objects",
        columns=("canonical_path",),
        description="canonical_path is required on identity records.",
    ),
    SchemaConstraint(
        name="nn_legal_object_versions_raw_text",
        constraint_type=ConstraintType.NOT_NULL,
        table="legal_object_versions",
        columns=("raw_text",),
        description="raw_text is required and immutable after insert.",
    ),
    SchemaConstraint(
        name="chk_legal_object_versions_offsets",
        constraint_type=ConstraintType.CHECK,
        table="legal_object_versions",
        columns=("start_offset", "end_offset"),
        description="end_offset must be >= start_offset.",
    ),
    SchemaConstraint(
        name="fk_legal_object_versions_legal_object_id",
        constraint_type=ConstraintType.FOREIGN_KEY,
        table="legal_object_versions",
        columns=("legal_object_id",),
        description="legal_object_id references legal_objects.legal_object_id.",
    ),
    SchemaConstraint(
        name="fk_legal_object_lineage_legal_object_id",
        constraint_type=ConstraintType.FOREIGN_KEY,
        table="legal_object_lineage",
        columns=("legal_object_id",),
        description="lineage rows reference persisted legal_objects.",
    ),
    SchemaConstraint(
        name="app_no_unconverged_persistence",
        constraint_type=ConstraintType.APPLICATION,
        table="legal_object_versions",
        columns=(),
        description="Only ConvergedLegalObjectCandidate inputs may be persisted.",
    ),
    SchemaConstraint(
        name="app_no_destructive_overwrite",
        constraint_type=ConstraintType.APPLICATION,
        table="legal_object_versions",
        columns=("raw_text", "text_hash", "start_offset", "end_offset"),
        description="No in-place update of immutable version content fields.",
    ),
)


def constraints_for_table(table_name: str) -> tuple[SchemaConstraint, ...]:
    return tuple(c for c in SCHEMA_CONSTRAINTS if c.table == table_name)
