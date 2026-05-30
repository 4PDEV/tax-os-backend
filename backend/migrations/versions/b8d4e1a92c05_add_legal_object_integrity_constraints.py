"""add legal object integrity constraints

Revision ID: b8d4e1a92c05
Revises: f7c2d9e41a83
Create Date: 2026-05-30 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "b8d4e1a92c05"
down_revision: Union[str, Sequence[str], None] = "f7c2d9e41a83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LEGAL_OBJECT_STATUS_CHECK = (
    "status IN ('draft', 'active', 'superseded', 'archived', 'rejected')"
)
VERSION_STATUS_CHECK = (
    "version_status IN ('draft', 'active', 'superseded', 'archived', 'rejected')"
)


def upgrade() -> None:
    op.create_check_constraint(
        "ck_legal_objects_status",
        "legal_objects",
        LEGAL_OBJECT_STATUS_CHECK,
    )
    op.create_check_constraint(
        "ck_legal_object_versions_version_status",
        "legal_object_versions",
        VERSION_STATUS_CHECK,
    )
    op.create_unique_constraint(
        "uq_legal_object_versions_object_hash",
        "legal_object_versions",
        ["legal_object_id", "text_hash"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_legal_object_versions_object_hash",
        "legal_object_versions",
        type_="unique",
    )
    op.drop_constraint(
        "ck_legal_object_versions_version_status",
        "legal_object_versions",
        type_="check",
    )
    op.drop_constraint(
        "ck_legal_objects_status",
        "legal_objects",
        type_="check",
    )
