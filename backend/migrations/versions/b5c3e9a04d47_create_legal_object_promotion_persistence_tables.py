"""create legal object promotion persistence tables

Revision ID: b5c3e9a04d47
Revises: a4d2e8f93b36
Create Date: 2026-06-02 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b5c3e9a04d47"
down_revision: Union[str, Sequence[str], None] = "a4d2e8f93b36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "legal_object_promotion_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parsed_structure_id", sa.UUID(), nullable=False),
        sa.Column("source_version_id", sa.UUID(), nullable=False),
        sa.Column("promotion_reason", sa.Text(), nullable=False),
        sa.Column("requested_by_actor_type", sa.String(length=64), nullable=False),
        sa.Column("requested_by_actor_identifier", sa.String(length=255), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("force_repromotion", sa.Boolean(), nullable=False),
        sa.Column("promotion_hash", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parsed_structure_id"], ["parsed_structures.id"]),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.CheckConstraint(
            "requested_by_actor_type in ('user','system','worker','admin','test')",
            name="ck_legal_object_promotion_request_actor_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_legal_object_promotion_requests_parsed_structure_id",
        "legal_object_promotion_requests",
        ["parsed_structure_id"],
    )
    op.create_index(
        "ix_legal_object_promotion_requests_promotion_hash",
        "legal_object_promotion_requests",
        ["promotion_hash"],
    )
    op.create_index(
        "uq_legal_object_promotion_requests_parsed_structure_default",
        "legal_object_promotion_requests",
        ["parsed_structure_id"],
        unique=True,
        postgresql_where=sa.text("force_repromotion = false"),
    )

    op.create_table(
        "legal_object_promotion_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("legal_object_promotion_request_id", sa.UUID(), nullable=False),
        sa.Column("parsed_structure_id", sa.UUID(), nullable=False),
        sa.Column("promotion_status", sa.String(length=64), nullable=False),
        sa.Column("legal_object_id", sa.String(length=64), nullable=True),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_category", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["legal_object_promotion_request_id"],
            ["legal_object_promotion_requests.id"],
        ),
        sa.ForeignKeyConstraint(["parsed_structure_id"], ["parsed_structures.id"]),
        sa.ForeignKeyConstraint(["legal_object_id"], ["legal_objects.legal_object_id"]),
        sa.CheckConstraint(
            "promotion_status in ('pending','accepted','rejected','promoted',"
            "'failed','skipped','duplicate_rejected')",
            name="ck_legal_object_promotion_result_status",
        ),
        sa.CheckConstraint(
            "error_category is null or error_category in "
            "('parsed_structure_missing','parser_run_incomplete','provenance_incomplete',"
            "'duplicate_promotion','invalid_request','promotion_pipeline_unavailable',"
            "'unknown_failure')",
            name="ck_legal_object_promotion_result_error_category",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_legal_object_promotion_results_request_id",
        "legal_object_promotion_results",
        ["legal_object_promotion_request_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_legal_object_promotion_results_request_id",
        table_name="legal_object_promotion_results",
    )
    op.drop_table("legal_object_promotion_results")
    op.drop_index(
        "uq_legal_object_promotion_requests_parsed_structure_default",
        table_name="legal_object_promotion_requests",
    )
    op.drop_index(
        "ix_legal_object_promotion_requests_promotion_hash",
        table_name="legal_object_promotion_requests",
    )
    op.drop_index(
        "ix_legal_object_promotion_requests_parsed_structure_id",
        table_name="legal_object_promotion_requests",
    )
    op.drop_table("legal_object_promotion_requests")
