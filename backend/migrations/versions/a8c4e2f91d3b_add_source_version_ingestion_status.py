"""add source version ingestion status

Revision ID: a8c4e2f91d3b
Revises: fd6be8e34b7b
Create Date: 2026-05-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a8c4e2f91d3b"
down_revision: Union[str, Sequence[str], None] = "fd6be8e34b7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "source_versions",
        sa.Column(
            "ingestion_status",
            sa.String(length=50),
            nullable=False,
            server_default="not_started",
        ),
    )
    op.alter_column("source_versions", "ingestion_status", server_default=None)


def downgrade() -> None:
    op.drop_column("source_versions", "ingestion_status")
