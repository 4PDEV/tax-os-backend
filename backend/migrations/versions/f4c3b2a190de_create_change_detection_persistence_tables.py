"""create change detection persistence tables

Revision ID: f4c3b2a190de
Revises: e2f4a1b9c8d7
Create Date: 2026-06-02 13:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f4c3b2a190de"
down_revision: Union[str, Sequence[str], None] = "e2f4a1b9c8d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "change_detection_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("monitoring_candidate_id", sa.UUID(), nullable=True),
        sa.Column("fetch_result_id", sa.UUID(), nullable=True),
        sa.Column("source_document_id", sa.UUID(), nullable=True),
        sa.Column("source_version_id", sa.UUID(), nullable=True),
        sa.Column("previous_artifact_reference", sa.Text(), nullable=True),
        sa.Column("current_artifact_reference", sa.Text(), nullable=False),
        sa.Column("requested_by_actor_type", sa.String(length=64), nullable=False),
        sa.Column("requested_by_actor_identifier", sa.String(length=255), nullable=True),
        sa.Column("detection_reason", sa.Text(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["monitoring_candidate_id"], ["monitoring_candidates.id"]),
        sa.ForeignKeyConstraint(["fetch_result_id"], ["fetch_results.id"]),
        sa.ForeignKeyConstraint(["source_document_id"], ["source_documents.id"]),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.CheckConstraint(
            "requested_by_actor_type in ('user','system','worker','admin','test')",
            name="ck_change_detection_request_actor_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_change_detection_requests_monitoring_candidate_id",
        "change_detection_requests",
        ["monitoring_candidate_id"],
    )
    op.create_index(
        "ix_change_detection_requests_fetch_result_id",
        "change_detection_requests",
        ["fetch_result_id"],
    )
    op.create_index(
        "ix_change_detection_requests_source_document_id",
        "change_detection_requests",
        ["source_document_id"],
    )
    op.create_index(
        "ix_change_detection_requests_source_version_id",
        "change_detection_requests",
        ["source_version_id"],
    )

    op.create_table(
        "change_detection_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("change_detection_request_id", sa.UUID(), nullable=False),
        sa.Column("detection_status", sa.String(length=32), nullable=False),
        sa.Column("change_detected", sa.Boolean(), nullable=False),
        sa.Column("change_type", sa.String(length=64), nullable=False),
        sa.Column("previous_checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("current_checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("metadata_diff_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("structural_diff_summary", sa.Text(), nullable=True),
        sa.Column("confidence", sa.String(length=16), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False),
        sa.Column("detector_name", sa.String(length=128), nullable=False),
        sa.Column("detector_version", sa.String(length=64), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("error_category", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["change_detection_request_id"], ["change_detection_requests.id"]),
        sa.CheckConstraint(
            "detection_status in ('pending','completed','failed','skipped','blocked')",
            name="ck_change_detection_result_status",
        ),
        sa.CheckConstraint(
            "change_type in ('no_change','checksum_changed','metadata_changed','content_changed',"
            "'structure_changed','removed_or_unavailable','duplicate_detected','new_artifact','unknown')",
            name="ck_change_detection_result_change_type",
        ),
        sa.CheckConstraint("confidence in ('high','medium','low')", name="ck_change_detection_result_confidence"),
        sa.CheckConstraint(
            "error_category is null or error_category in "
            "('missing_previous_artifact','missing_current_artifact','checksum_unavailable',"
            "'unsupported_content_type','diff_failed','corrupted_artifact','timeout','unknown_failure')",
            name="ck_change_detection_result_error_category",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_change_detection_results_request_id",
        "change_detection_results",
        ["change_detection_request_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_change_detection_results_request_id", table_name="change_detection_results")
    op.drop_table("change_detection_results")
    op.drop_index("ix_change_detection_requests_source_version_id", table_name="change_detection_requests")
    op.drop_index("ix_change_detection_requests_source_document_id", table_name="change_detection_requests")
    op.drop_index("ix_change_detection_requests_fetch_result_id", table_name="change_detection_requests")
    op.drop_index(
        "ix_change_detection_requests_monitoring_candidate_id",
        table_name="change_detection_requests",
    )
    op.drop_table("change_detection_requests")
