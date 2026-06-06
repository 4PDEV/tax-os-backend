"""create citations table

Revision ID: d8f2c4a19b63
Revises: c6d4f0b15e58
Create Date: 2026-06-02 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d8f2c4a19b63"
down_revision: Union[str, Sequence[str], None] = "c6d4f0b15e58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "citations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("citation_id", sa.String(length=255), nullable=False),
        sa.Column("citation_hash", sa.String(length=64), nullable=False),
        sa.Column("legal_object_id", sa.String(length=64), nullable=False),
        sa.Column("legal_object_version_id", sa.UUID(), nullable=False),
        sa.Column("source_version_id", sa.UUID(), nullable=False),
        sa.Column("location_reference", sa.String(length=255), nullable=False),
        sa.Column("rendered_citation_text", sa.Text(), nullable=False),
        sa.Column("assembled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["legal_object_id"], ["legal_objects.legal_object_id"]),
        sa.ForeignKeyConstraint(
            ["legal_object_version_id"],
            ["legal_object_versions.legal_object_version_id"],
        ),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("citation_hash", name="uq_citations_citation_hash"),
        sa.UniqueConstraint("citation_id", name="uq_citations_citation_id"),
    )
    op.create_index("ix_citations_citation_hash", "citations", ["citation_hash"])
    op.create_index("ix_citations_legal_object_version_id", "citations", ["legal_object_version_id"])


def downgrade() -> None:
    op.drop_index("ix_citations_legal_object_version_id", table_name="citations")
    op.drop_index("ix_citations_citation_hash", table_name="citations")
    op.drop_table("citations")
