"""add processing job result metadata

Revision ID: e5f2a8c31b74
Revises: d4a8b1c92e61
Create Date: 2026-05-28 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e5f2a8c31b74"
down_revision: Union[str, Sequence[str], None] = "d4a8b1c92e61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "source_processing_jobs",
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "source_processing_jobs",
        sa.Column("completed_by", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "source_processing_jobs",
        sa.Column("failed_by", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("source_processing_jobs", "failed_by")
    op.drop_column("source_processing_jobs", "completed_by")
    op.drop_column("source_processing_jobs", "result_json")
