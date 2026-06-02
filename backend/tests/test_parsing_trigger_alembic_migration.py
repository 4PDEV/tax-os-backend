from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

REVISION_FILE = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "f3b9c2e81a25_create_parsing_trigger_persistence_tables.py"
)
REVISION_ID = "f3b9c2e81a25"
ROOT_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = ROOT_DIR / "alembic.ini"
MIGRATIONS_PATH = ROOT_DIR / "backend" / "migrations"

TABLES = ("parsing_trigger_requests", "parsing_trigger_results")


def _migration_source() -> str:
    assert REVISION_FILE.exists(), "parsing trigger migration file must exist"
    return REVISION_FILE.read_text()


def test_migration_file_exists():
    assert REVISION_FILE.is_file()
    assert REVISION_ID in _migration_source()


def test_migration_creates_parsing_trigger_tables():
    source = _migration_source()
    for table in TABLES:
        assert table in source
        assert "create_table" in source
    assert "uq_parsing_trigger_requests_extracted_text_default" in source


def test_migration_revises_extraction_replay_head():
    assert "e8c1d4f92a17" in _migration_source()


@pytest.mark.integration
def test_parsing_trigger_tables_exist_at_head(engine):
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    for table in TABLES:
        assert table in tables


@pytest.mark.integration
def test_partial_unique_index_exists_at_head(engine):
    inspector = inspect(engine)
    indexes = inspector.get_indexes("parsing_trigger_requests")
    names = {idx["name"] for idx in indexes}
    assert "uq_parsing_trigger_requests_extracted_text_default" in names


@pytest.mark.integration
def test_downgrade_removes_and_upgrade_restores_parsing_trigger_tables(migrated_test_database):
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_PATH))

    command.downgrade(alembic_cfg, "e8c1d4f92a17")
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
