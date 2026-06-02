from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

REVISION_FILE = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "a7e6c9b4d201_create_source_version_promotions_table.py"
)
REVISION_ID = "a7e6c9b4d201"
ROOT_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = ROOT_DIR / "alembic.ini"
MIGRATIONS_PATH = ROOT_DIR / "backend" / "migrations"


def _migration_source() -> str:
    assert REVISION_FILE.exists(), "source promotion migration file must exist"
    return REVISION_FILE.read_text()


def test_migration_file_exists():
    assert REVISION_FILE.is_file()
    assert REVISION_ID in _migration_source()


def test_migration_creates_source_version_promotions_table():
    source = _migration_source()
    assert "source_version_promotions" in source
    assert "create_table" in source
    assert "ck_source_version_promotion_status" in source


def test_migration_revises_change_detection_head():
    source = _migration_source()
    assert "f4c3b2a190de" in source


@pytest.mark.integration
def test_table_exists_at_head(engine):
    inspector = inspect(engine)
    assert "source_version_promotions" in set(inspector.get_table_names())


@pytest.mark.integration
def test_downgrade_and_upgrade_source_promotion_table(migrated_test_database):
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_PATH))

    command.downgrade(alembic_cfg, "f4c3b2a190de")
    from app.db.session import engine as app_engine

    inspector = inspect(app_engine)
    assert "source_version_promotions" not in set(inspector.get_table_names())

    command.upgrade(alembic_cfg, "head")
    inspector = inspect(app_engine)
    assert "source_version_promotions" in set(inspector.get_table_names())
