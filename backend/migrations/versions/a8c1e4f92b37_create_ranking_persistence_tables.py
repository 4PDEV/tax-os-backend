"""create ranking persistence tables

Revision ID: a8c1e4f92b37
Revises: f9e4d2a87c10
Create Date: 2026-06-02 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a8c1e4f92b37"
down_revision: Union[str, Sequence[str], None] = "f9e4d2a87c10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RANKING_PROFILES = (
    "'CANONICAL','EFFECTIVE_DATE_DESC','GROUP_BY_SOURCE','GROUP_BY_DOCUMENT'"
)
RANKING_STATUSES = (
    "'pending','accepted','completed','failed','skipped','duplicate_rejected'"
)
RANKING_ERROR_CATEGORIES = (
    "'retrieval_result_missing','retrieval_result_not_completed',"
    "'evidence_reference_missing','provenance_incomplete','profile_not_allowed',"
    "'duplicate_ranking','permutation_mismatch','ranking_pipeline_unavailable',"
    "'unknown_failure'"
)


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_retrieval_evidence_result_id_pk",
        "retrieval_evidence_references",
        ["retrieval_result_id", "id"],
    )

    op.create_table(
        "ranking_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ranking_request_hash", sa.String(length=64), nullable=False),
        sa.Column("retrieval_result_id", sa.UUID(), nullable=False),
        sa.Column("ranking_profile", sa.String(length=64), nullable=False),
        sa.Column("contract_version", sa.String(length=32), nullable=False),
        sa.Column("requested_by_actor_type", sa.String(length=64), nullable=False),
        sa.Column("requested_by_actor_identifier", sa.String(length=255), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("force_replay", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["retrieval_result_id"],
            ["retrieval_results.id"],
        ),
        sa.CheckConstraint(
            f"ranking_profile in ({RANKING_PROFILES})",
            name="ck_ranking_request_profile",
        ),
        sa.CheckConstraint(
            "requested_by_actor_type in ('user','system','worker','admin','test')",
            name="ck_ranking_request_actor_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ranking_requests_ranking_request_hash",
        "ranking_requests",
        ["ranking_request_hash"],
    )
    op.create_index(
        "ix_ranking_requests_retrieval_result_id",
        "ranking_requests",
        ["retrieval_result_id"],
    )
    op.create_index(
        "uq_ranking_requests_hash_default",
        "ranking_requests",
        ["ranking_request_hash"],
        unique=True,
        postgresql_where=sa.text("force_replay = false"),
    )

    op.create_table(
        "ranking_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ranking_request_id", sa.UUID(), nullable=False),
        sa.Column("retrieval_result_id", sa.UUID(), nullable=False),
        sa.Column("ranking_status", sa.String(length=64), nullable=False),
        sa.Column("rank_count", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_category", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["ranking_request_id"],
            ["ranking_requests.id"],
        ),
        sa.ForeignKeyConstraint(
            ["retrieval_result_id"],
            ["retrieval_results.id"],
        ),
        sa.CheckConstraint(
            f"ranking_status in ({RANKING_STATUSES})",
            name="ck_ranking_result_status",
        ),
        sa.CheckConstraint(
            f"error_category is null or error_category in ({RANKING_ERROR_CATEGORIES})",
            name="ck_ranking_result_error_category",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ranking_results_ranking_request_id",
        "ranking_results",
        ["ranking_request_id"],
    )
    op.create_index(
        "ix_ranking_results_retrieval_result_id",
        "ranking_results",
        ["retrieval_result_id"],
    )

    op.create_table(
        "ranked_evidence_references",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ranking_result_id", sa.UUID(), nullable=False),
        sa.Column("retrieval_result_id", sa.UUID(), nullable=False),
        sa.Column("retrieval_evidence_reference_id", sa.UUID(), nullable=False),
        sa.Column("presentation_order_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["ranking_result_id"],
            ["ranking_results.id"],
        ),
        sa.ForeignKeyConstraint(
            ["retrieval_result_id"],
            ["retrieval_results.id"],
        ),
        sa.ForeignKeyConstraint(
            ["retrieval_evidence_reference_id"],
            ["retrieval_evidence_references.id"],
        ),
        sa.ForeignKeyConstraint(
            ["retrieval_result_id", "retrieval_evidence_reference_id"],
            ["retrieval_evidence_references.retrieval_result_id", "retrieval_evidence_references.id"],
            name="fk_ranked_evidence_composite_membership",
        ),
        sa.CheckConstraint(
            "presentation_order_index >= 1",
            name="ck_ranked_evidence_presentation_order_index",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ranking_result_id",
            "presentation_order_index",
            name="uq_ranked_evidence_result_order",
        ),
        sa.UniqueConstraint(
            "ranking_result_id",
            "retrieval_evidence_reference_id",
            name="uq_ranked_evidence_result_evidence",
        ),
    )
    op.create_index(
        "ix_ranked_evidence_ranking_result_id",
        "ranked_evidence_references",
        ["ranking_result_id"],
    )
    op.create_index(
        "ix_ranked_evidence_retrieval_result_id",
        "ranked_evidence_references",
        ["retrieval_result_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ranked_evidence_retrieval_result_id",
        table_name="ranked_evidence_references",
    )
    op.drop_index(
        "ix_ranked_evidence_ranking_result_id",
        table_name="ranked_evidence_references",
    )
    op.drop_table("ranked_evidence_references")
    op.drop_index("ix_ranking_results_retrieval_result_id", table_name="ranking_results")
    op.drop_index("ix_ranking_results_ranking_request_id", table_name="ranking_results")
    op.drop_table("ranking_results")
    op.drop_index(
        "uq_ranking_requests_hash_default",
        table_name="ranking_requests",
    )
    op.drop_index("ix_ranking_requests_retrieval_result_id", table_name="ranking_requests")
    op.drop_index("ix_ranking_requests_ranking_request_hash", table_name="ranking_requests")
    op.drop_table("ranking_requests")
    op.drop_constraint(
        "uq_retrieval_evidence_result_id_pk",
        "retrieval_evidence_references",
        type_="unique",
    )
