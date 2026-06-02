"""create extraction trigger persistence tables

Revision ID: b3d7a9f1c204
Revises: a7e6c9b4d201
Create Date: 2026-06-02 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b3d7a9f1c204"
down_revision: Union[str, Sequence[str], None] = "a7e6c9b4d201"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "extraction_trigger_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_version_id", sa.UUID(), nullable=False),
        sa.Column("requested_by_actor_type", sa.String(length=64), nullable=False),
        sa.Column("requested_by_actor_identifier", sa.String(length=255), nullable=True),
        sa.Column("trigger_reason", sa.Text(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rerun_allowed", sa.Boolean(), nullable=False),
        sa.Column("force_reprocess", sa.Boolean(), nullable=False),
        sa.Column("trigger_hash", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.CheckConstraint(
            "requested_by_actor_type in ('user','system','worker','admin','test')",
            name="ck_extraction_trigger_request_actor_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_extraction_trigger_requests_source_version_id",
        "extraction_trigger_requests",
        ["source_version_id"],
    )
    op.create_index(
        "ix_extraction_trigger_requests_trigger_hash",
        "extraction_trigger_requests",
        ["trigger_hash"],
    )

    op.create_table(
        "extraction_trigger_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("extraction_trigger_request_id", sa.UUID(), nullable=False),
        sa.Column("source_version_id", sa.UUID(), nullable=False),
        sa.Column("trigger_status", sa.String(length=64), nullable=False),
        sa.Column("extraction_run_id", sa.UUID(), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_category", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["extraction_trigger_request_id"], ["extraction_trigger_requests.id"]),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.ForeignKeyConstraint(["extraction_run_id"], ["extraction_runs.id"]),
        sa.CheckConstraint(
            "trigger_status in ('pending','accepted','rejected','queued','started',"
            "'completed','failed','skipped','duplicate_rejected')",
            name="ck_extraction_trigger_result_status",
        ),
        sa.CheckConstraint(
            "error_category is null or error_category in "
            "('source_version_missing','source_version_not_eligible','provenance_missing',"
            "'extraction_already_completed','unsupported_source_type','extraction_pipeline_unavailable',"
            "'invalid_request','unknown_failure')",
            name="ck_extraction_trigger_result_error_category",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_extraction_trigger_results_request_id",
        "extraction_trigger_results",
        ["extraction_trigger_request_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_extraction_trigger_results_request_id", table_name="extraction_trigger_results")
    op.drop_table("extraction_trigger_results")
    op.drop_index("ix_extraction_trigger_requests_trigger_hash", table_name="extraction_trigger_requests")
    op.drop_index("ix_extraction_trigger_requests_source_version_id", table_name="extraction_trigger_requests")
    op.drop_table("extraction_trigger_requests")
