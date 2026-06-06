from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

REVISION_FILE = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "d8f2c4a19b63_create_citations_table.py"
)
REVISION_ID = "d8f2c4a19b63"
ROOT_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = ROOT_DIR / "alembic.ini"
MIGRATIONS_PATH = ROOT_DIR / "backend" / "migrations"


def _migration_source() -> str:
    assert REVISION_FILE.exists()
    return REVISION_FILE.read_text()


def test_migration_file_exists():
    assert REVISION_ID in _migration_source()
    assert "citations" in _migration_source()
    assert "uq_citations_citation_hash" in _migration_source()


def test_migration_revises_governance_head():
    assert "c6d4f0b15e58" in _migration_source()


@pytest.mark.integration
def test_citations_table_exists_at_head(engine):
    assert "citations" in inspect(engine).get_table_names()


@pytest.mark.integration
def test_downgrade_removes_and_upgrade_restores_citations_table(migrated_test_database):
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_PATH))

    command.downgrade(alembic_cfg, "c6d4f0b15e58")
    from app.db.session import engine as app_engine

    assert "citations" not in inspect(app_engine).get_table_names()

    command.upgrade(alembic_cfg, "head")
    assert "citations" in inspect(app_engine).get_table_names()
