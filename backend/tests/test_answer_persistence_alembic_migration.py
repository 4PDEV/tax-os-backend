from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

REVISION_FILE = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "c7e3a1f94d82_create_answer_persistence_tables.py"
)
REVISION_ID = "c7e3a1f94d82"
ROOT_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = ROOT_DIR / "alembic.ini"
MIGRATIONS_PATH = ROOT_DIR / "backend" / "migrations"

TABLES = (
    "answer_requests",
    "answer_results",
    "answer_evidence_entries",
    "answer_uncertainty_flags",
)


def _migration_source() -> str:
    assert REVISION_FILE.exists(), "answer persistence migration file must exist"
    return REVISION_FILE.read_text()


def test_migration_file_exists():
    assert REVISION_FILE.is_file()
    assert REVISION_ID in _migration_source()


def test_migration_creates_answer_tables():
    source = _migration_source()
    for table in TABLES:
        assert table in source
    assert "uq_answer_requests_hash_default" in source
    assert "uq_answer_evidence_result_order" in source
    assert "uq_answer_evidence_result_ranked" in source
    assert "uq_answer_evidence_result_retrieval" in source
    assert "fk_answer_evidence_retrieval_composite" in source
    assert "uq_ranked_evidence_result_id_pk" in source
    assert "ck_answer_result_status" in source
    assert "ck_answer_result_error_category" in source


def test_migration_revises_ranking_head():
    assert "a8c1e4f92b37" in _migration_source()


@pytest.mark.integration
def test_answer_tables_exist_at_head(engine):
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    for table in TABLES:
        assert table in tables


@pytest.mark.integration
def test_partial_unique_hash_index_exists_at_head(engine):
    inspector = inspect(engine)
    indexes = inspector.get_indexes("answer_requests")
    names = {idx["name"] for idx in indexes}
    assert "uq_answer_requests_hash_default" in names


@pytest.mark.integration
def test_answer_evidence_unique_constraints_exist_at_head(engine):
    inspector = inspect(engine)
    constraints = inspector.get_unique_constraints("answer_evidence_entries")
    names = {c["name"] for c in constraints}
    assert "uq_answer_evidence_result_order" in names
    assert "uq_answer_evidence_result_ranked" in names
    assert "uq_answer_evidence_result_retrieval" in names


@pytest.mark.integration
def test_ranked_evidence_result_id_pk_unique_exists_at_head(engine):
    inspector = inspect(engine)
    constraints = inspector.get_unique_constraints("ranked_evidence_references")
    names = {c["name"] for c in constraints}
    assert "uq_ranked_evidence_result_id_pk" in names


@pytest.mark.integration
def test_retrieval_composite_fk_exists_at_head(engine):
    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("answer_evidence_entries")
    names = {fk["name"] for fk in fks}
    assert "fk_answer_evidence_retrieval_composite" in names


@pytest.mark.integration
def test_check_constraints_exist_at_head(engine):
    inspector = inspect(engine)
    for table in TABLES:
        checks = inspector.get_check_constraints(table)
        assert checks, f"expected CHECK constraints on {table}"


@pytest.mark.integration
def test_downgrade_removes_and_upgrade_restores_answer_tables(migrated_test_database):
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_PATH))

    command.downgrade(alembic_cfg, "a8c1e4f92b37")
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
