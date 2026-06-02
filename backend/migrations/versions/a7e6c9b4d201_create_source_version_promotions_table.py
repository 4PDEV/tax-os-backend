"""create source version promotions table

Revision ID: a7e6c9b4d201
Revises: f4c3b2a190de
Create Date: 2026-06-02 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a7e6c9b4d201"
down_revision: Union[str, Sequence[str], None] = "f4c3b2a190de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_version_promotions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_version_id", sa.UUID(), nullable=True),
        sa.Column("source_document_id", sa.UUID(), nullable=False),
        sa.Column("fetch_result_id", sa.UUID(), nullable=False),
        sa.Column("monitoring_candidate_id", sa.UUID(), nullable=True),
        sa.Column("change_detection_result_id", sa.UUID(), nullable=True),
        sa.Column("promotion_status", sa.String(length=64), nullable=False),
        sa.Column("requested_by_actor_type", sa.String(length=64), nullable=False),
        sa.Column("requested_by_actor_identifier", sa.String(length=255), nullable=True),
        sa.Column("promotion_reason", sa.Text(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.ForeignKeyConstraint(["source_document_id"], ["source_documents.id"]),
        sa.ForeignKeyConstraint(["fetch_result_id"], ["fetch_results.id"]),
        sa.ForeignKeyConstraint(["monitoring_candidate_id"], ["monitoring_candidates.id"]),
        sa.ForeignKeyConstraint(["change_detection_result_id"], ["change_detection_results.id"]),
        sa.CheckConstraint(
            "promotion_status in ('pending_review','approved','rejected','failed',"
            "'superseded_candidate','duplicate_rejected')",
            name="ck_source_version_promotion_status",
        ),
        sa.CheckConstraint(
            "requested_by_actor_type in ('user','system','worker','admin','test')",
            name="ck_source_version_promotion_actor_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_source_version_promotions_source_document_id",
        "source_version_promotions",
        ["source_document_id"],
    )
    op.create_index(
        "ix_source_version_promotions_fetch_result_id",
        "source_version_promotions",
        ["fetch_result_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_source_version_promotions_fetch_result_id", table_name="source_version_promotions")
    op.drop_index("ix_source_version_promotions_source_document_id", table_name="source_version_promotions")
    op.drop_table("source_version_promotions")
