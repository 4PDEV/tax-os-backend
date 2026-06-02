from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

REVISION_FILE = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "e2f4a1b9c8d7_create_fetch_persistence_tables.py"
)
REVISION_ID = "e2f4a1b9c8d7"
ROOT_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = ROOT_DIR / "alembic.ini"
MIGRATIONS_PATH = ROOT_DIR / "backend" / "migrations"

FETCH_TABLES = (
    "fetch_requests",
    "fetch_results",
)


def _migration_source() -> str:
    assert REVISION_FILE.exists(), "fetch persistence migration file must exist"
    return REVISION_FILE.read_text()


def test_migration_file_exists():
    assert REVISION_FILE.is_file()
    assert REVISION_ID in _migration_source()


def test_migration_creates_fetch_tables():
    source = _migration_source()
    for table in FETCH_TABLES:
        assert table in source
        assert "create_table" in source


def test_migration_revises_monitoring_head():
    source = _migration_source()
    assert "d4b7f91e62a1" in source


@pytest.mark.integration
def test_fetch_tables_exist_at_head(engine):
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    for table in FETCH_TABLES:
        assert table in tables


@pytest.mark.integration
def test_downgrade_removes_and_upgrade_restores_fetch_tables(migrated_test_database):
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_PATH))

    command.downgrade(alembic_cfg, "d4b7f91e62a1")
    from app.db.session import engine as app_engine

    inspector = inspect(app_engine)
    tables = set(inspector.get_table_names())
    for table in FETCH_TABLES:
        assert table not in tables

    command.upgrade(alembic_cfg, "head")
    inspector = inspect(app_engine)
    tables = set(inspector.get_table_names())
    for table in FETCH_TABLES:
        assert table in tables
