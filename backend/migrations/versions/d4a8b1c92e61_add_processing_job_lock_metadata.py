"""add processing job lock metadata

Revision ID: d4a8b1c92e61
Revises: c3d91e7a4f20
Create Date: 2026-05-28 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4a8b1c92e61"
down_revision: Union[str, Sequence[str], None] = "c3d91e7a4f20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "source_processing_jobs",
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "source_processing_jobs",
        sa.Column("locked_by", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("source_processing_jobs", "locked_by")
    op.drop_column("source_processing_jobs", "locked_at")
