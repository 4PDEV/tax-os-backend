"""TASK-006X1 — Alembic evidence for legal_object_versions (legal_object_id, text_hash) uniqueness."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

INTEGRITY_REVISION = "b8d4e9a92c05"
INTEGRITY_FILE = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "b8d4e1a92c05_add_legal_object_integrity_constraints.py"
)
CONSTRAINT_NAME = "uq_legal_object_versions_object_hash"
ROOT_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = ROOT_DIR / "alembic.ini"
MIGRATIONS_PATH = ROOT_DIR / "backend" / "migrations"
PARENT_BEFORE_INTEGRITY = "f7c2d9e41a83"


def test_integrity_migration_defines_object_text_hash_unique():
    source = INTEGRITY_FILE.read_text()
    assert CONSTRAINT_NAME in source
    assert '"legal_object_id"' in source or "'legal_object_id'" in source
    assert "text_hash" in source


@pytest.mark.integration
def test_unique_constraint_exists_at_head(engine):
    inspector = inspect(engine)
    uniques = inspector.get_unique_constraints("legal_object_versions")
    names = {c["name"] for c in uniques}
    assert CONSTRAINT_NAME in names
    match = next(c for c in uniques if c["name"] == CONSTRAINT_NAME)
    assert set(match["column_names"]) == {"legal_object_id", "text_hash"}


@pytest.mark.integration
def test_downgrade_removes_and_upgrade_restores_object_text_hash_unique(migrated_test_database):
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_PATH))

    command.downgrade(alembic_cfg, PARENT_BEFORE_INTEGRITY)
    from app.db.session import engine as app_engine

    inspector = inspect(app_engine)
    names = {c["name"] for c in inspector.get_unique_constraints("legal_object_versions")}
    assert CONSTRAINT_NAME not in names

    command.upgrade(alembic_cfg, "head")
    inspector = inspect(app_engine)
    names = {c["name"] for c in inspector.get_unique_constraints("legal_object_versions")}
    assert CONSTRAINT_NAME in names
