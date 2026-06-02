"""create parsing trigger persistence tables

Revision ID: f3b9c2e81a25
Revises: e8c1d4f92a17
Create Date: 2026-06-02 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f3b9c2e81a25"
down_revision: Union[str, Sequence[str], None] = "e8c1d4f92a17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "parsing_trigger_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("extracted_text_id", sa.UUID(), nullable=False),
        sa.Column("requested_by_actor_type", sa.String(length=64), nullable=False),
        sa.Column("requested_by_actor_identifier", sa.String(length=255), nullable=True),
        sa.Column("trigger_reason", sa.Text(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rerun_allowed", sa.Boolean(), nullable=False),
        sa.Column("force_reparse", sa.Boolean(), nullable=False),
        sa.Column("trigger_hash", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["extracted_text_id"], ["extracted_texts.id"]),
        sa.CheckConstraint(
            "requested_by_actor_type in ('user','system','worker','admin','test')",
            name="ck_parsing_trigger_request_actor_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_parsing_trigger_requests_extracted_text_id",
        "parsing_trigger_requests",
        ["extracted_text_id"],
    )
    op.create_index(
        "ix_parsing_trigger_requests_trigger_hash",
        "parsing_trigger_requests",
        ["trigger_hash"],
    )
    op.create_index(
        "uq_parsing_trigger_requests_extracted_text_default",
        "parsing_trigger_requests",
        ["extracted_text_id"],
        unique=True,
        postgresql_where=sa.text("force_reparse = false"),
    )

    op.create_table(
        "parsing_trigger_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parsing_trigger_request_id", sa.UUID(), nullable=False),
        sa.Column("extracted_text_id", sa.UUID(), nullable=False),
        sa.Column("trigger_status", sa.String(length=64), nullable=False),
        sa.Column("parser_run_id", sa.UUID(), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_category", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parsing_trigger_request_id"], ["parsing_trigger_requests.id"]),
        sa.ForeignKeyConstraint(["extracted_text_id"], ["extracted_texts.id"]),
        sa.ForeignKeyConstraint(["parser_run_id"], ["parser_runs.id"]),
        sa.CheckConstraint(
            "trigger_status in ('pending','accepted','rejected','queued','started',"
            "'completed','failed','skipped','duplicate_rejected')",
            name="ck_parsing_trigger_result_status",
        ),
        sa.CheckConstraint(
            "error_category is null or error_category in "
            "('extracted_text_missing','extracted_text_not_eligible','extraction_not_completed',"
            "'parsing_already_completed','unsupported_content_type','parsing_pipeline_unavailable',"
            "'invalid_request','unknown_failure')",
            name="ck_parsing_trigger_result_error_category",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_parsing_trigger_results_request_id",
        "parsing_trigger_results",
        ["parsing_trigger_request_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_parsing_trigger_results_request_id", table_name="parsing_trigger_results")
    op.drop_table("parsing_trigger_results")
    op.drop_index(
        "uq_parsing_trigger_requests_extracted_text_default",
        table_name="parsing_trigger_requests",
    )
    op.drop_index("ix_parsing_trigger_requests_trigger_hash", table_name="parsing_trigger_requests")
    op.drop_index(
        "ix_parsing_trigger_requests_extracted_text_id",
        table_name="parsing_trigger_requests",
    )
    op.drop_table("parsing_trigger_requests")
