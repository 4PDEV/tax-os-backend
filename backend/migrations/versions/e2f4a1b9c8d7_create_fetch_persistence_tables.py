"""create fetch persistence tables

Revision ID: e2f4a1b9c8d7
Revises: d4b7f91e62a1
Create Date: 2026-06-02 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e2f4a1b9c8d7"
down_revision: Union[str, Sequence[str], None] = "d4b7f91e62a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fetch_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("monitoring_candidate_id", sa.UUID(), nullable=True),
        sa.Column("source_allowlist_entry_id", sa.UUID(), nullable=True),
        sa.Column("requested_url", sa.Text(), nullable=False),
        sa.Column("requested_by_actor_type", sa.String(length=64), nullable=False),
        sa.Column("requested_by_actor_identifier", sa.String(length=255), nullable=True),
        sa.Column("request_reason", sa.Text(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("local_fixture_mode", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["monitoring_candidate_id"], ["monitoring_candidates.id"]),
        sa.ForeignKeyConstraint(["source_allowlist_entry_id"], ["source_allowlist_entries.id"]),
        sa.CheckConstraint(
            "requested_by_actor_type in ('user','system','worker','admin','test')",
            name="ck_fetch_request_actor_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_fetch_requests_monitoring_candidate_id",
        "fetch_requests",
        ["monitoring_candidate_id"],
    )
    op.create_index(
        "ix_fetch_requests_source_allowlist_entry_id",
        "fetch_requests",
        ["source_allowlist_entry_id"],
    )

    op.create_table(
        "fetch_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("fetch_request_id", sa.UUID(), nullable=False),
        sa.Column("fetched_url", sa.Text(), nullable=False),
        sa.Column("final_url", sa.Text(), nullable=True),
        sa.Column("fetch_status", sa.String(length=32), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("http_status_code", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("content_length", sa.Integer(), nullable=True),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("storage_backend", sa.String(length=64), nullable=True),
        sa.Column("storage_path", sa.Text(), nullable=True),
        sa.Column("error_category", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("fetcher_name", sa.String(length=128), nullable=False),
        sa.Column("fetcher_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["fetch_request_id"], ["fetch_requests.id"]),
        sa.CheckConstraint(
            "fetch_status in ('pending','success','failed','blocked','skipped','partial')",
            name="ck_fetch_result_status",
        ),
        sa.CheckConstraint(
            "error_category is null or error_category in "
            "('source_unreachable','access_denied','robots_or_terms_restricted',"
            "'unsupported_content_type','content_too_large','checksum_failed','timeout',"
            "'redirect_policy_failed','unexpected_content','unknown_failure')",
            name="ck_fetch_result_error_category",
        ),
        sa.CheckConstraint(
            "storage_backend is null or storage_backend in "
            "('none','database','local_fixture','local_test','filesystem','s3','minio','azure_blob')",
            name="ck_fetch_result_storage_backend",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fetch_results_fetch_request_id", "fetch_results", ["fetch_request_id"])


def downgrade() -> None:
    op.drop_index("ix_fetch_results_fetch_request_id", table_name="fetch_results")
    op.drop_table("fetch_results")
    op.drop_index("ix_fetch_requests_source_allowlist_entry_id", table_name="fetch_requests")
    op.drop_index("ix_fetch_requests_monitoring_candidate_id", table_name="fetch_requests")
    op.drop_table("fetch_requests")
