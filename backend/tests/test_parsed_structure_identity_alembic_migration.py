from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

REVISION_FILE = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "a4d2e8f93b36_parsed_structure_identity_hardening.py"
)
REVISION_ID = "a4d2e8f93b36"
ROOT_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = ROOT_DIR / "alembic.ini"
MIGRATIONS_PATH = ROOT_DIR / "backend" / "migrations"


def _migration_source() -> str:
    assert REVISION_FILE.exists()
    return REVISION_FILE.read_text()


def test_migration_file_exists():
    assert REVISION_ID in _migration_source()
    assert "uq_parsed_structures_parser_run_id" in _migration_source()


def test_migration_revises_parsing_trigger_head():
    assert "f3b9c2e81a25" in _migration_source()


@pytest.mark.integration
def test_unique_constraint_exists_at_head(engine):
    inspector = inspect(engine)
    uniques = inspector.get_unique_constraints("parsed_structures")
    names = {c["name"] for c in uniques}
    assert "uq_parsed_structures_parser_run_id" in names


@pytest.mark.integration
def test_downgrade_and_upgrade_parsed_structure_identity(migrated_test_database):
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_PATH))

    command.downgrade(alembic_cfg, "f3b9c2e81a25")
    from app.db.session import engine as app_engine

    inspector = inspect(app_engine)
    uniques = {c["name"] for c in inspector.get_unique_constraints("parsed_structures")}
    assert "uq_parsed_structures_parser_run_id" not in uniques

    command.upgrade(alembic_cfg, "head")
    inspector = inspect(app_engine)
    uniques = {c["name"] for c in inspector.get_unique_constraints("parsed_structures")}
    assert "uq_parsed_structures_parser_run_id" in uniques
