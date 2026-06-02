from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

REVISION_FILE = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "f4c3b2a190de_create_change_detection_persistence_tables.py"
)
REVISION_ID = "f4c3b2a190de"
ROOT_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = ROOT_DIR / "alembic.ini"
MIGRATIONS_PATH = ROOT_DIR / "backend" / "migrations"

CHANGE_DETECTION_TABLES = (
    "change_detection_requests",
    "change_detection_results",
)


def _migration_source() -> str:
    assert REVISION_FILE.exists(), "change detection migration file must exist"
    return REVISION_FILE.read_text()


def test_migration_file_exists():
    assert REVISION_FILE.is_file()
    assert REVISION_ID in _migration_source()


def test_migration_creates_change_detection_tables():
    source = _migration_source()
    for table in CHANGE_DETECTION_TABLES:
        assert table in source
        assert "create_table" in source


def test_migration_revises_fetch_head():
    source = _migration_source()
    assert "e2f4a1b9c8d7" in source


@pytest.mark.integration
def test_change_detection_tables_exist_at_head(engine):
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    for table in CHANGE_DETECTION_TABLES:
        assert table in tables


@pytest.mark.integration
def test_downgrade_removes_and_upgrade_restores_change_detection_tables(migrated_test_database):
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_PATH))

    command.downgrade(alembic_cfg, "e2f4a1b9c8d7")
    from app.db.session import engine as app_engine

    inspector = inspect(app_engine)
    tables = set(inspector.get_table_names())
    for table in CHANGE_DETECTION_TABLES:
        assert table not in tables

    command.upgrade(alembic_cfg, "head")
    inspector = inspect(app_engine)
    tables = set(inspector.get_table_names())
    for table in CHANGE_DETECTION_TABLES:
        assert table in tables
