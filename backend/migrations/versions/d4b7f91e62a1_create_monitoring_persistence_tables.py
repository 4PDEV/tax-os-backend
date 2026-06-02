"""create monitoring persistence tables

Revision ID: d4b7f91e62a1
Revises: c9a2f3b81d06
Create Date: 2026-06-02 11:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d4b7f91e62a1"
down_revision: Union[str, Sequence[str], None] = "c9a2f3b81d06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_allowlist_entries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("jurisdiction", sa.String(length=16), nullable=False),
        sa.Column("authority_name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("allowed_patterns_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("blocked_patterns_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("monitoring_frequency", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status in ('active','inactive','suspended')", name="ck_allowlist_status"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "monitoring_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_allowlist_entry_id", sa.UUID(), nullable=False),
        sa.Column("agent_name", sa.String(length=128), nullable=False),
        sa.Column("agent_version", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_status", sa.String(length=32), nullable=False),
        sa.Column("error_category", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_allowlist_entry_id"], ["source_allowlist_entries.id"]),
        sa.CheckConstraint(
            "attempt_status in ('started','completed','failed','partial')",
            name="ck_monitoring_attempt_status",
        ),
        sa.CheckConstraint(
            "error_category is null or error_category in "
            "('source_unreachable','access_denied','robots_or_terms_restricted','parse_failed',"
            "'checksum_failed','unexpected_content','timeout','unknown_failure')",
            name="ck_monitoring_attempt_error_category",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitoring_attempts_allowlist_id", "monitoring_attempts", ["source_allowlist_entry_id"])

    op.create_table(
        "monitoring_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("monitoring_attempt_id", sa.UUID(), nullable=False),
        sa.Column("source_registry_id", sa.UUID(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("detected_title", sa.String(length=1024), nullable=False),
        sa.Column("detected_url", sa.Text(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detection_method", sa.String(length=64), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("previous_checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("change_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.String(length=16), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["monitoring_attempt_id"], ["monitoring_attempts.id"]),
        sa.ForeignKeyConstraint(["source_registry_id"], ["source_documents.id"]),
        sa.CheckConstraint(
            "change_type in ('new_document','modified_document','removed_or_unavailable',"
            "'metadata_changed','checksum_changed','unknown')",
            name="ck_monitoring_event_change_type",
        ),
        sa.CheckConstraint("confidence in ('high','medium','low')", name="ck_monitoring_event_confidence"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitoring_events_attempt_id", "monitoring_events", ["monitoring_attempt_id"])

    op.create_table(
        "monitoring_candidates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("monitoring_event_id", sa.UUID(), nullable=False),
        sa.Column("candidate_state", sa.String(length=64), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.String(length=255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_for_ingestion_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["monitoring_event_id"], ["monitoring_events.id"]),
        sa.CheckConstraint(
            "candidate_state in ('detected','queued_for_review','rejected',"
            "'approved_for_ingestion','superseded','failed')",
            name="ck_monitoring_candidate_state",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "monitoring_candidate_state_transitions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("monitoring_candidate_id", sa.UUID(), nullable=False),
        sa.Column("from_state", sa.String(length=64), nullable=True),
        sa.Column("to_state", sa.String(length=64), nullable=False),
        sa.Column("transition_reason", sa.Text(), nullable=True),
        sa.Column("actor_type", sa.String(length=64), nullable=False),
        sa.Column("actor_identifier", sa.String(length=255), nullable=True),
        sa.Column("transitioned_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["monitoring_candidate_id"], ["monitoring_candidates.id"]),
        sa.CheckConstraint(
            "from_state is null or from_state in ('detected','queued_for_review','rejected',"
            "'approved_for_ingestion','superseded','failed')",
            name="ck_monitoring_transition_from_state",
        ),
        sa.CheckConstraint(
            "to_state in ('detected','queued_for_review','rejected',"
            "'approved_for_ingestion','superseded','failed')",
            name="ck_monitoring_transition_to_state",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_monitoring_candidate_state_transitions_candidate_id",
        "monitoring_candidate_state_transitions",
        ["monitoring_candidate_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_monitoring_candidate_state_transitions_candidate_id",
        table_name="monitoring_candidate_state_transitions",
    )
    op.drop_table("monitoring_candidate_state_transitions")
    op.drop_table("monitoring_candidates")
    op.drop_index("ix_monitoring_events_attempt_id", table_name="monitoring_events")
    op.drop_table("monitoring_events")
    op.drop_index("ix_monitoring_attempts_allowlist_id", table_name="monitoring_attempts")
    op.drop_table("monitoring_attempts")
    op.drop_table("source_allowlist_entries")
