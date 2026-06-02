from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

REVISION_FILE = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "e8c1d4f92a17_extraction_replay_idempotency_hardening.py"
)
REVISION_ID = "e8c1d4f92a17"
ROOT_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = ROOT_DIR / "alembic.ini"
MIGRATIONS_PATH = ROOT_DIR / "backend" / "migrations"


def _migration_source() -> str:
    assert REVISION_FILE.exists()
    return REVISION_FILE.read_text()


def test_migration_file_exists():
    assert REVISION_ID in _migration_source()
    assert "uq_extraction_trigger_requests_source_version_default" in _migration_source()
    assert "uq_extracted_texts_extraction_run_id" in _migration_source()


def test_migration_revises_extraction_trigger_head():
    assert "b3d7a9f1c204" in _migration_source()


@pytest.mark.integration
def test_partial_unique_index_exists_at_head(engine):
    inspector = inspect(engine)
    indexes = inspector.get_indexes("extraction_trigger_requests")
    names = {idx["name"] for idx in indexes}
    assert "uq_extraction_trigger_requests_source_version_default" in names


@pytest.mark.integration
def test_downgrade_and_upgrade_replay_hardening(migrated_test_database):
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_PATH))

    command.downgrade(alembic_cfg, "b3d7a9f1c204")
    from app.db.session import engine as app_engine

    inspector = inspect(app_engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("extraction_trigger_requests")}
    assert "uq_extraction_trigger_requests_source_version_default" not in indexes

    command.upgrade(alembic_cfg, "head")
    inspector = inspect(app_engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("extraction_trigger_requests")}
    assert "uq_extraction_trigger_requests_source_version_default" in indexes
