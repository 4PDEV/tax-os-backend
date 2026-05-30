"""create legal object persistence tables

Revision ID: f7c2d9e41a83
Revises: e5f2a8c31b74
Create Date: 2026-05-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f7c2d9e41a83"
down_revision: Union[str, Sequence[str], None] = "e5f2a8c31b74"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "legal_objects",
        sa.Column("legal_object_id", sa.String(length=64), nullable=False),
        sa.Column("source_document_id", sa.UUID(), nullable=False),
        sa.Column("country_id", sa.UUID(), nullable=False),
        sa.Column("tax_type_id", sa.UUID(), nullable=True),
        sa.Column("object_type", sa.String(length=50), nullable=False),
        sa.Column("canonical_path", sa.String(length=1024), nullable=False),
        sa.Column("current_version_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_document_id"], ["source_documents.id"]),
        sa.ForeignKeyConstraint(["country_id"], ["countries.id"]),
        sa.ForeignKeyConstraint(["tax_type_id"], ["tax_types.id"]),
        sa.PrimaryKeyConstraint("legal_object_id"),
    )
    op.create_index("ix_legal_objects_country_id", "legal_objects", ["country_id"])
    op.create_index("ix_legal_objects_tax_type_id", "legal_objects", ["tax_type_id"])
    op.create_index("ix_legal_objects_object_type", "legal_objects", ["object_type"])
    op.create_index("ix_legal_objects_canonical_path", "legal_objects", ["canonical_path"])

    op.create_table(
        "legal_object_versions",
        sa.Column("legal_object_version_id", sa.UUID(), nullable=False),
        sa.Column("legal_object_id", sa.String(length=64), nullable=False),
        sa.Column("source_version_id", sa.UUID(), nullable=False),
        sa.Column("parent_legal_object_id", sa.String(length=64), nullable=True),
        sa.Column("structural_unit_id", sa.String(length=255), nullable=False),
        sa.Column("object_label", sa.String(length=512), nullable=False),
        sa.Column("object_title", sa.String(length=1024), nullable=True),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("version_status", sa.String(length=50), nullable=False),
        sa.Column("extraction_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["legal_object_id"], ["legal_objects.legal_object_id"]),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.ForeignKeyConstraint(["parent_legal_object_id"], ["legal_objects.legal_object_id"]),
        sa.CheckConstraint("end_offset >= start_offset", name="ck_legal_object_versions_offsets"),
        sa.PrimaryKeyConstraint("legal_object_version_id"),
    )
    op.create_index(
        "ix_legal_object_versions_source_version_id",
        "legal_object_versions",
        ["source_version_id"],
    )
    op.create_index(
        "ix_legal_object_versions_text_hash",
        "legal_object_versions",
        ["text_hash"],
    )
    op.create_index(
        "ix_legal_object_versions_effective_dates",
        "legal_object_versions",
        ["effective_from", "effective_to"],
    )

    op.create_foreign_key(
        "fk_legal_objects_current_version_id",
        "legal_objects",
        "legal_object_versions",
        ["current_version_id"],
        ["legal_object_version_id"],
    )

    op.create_table(
        "legal_object_lineage",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("legal_object_id", sa.String(length=64), nullable=False),
        sa.Column("parent_legal_object_id", sa.String(length=64), nullable=True),
        sa.Column("supersedes_legal_object_id", sa.String(length=64), nullable=True),
        sa.Column("superseded_by_legal_object_id", sa.String(length=64), nullable=True),
        sa.Column("relationship_type", sa.String(length=50), nullable=False),
        sa.Column("source_version_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["legal_object_id"], ["legal_objects.legal_object_id"]),
        sa.ForeignKeyConstraint(["parent_legal_object_id"], ["legal_objects.legal_object_id"]),
        sa.ForeignKeyConstraint(["supersedes_legal_object_id"], ["legal_objects.legal_object_id"]),
        sa.ForeignKeyConstraint(["superseded_by_legal_object_id"], ["legal_objects.legal_object_id"]),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_legal_object_lineage_parent_legal_object_id",
        "legal_object_lineage",
        ["parent_legal_object_id"],
    )

    op.create_table(
        "legal_object_duplicates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("primary_legal_object_id", sa.String(length=64), nullable=False),
        sa.Column("duplicate_legal_object_id", sa.String(length=64), nullable=False),
        sa.Column("duplicate_type", sa.String(length=50), nullable=False),
        sa.Column("text_hash_match", sa.Boolean(), nullable=False),
        sa.Column("canonical_path_match", sa.Boolean(), nullable=False),
        sa.Column("resolution_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["primary_legal_object_id"], ["legal_objects.legal_object_id"]),
        sa.ForeignKeyConstraint(["duplicate_legal_object_id"], ["legal_objects.legal_object_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_legal_object_duplicates_primary_legal_object_id",
        "legal_object_duplicates",
        ["primary_legal_object_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_legal_object_duplicates_primary_legal_object_id",
        table_name="legal_object_duplicates",
    )
    op.drop_table("legal_object_duplicates")

    op.drop_index(
        "ix_legal_object_lineage_parent_legal_object_id",
        table_name="legal_object_lineage",
    )
    op.drop_table("legal_object_lineage")

    op.drop_constraint(
        "fk_legal_objects_current_version_id",
        "legal_objects",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_legal_object_versions_effective_dates",
        table_name="legal_object_versions",
    )
    op.drop_index(
        "ix_legal_object_versions_text_hash",
        table_name="legal_object_versions",
    )
    op.drop_index(
        "ix_legal_object_versions_source_version_id",
        table_name="legal_object_versions",
    )
    op.drop_table("legal_object_versions")

    op.drop_index("ix_legal_objects_canonical_path", table_name="legal_objects")
    op.drop_index("ix_legal_objects_object_type", table_name="legal_objects")
    op.drop_index("ix_legal_objects_tax_type_id", table_name="legal_objects")
    op.drop_index("ix_legal_objects_country_id", table_name="legal_objects")
    op.drop_table("legal_objects")
