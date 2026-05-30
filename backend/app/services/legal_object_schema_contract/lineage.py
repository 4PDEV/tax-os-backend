from enum import Enum


class LineageRelationshipType(str, Enum):
    """Proposed lineage relationship labels."""

    PARENT_CHILD = "parent_child"
    SUPERSEDES = "supersedes"
    SUPERSEDED_BY = "superseded_by"
    DUPLICATE_OF = "duplicate_of"


LINEAGE_RULES: tuple[str, ...] = (
    "parent-child lineage must be preserved via legal_object_lineage and parent_legal_object_id",
    "supersession must be explicit via supersedes_legal_object_id or superseded_by_legal_object_id",
    "no silent merge of duplicate legal objects — use legal_object_duplicates",
    "missing parent lineage must be flagged at persistence time (partial convergence)",
    "lineage corruption is high severity and must block batch commit",
    "lineage rows are append-only; supersession links do not mutate historical text",
    "cross-version lineage expressed via lineage table, not legal_object_id mutation",
)

DUPLICATE_HANDLING_ASSUMPTIONS: tuple[str, ...] = (
    "identical text_hash within source_version_id creates duplicate record, not overwrite",
    "identical canonical_path within source_version_id flagged for review",
    "conflicting legal_object_id for different content rejects persistence",
    "duplicate resolution_status tracks review outcome without deleting rows",
    "primary_legal_object_id is the canonical survivor; duplicate remains auditable",
)

MIGRATION_EXPECTATIONS: tuple[str, ...] = (
    "Phase 1 Alembic revision creates all four proposed tables with constraints",
    "Phase 2 adds lineage foreign-key enforcement and orphan checks",
    "Phase 3 adds effective-date composite index (no backfill mutation)",
    "Migrations must be reversible with data-preserving downgrade scripts",
    "No migration may alter immutable version column values",
    "Schema contract (TASK-003A) must be approved before first Alembic revision",
)


def lineage_rules_are_documented() -> bool:
    return len(LINEAGE_RULES) >= 4 and len(DUPLICATE_HANDLING_ASSUMPTIONS) >= 3
