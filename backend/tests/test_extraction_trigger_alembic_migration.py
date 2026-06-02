from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

REVISION_FILE = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "b3d7a9f1c204_create_extraction_trigger_persistence_tables.py"
)
REVISION_ID = "b3d7a9f1c204"
ROOT_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = ROOT_DIR / "alembic.ini"
MIGRATIONS_PATH = ROOT_DIR / "backend" / "migrations"

TABLES = ("extraction_trigger_requests", "extraction_trigger_results")


def _migration_source() -> str:
    assert REVISION_FILE.exists(), "extraction trigger migration file must exist"
    return REVISION_FILE.read_text()


def test_migration_file_exists():
    assert REVISION_FILE.is_file()
    assert REVISION_ID in _migration_source()


def test_migration_creates_extraction_trigger_tables():
    source = _migration_source()
    for table in TABLES:
        assert table in source
        assert "create_table" in source


def test_migration_revises_source_promotion_head():
    source = _migration_source()
    assert "a7e6c9b4d201" in source


@pytest.mark.integration
def test_extraction_trigger_tables_exist_at_head(engine):
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    for table in TABLES:
        assert table in tables


@pytest.mark.integration
def test_downgrade_removes_and_upgrade_restores_extraction_trigger_tables(migrated_test_database):
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_PATH))

    command.downgrade(alembic_cfg, "a7e6c9b4d201")
    from app.db.session import engine as app_engine

    inspector = inspect(app_engine)
    tables = set(inspector.get_table_names())
    for table in TABLES:
        assert table not in tables

    command.upgrade(alembic_cfg, "head")
    inspector = inspect(app_engine)
    tables = set(inspector.get_table_names())
    for table in TABLES:
        assert table in tables
