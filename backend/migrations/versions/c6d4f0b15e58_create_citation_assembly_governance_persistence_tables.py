"""create citation assembly governance persistence tables

Revision ID: c6d4f0b15e58
Revises: b5c3e9a04d47
Create Date: 2026-06-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c6d4f0b15e58"
down_revision: Union[str, Sequence[str], None] = "b5c3e9a04d47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "citation_assembly_governance_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("legal_object_id", sa.String(length=64), nullable=False),
        sa.Column("legal_object_version_id", sa.UUID(), nullable=False),
        sa.Column("source_version_id", sa.UUID(), nullable=False),
        sa.Column("citation_reason", sa.Text(), nullable=False),
        sa.Column("requested_by_actor_type", sa.String(length=64), nullable=False),
        sa.Column("requested_by_actor_identifier", sa.String(length=255), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("force_reassembly", sa.Boolean(), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["legal_object_id"], ["legal_objects.legal_object_id"]),
        sa.ForeignKeyConstraint(
            ["legal_object_version_id"],
            ["legal_object_versions.legal_object_version_id"],
        ),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.CheckConstraint(
            "requested_by_actor_type in ('user','system','worker','admin','test')",
            name="ck_citation_assembly_governance_request_actor_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_citation_asm_gov_req_legal_object_version_id",
        "citation_assembly_governance_requests",
        ["legal_object_version_id"],
    )
    op.create_index(
        "ix_citation_asm_gov_req_request_hash",
        "citation_assembly_governance_requests",
        ["request_hash"],
    )
    op.create_index(
        "uq_citation_asm_gov_req_version_default",
        "citation_assembly_governance_requests",
        ["legal_object_version_id"],
        unique=True,
        postgresql_where=sa.text("force_reassembly = false"),
    )

    op.create_table(
        "citation_assembly_governance_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("citation_assembly_governance_request_id", sa.UUID(), nullable=False),
        sa.Column("legal_object_id", sa.String(length=64), nullable=False),
        sa.Column("legal_object_version_id", sa.UUID(), nullable=False),
        sa.Column("citation_status", sa.String(length=64), nullable=False),
        sa.Column("citation_id", sa.String(length=255), nullable=True),
        sa.Column("assembled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_category", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["citation_assembly_governance_request_id"],
            ["citation_assembly_governance_requests.id"],
        ),
        sa.ForeignKeyConstraint(["legal_object_id"], ["legal_objects.legal_object_id"]),
        sa.ForeignKeyConstraint(
            ["legal_object_version_id"],
            ["legal_object_versions.legal_object_version_id"],
        ),
        sa.CheckConstraint(
            "citation_status in ('pending','accepted','rejected','assembled',"
            "'failed','skipped','duplicate_rejected')",
            name="ck_citation_assembly_governance_result_status",
        ),
        sa.CheckConstraint(
            "error_category is null or error_category in "
            "('legal_object_missing','version_missing','provenance_incomplete',"
            "'duplicate_citation','invalid_request','citation_pipeline_unavailable',"
            "'unknown_failure')",
            name="ck_citation_assembly_governance_result_error_category",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_citation_asm_gov_res_request_id",
        "citation_assembly_governance_results",
        ["citation_assembly_governance_request_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_citation_asm_gov_res_request_id",
        table_name="citation_assembly_governance_results",
    )
    op.drop_table("citation_assembly_governance_results")
    op.drop_index(
        "uq_citation_asm_gov_req_version_default",
        table_name="citation_assembly_governance_requests",
    )
    op.drop_index(
        "ix_citation_asm_gov_req_request_hash",
        table_name="citation_assembly_governance_requests",
    )
    op.drop_index(
        "ix_citation_asm_gov_req_legal_object_version_id",
        table_name="citation_assembly_governance_requests",
    )
    op.drop_table("citation_assembly_governance_requests")
