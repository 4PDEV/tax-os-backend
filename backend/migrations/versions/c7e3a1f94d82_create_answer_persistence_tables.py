"""create answer persistence tables

Revision ID: c7e3a1f94d82
Revises: a8c1e4f92b37
Create Date: 2026-06-02 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c7e3a1f94d82"
down_revision: Union[str, Sequence[str], None] = "a8c1e4f92b37"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ANSWER_STATUSES = (
    "'pending','accepted','completed','failed','skipped','duplicate_rejected'"
)
ANSWER_ERROR_CATEGORIES = (
    "'ranking_result_not_completed','accepted_ranking_result_missing',"
    "'ranked_evidence_missing','evidence_count_mismatch','provenance_chain_incomplete',"
    "'citation_reference_incomplete','retrieval_result_mismatch','assembly_validation_failed',"
    "'answer_pipeline_unavailable','unknown_failure','duplicate_answer',"
    "'ranking_request_missing','invalid_answer_request'"
)
UNCERTAINTY_FLAG_TYPES = (
    "'conflict','ambiguity','incomplete_provenance','zero_evidence','other'"
)
UNCERTAINTY_SEVERITIES = "'informational','warning','error'"


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_ranked_evidence_result_id_pk",
        "ranked_evidence_references",
        ["ranking_result_id", "id"],
    )

    op.create_table(
        "answer_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("answer_request_hash", sa.String(length=64), nullable=False),
        sa.Column("ranking_request_id", sa.UUID(), nullable=False),
        sa.Column("contract_version", sa.String(length=32), nullable=False),
        sa.Column("assembly_contract_version", sa.String(length=32), nullable=False),
        sa.Column("include_rendered_citation_text", sa.Boolean(), nullable=False),
        sa.Column("requested_by_actor_type", sa.String(length=64), nullable=False),
        sa.Column("requested_by_actor_identifier", sa.String(length=255), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("force_replay", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["ranking_request_id"],
            ["ranking_requests.id"],
        ),
        sa.CheckConstraint(
            "requested_by_actor_type in ('user','system','worker','admin','test')",
            name="ck_answer_request_actor_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_answer_requests_answer_request_hash",
        "answer_requests",
        ["answer_request_hash"],
    )
    op.create_index(
        "ix_answer_requests_ranking_request_id",
        "answer_requests",
        ["ranking_request_id"],
    )
    op.create_index(
        "uq_answer_requests_hash_default",
        "answer_requests",
        ["answer_request_hash"],
        unique=True,
        postgresql_where=sa.text("force_replay = false"),
    )

    op.create_table(
        "answer_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("answer_request_id", sa.UUID(), nullable=False),
        sa.Column("ranking_request_id", sa.UUID(), nullable=False),
        sa.Column("retrieval_result_id", sa.UUID(), nullable=False),
        sa.Column("accepted_ranking_result_id", sa.UUID(), nullable=True),
        sa.Column("terminal_ranking_result_id", sa.UUID(), nullable=True),
        sa.Column("answer_status", sa.String(length=64), nullable=False),
        sa.Column("rank_count", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_category", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["answer_request_id"],
            ["answer_requests.id"],
        ),
        sa.ForeignKeyConstraint(
            ["ranking_request_id"],
            ["ranking_requests.id"],
        ),
        sa.ForeignKeyConstraint(
            ["retrieval_result_id"],
            ["retrieval_results.id"],
        ),
        sa.ForeignKeyConstraint(
            ["accepted_ranking_result_id"],
            ["ranking_results.id"],
        ),
        sa.ForeignKeyConstraint(
            ["terminal_ranking_result_id"],
            ["ranking_results.id"],
        ),
        sa.CheckConstraint(
            f"answer_status in ({ANSWER_STATUSES})",
            name="ck_answer_result_status",
        ),
        sa.CheckConstraint(
            f"error_category is null or error_category in ({ANSWER_ERROR_CATEGORIES})",
            name="ck_answer_result_error_category",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_answer_results_answer_request_id",
        "answer_results",
        ["answer_request_id"],
    )
    op.create_index(
        "ix_answer_results_ranking_request_id",
        "answer_results",
        ["ranking_request_id"],
    )
    op.create_index(
        "ix_answer_results_retrieval_result_id",
        "answer_results",
        ["retrieval_result_id"],
    )

    op.create_table(
        "answer_evidence_entries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("answer_result_id", sa.UUID(), nullable=False),
        sa.Column("answer_request_id", sa.UUID(), nullable=False),
        sa.Column("ranking_request_id", sa.UUID(), nullable=False),
        sa.Column("ranked_evidence_reference_id", sa.UUID(), nullable=False),
        sa.Column("retrieval_result_id", sa.UUID(), nullable=False),
        sa.Column("retrieval_evidence_reference_id", sa.UUID(), nullable=False),
        sa.Column("presentation_order_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["answer_result_id"],
            ["answer_results.id"],
        ),
        sa.ForeignKeyConstraint(
            ["answer_request_id"],
            ["answer_requests.id"],
        ),
        sa.ForeignKeyConstraint(
            ["ranking_request_id"],
            ["ranking_requests.id"],
        ),
        sa.ForeignKeyConstraint(
            ["ranked_evidence_reference_id"],
            ["ranked_evidence_references.id"],
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
            [
                "retrieval_evidence_references.retrieval_result_id",
                "retrieval_evidence_references.id",
            ],
            name="fk_answer_evidence_retrieval_composite",
        ),
        sa.CheckConstraint(
            "presentation_order_index >= 1",
            name="ck_answer_evidence_presentation_order_index",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "answer_result_id",
            "presentation_order_index",
            name="uq_answer_evidence_result_order",
        ),
        sa.UniqueConstraint(
            "answer_result_id",
            "ranked_evidence_reference_id",
            name="uq_answer_evidence_result_ranked",
        ),
        sa.UniqueConstraint(
            "answer_result_id",
            "retrieval_evidence_reference_id",
            name="uq_answer_evidence_result_retrieval",
        ),
    )
    op.create_index(
        "ix_answer_evidence_answer_result_id",
        "answer_evidence_entries",
        ["answer_result_id"],
    )
    op.create_index(
        "ix_answer_evidence_ranking_request_id",
        "answer_evidence_entries",
        ["ranking_request_id"],
    )

    op.create_table(
        "answer_uncertainty_flags",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("answer_result_id", sa.UUID(), nullable=False),
        sa.Column("flag_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("related_retrieval_evidence_reference_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["answer_result_id"],
            ["answer_results.id"],
        ),
        sa.ForeignKeyConstraint(
            ["related_retrieval_evidence_reference_id"],
            ["retrieval_evidence_references.id"],
        ),
        sa.CheckConstraint(
            f"flag_type in ({UNCERTAINTY_FLAG_TYPES})",
            name="ck_answer_uncertainty_flag_type",
        ),
        sa.CheckConstraint(
            f"severity in ({UNCERTAINTY_SEVERITIES})",
            name="ck_answer_uncertainty_severity",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_answer_uncertainty_answer_result_id",
        "answer_uncertainty_flags",
        ["answer_result_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_answer_uncertainty_answer_result_id", table_name="answer_uncertainty_flags")
    op.drop_table("answer_uncertainty_flags")
    op.drop_index("ix_answer_evidence_ranking_request_id", table_name="answer_evidence_entries")
    op.drop_index("ix_answer_evidence_answer_result_id", table_name="answer_evidence_entries")
    op.drop_table("answer_evidence_entries")
    op.drop_index("ix_answer_results_retrieval_result_id", table_name="answer_results")
    op.drop_index("ix_answer_results_ranking_request_id", table_name="answer_results")
    op.drop_index("ix_answer_results_answer_request_id", table_name="answer_results")
    op.drop_table("answer_results")
    op.drop_index("uq_answer_requests_hash_default", table_name="answer_requests")
    op.drop_index("ix_answer_requests_ranking_request_id", table_name="answer_requests")
    op.drop_index("ix_answer_requests_answer_request_hash", table_name="answer_requests")
    op.drop_table("answer_requests")
    op.drop_constraint(
        "uq_ranked_evidence_result_id_pk",
        "ranked_evidence_references",
        type_="unique",
    )
