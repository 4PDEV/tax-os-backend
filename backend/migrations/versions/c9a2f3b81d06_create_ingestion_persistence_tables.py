"""create ingestion persistence tables

Revision ID: c9a2f3b81d06
Revises: b8d4e1a92c05
Create Date: 2026-06-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c9a2f3b81d06"
down_revision: Union[str, Sequence[str], None] = "b8d4e1a92c05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "extraction_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_version_id", sa.UUID(), nullable=False),
        sa.Column("extractor_name", sa.String(length=128), nullable=False),
        sa.Column("extractor_version", sa.String(length=64), nullable=False),
        sa.Column("extraction_status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("raw_text_length", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_extraction_runs_source_version_id",
        "extraction_runs",
        ["source_version_id"],
    )
    op.create_index(
        "ix_extraction_runs_extraction_status",
        "extraction_runs",
        ["extraction_status"],
    )

    op.create_table(
        "extracted_texts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("extraction_run_id", sa.UUID(), nullable=False),
        sa.Column("source_version_id", sa.UUID(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("storage_backend", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["extraction_run_id"], ["extraction_runs.id"]),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_extracted_texts_extraction_run_id",
        "extracted_texts",
        ["extraction_run_id"],
    )
    op.create_index(
        "ix_extracted_texts_source_version_id",
        "extracted_texts",
        ["source_version_id"],
    )
    op.create_index(
        "ix_extracted_texts_content_hash",
        "extracted_texts",
        ["content_hash"],
    )

    op.create_table(
        "parser_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("extraction_run_id", sa.UUID(), nullable=False),
        sa.Column("parser_name", sa.String(length=128), nullable=False),
        sa.Column("parser_version", sa.String(length=64), nullable=False),
        sa.Column("parser_status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["extraction_run_id"], ["extraction_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_parser_runs_extraction_run_id",
        "parser_runs",
        ["extraction_run_id"],
    )

    op.create_table(
        "parsed_structures",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parser_run_id", sa.UUID(), nullable=False),
        sa.Column("source_version_id", sa.UUID(), nullable=False),
        sa.Column("structure_type", sa.String(length=64), nullable=False),
        sa.Column("structure_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("structure_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parser_run_id"], ["parser_runs.id"]),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_parsed_structures_parser_run_id",
        "parsed_structures",
        ["parser_run_id"],
    )
    op.create_index(
        "ix_parsed_structures_source_version_id",
        "parsed_structures",
        ["source_version_id"],
    )

    op.create_table(
        "ingestion_state_transitions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_version_id", sa.UUID(), nullable=False),
        sa.Column("pipeline_state", sa.String(length=64), nullable=False),
        sa.Column("previous_pipeline_state", sa.String(length=64), nullable=True),
        sa.Column("extraction_run_id", sa.UUID(), nullable=True),
        sa.Column("parser_run_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"]),
        sa.ForeignKeyConstraint(["extraction_run_id"], ["extraction_runs.id"]),
        sa.ForeignKeyConstraint(["parser_run_id"], ["parser_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ingestion_state_transitions_source_version_id",
        "ingestion_state_transitions",
        ["source_version_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_ingestion_state_transitions_source_version_id", "ingestion_state_transitions")
    op.drop_table("ingestion_state_transitions")
    op.drop_index("ix_parsed_structures_source_version_id", "parsed_structures")
    op.drop_index("ix_parsed_structures_parser_run_id", "parsed_structures")
    op.drop_table("parsed_structures")
    op.drop_index("ix_parser_runs_extraction_run_id", "parser_runs")
    op.drop_table("parser_runs")
    op.drop_index("ix_extracted_texts_content_hash", "extracted_texts")
    op.drop_index("ix_extracted_texts_source_version_id", "extracted_texts")
    op.drop_index("ix_extracted_texts_extraction_run_id", "extracted_texts")
    op.drop_table("extracted_texts")
    op.drop_index("ix_extraction_runs_extraction_status", "extraction_runs")
    op.drop_index("ix_extraction_runs_source_version_id", "extraction_runs")
    op.drop_table("extraction_runs")
