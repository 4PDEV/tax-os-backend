"""parsed structure identity hardening

Revision ID: a4d2e8f93b36
Revises: f3b9c2e81a25
Create Date: 2026-06-02 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "a4d2e8f93b36"
down_revision: Union[str, Sequence[str], None] = "f3b9c2e81a25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_parsed_structures_parser_run_id",
        "parsed_structures",
        ["parser_run_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_parsed_structures_parser_run_id",
        "parsed_structures",
        type_="unique",
    )
