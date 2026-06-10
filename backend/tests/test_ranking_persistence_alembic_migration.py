from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

REVISION_FILE = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "a8c1e4f92b37_create_ranking_persistence_tables.py"
)
REVISION_ID = "a8c1e4f92b37"
ROOT_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = ROOT_DIR / "alembic.ini"
MIGRATIONS_PATH = ROOT_DIR / "backend" / "migrations"

TABLES = (
    "ranking_requests",
    "ranking_results",
    "ranked_evidence_references",
)


def _migration_source() -> str:
    assert REVISION_FILE.exists(), "ranking persistence migration file must exist"
    return REVISION_FILE.read_text()


def test_migration_file_exists():
    assert REVISION_FILE.is_file()
    assert REVISION_ID in _migration_source()


def test_migration_creates_ranking_tables():
    source = _migration_source()
    for table in TABLES:
        assert table in source
    assert "uq_ranking_requests_hash_default" in source
    assert "uq_ranked_evidence_result_order" in source
    assert "uq_ranked_evidence_result_evidence" in source
    assert "fk_ranked_evidence_composite_membership" in source
    assert "uq_retrieval_evidence_result_id_pk" in source


def test_migration_revises_retrieval_head():
    assert "f9e4d2a87c10" in _migration_source()


@pytest.mark.integration
def test_ranking_tables_exist_at_head(engine):
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    for table in TABLES:
        assert table in tables


@pytest.mark.integration
def test_partial_unique_index_exists_at_head(engine):
    inspector = inspect(engine)
    indexes = inspector.get_indexes("ranking_requests")
    names = {idx["name"] for idx in indexes}
    assert "uq_ranking_requests_hash_default" in names


@pytest.mark.integration
def test_ranked_evidence_unique_constraints_exist_at_head(engine):
    inspector = inspect(engine)
    constraints = inspector.get_unique_constraints("ranked_evidence_references")
    names = {c["name"] for c in constraints}
    assert "uq_ranked_evidence_result_order" in names
    assert "uq_ranked_evidence_result_evidence" in names


@pytest.mark.integration
def test_retrieval_evidence_composite_unique_exists_at_head(engine):
    inspector = inspect(engine)
    constraints = inspector.get_unique_constraints("retrieval_evidence_references")
    names = {c["name"] for c in constraints}
    assert "uq_retrieval_evidence_result_id_pk" in names


@pytest.mark.integration
def test_composite_fk_exists_at_head(engine):
    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("ranked_evidence_references")
    names = {fk["name"] for fk in fks}
    assert "fk_ranked_evidence_composite_membership" in names


@pytest.mark.integration
def test_downgrade_removes_and_upgrade_restores_ranking_tables(migrated_test_database):
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_PATH))

    command.downgrade(alembic_cfg, "f9e4d2a87c10")
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
