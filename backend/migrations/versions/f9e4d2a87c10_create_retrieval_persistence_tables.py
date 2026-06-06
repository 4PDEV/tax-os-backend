"""create retrieval persistence tables

Revision ID: f9e4d2a87c10
Revises: d8f2c4a19b63
Create Date: 2026-06-02 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f9e4d2a87c10"
down_revision: Union[str, Sequence[str], None] = "d8f2c4a19b63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "retrieval_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("retrieval_mode", sa.String(length=64), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=True),
        sa.Column("legal_object_version_id", sa.UUID(), nullable=True),
        sa.Column("jurisdiction_code", sa.String(length=16), nullable=False),
        sa.Column("tax_type_code", sa.String(length=64), nullable=True),
        sa.Column("scope_envelope", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("requested_by_actor_type", sa.String(length=64), nullable=False),
        sa.Column("requested_by_actor_identifier", sa.String(length=255), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("force_replay", sa.Boolean(), nullable=False),
        sa.Column("include_canonical_text", sa.Boolean(), nullable=False),
        sa.Column("include_rendered_citation_text", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["legal_object_version_id"],
            ["legal_object_versions.legal_object_version_id"],
        ),
        sa.CheckConstraint(
            "retrieval_mode in ('AS_OF_DATE','EXACT_VERSION','LATEST_VERSION')",
            name="ck_retrieval_request_mode",
        ),
        sa.CheckConstraint(
            "requested_by_actor_type in ('user','system','worker','admin','test')",
            name="ck_retrieval_request_actor_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_retrieval_requests_request_hash",
        "retrieval_requests",
        ["request_hash"],
    )
    op.create_index(
        "uq_retrieval_requests_hash_default",
        "retrieval_requests",
        ["request_hash"],
        unique=True,
        postgresql_where=sa.text("force_replay = false"),
    )

    op.create_table(
        "retrieval_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("retrieval_request_id", sa.UUID(), nullable=False),
        sa.Column("retrieval_status", sa.String(length=64), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_category", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["retrieval_request_id"],
            ["retrieval_requests.id"],
        ),
        sa.CheckConstraint(
            "retrieval_status in ('pending','accepted','completed','failed','skipped',"
            "'duplicate_rejected')",
            name="ck_retrieval_result_status",
        ),
        sa.CheckConstraint(
            "error_category is null or error_category in "
            "('invalid_request','temporal_scope_missing','version_missing',"
            "'citation_missing','provenance_incomplete','duplicate_retrieval',"
            "'retrieval_pipeline_unavailable','unknown_failure')",
            name="ck_retrieval_result_error_category",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_retrieval_results_request_id",
        "retrieval_results",
        ["retrieval_request_id"],
    )

    op.create_table(
        "retrieval_evidence_references",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("retrieval_result_id", sa.UUID(), nullable=False),
        sa.Column("legal_object_id", sa.String(length=64), nullable=False),
        sa.Column("legal_object_version_id", sa.UUID(), nullable=False),
        sa.Column("source_version_id", sa.UUID(), nullable=False),
        sa.Column("citation_id", sa.String(length=255), nullable=True),
        sa.Column("citation_hash", sa.String(length=64), nullable=True),
        sa.Column("source_document_id", sa.UUID(), nullable=True),
        sa.Column("location_reference", sa.String(length=255), nullable=True),
        sa.Column("object_identifier", sa.String(length=255), nullable=True),
        sa.Column("deterministic_order_index", sa.Integer(), nullable=False),
        sa.Column("evidence_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["legal_object_id"], ["legal_objects.legal_object_id"]),
        sa.ForeignKeyConstraint(
            ["legal_object_version_id"],
            ["legal_object_versions.legal_object_version_id"],
        ),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.ForeignKeyConstraint(["citation_id"], ["citations.citation_id"]),
        sa.ForeignKeyConstraint(
            ["retrieval_result_id"],
            ["retrieval_results.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "retrieval_result_id",
            "deterministic_order_index",
            name="uq_retrieval_evidence_result_order",
        ),
    )
    op.create_index(
        "ix_retrieval_evidence_result_id",
        "retrieval_evidence_references",
        ["retrieval_result_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_retrieval_evidence_result_id",
        table_name="retrieval_evidence_references",
    )
    op.drop_table("retrieval_evidence_references")
    op.drop_index("ix_retrieval_results_request_id", table_name="retrieval_results")
    op.drop_table("retrieval_results")
    op.drop_index(
        "uq_retrieval_requests_hash_default",
        table_name="retrieval_requests",
    )
    op.drop_index("ix_retrieval_requests_request_hash", table_name="retrieval_requests")
    op.drop_table("retrieval_requests")
