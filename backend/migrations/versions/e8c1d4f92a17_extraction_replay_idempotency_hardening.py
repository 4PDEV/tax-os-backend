"""extraction replay idempotency hardening

Revision ID: e8c1d4f92a17
Revises: b3d7a9f1c204
Create Date: 2026-06-02 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e8c1d4f92a17"
down_revision: Union[str, Sequence[str], None] = "b3d7a9f1c204"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_extraction_trigger_requests_source_version_default",
        "extraction_trigger_requests",
        ["source_version_id"],
        unique=True,
        postgresql_where=sa.text("force_reprocess = false"),
    )

    op.create_unique_constraint(
        "uq_extracted_texts_extraction_run_id",
        "extracted_texts",
        ["extraction_run_id"],
    )

    op.create_check_constraint(
        "ck_extraction_runs_extraction_status",
        "extraction_runs",
        "extraction_status in ('pending','success','failed','partial')",
    )
    op.create_check_constraint(
        "ck_parser_runs_parser_status",
        "parser_runs",
        "parser_status in ('pending','success','failed','partial')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_parser_runs_parser_status", "parser_runs", type_="check")
    op.drop_constraint("ck_extraction_runs_extraction_status", "extraction_runs", type_="check")
    op.drop_constraint("uq_extracted_texts_extraction_run_id", "extracted_texts", type_="unique")
    op.drop_index(
        "uq_extraction_trigger_requests_source_version_default",
        table_name="extraction_trigger_requests",
    )
