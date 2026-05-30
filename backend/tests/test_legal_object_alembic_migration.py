from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

ROOT_DIR = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = ROOT_DIR / "backend" / "migrations" / "versions"
ALEMBIC_INI_PATH = ROOT_DIR / "alembic.ini"
MIGRATIONS_PATH = ROOT_DIR / "backend" / "migrations"

REVISION_FILE = MIGRATIONS_DIR / "f7c2d9e41a83_create_legal_object_persistence_tables.py"
REVISION_ID = "f7c2d9e41a83"

LEGAL_OBJECT_TABLES = (
    "legal_objects",
    "legal_object_versions",
    "legal_object_lineage",
    "legal_object_duplicates",
)


def _migration_source() -> str:
    assert REVISION_FILE.exists(), "legal object migration revision file must exist"
    return REVISION_FILE.read_text()


def test_migration_file_exists():
    assert REVISION_FILE.is_file()
    assert REVISION_ID in _migration_source()


def test_migration_creates_all_four_tables():
    source = _migration_source()
    for table in LEGAL_OBJECT_TABLES:
        assert f'"{table}"' in source or f"'{table}'" in source
        assert "create_table" in source


def test_migration_includes_offset_check_constraint():
    source = _migration_source()
    assert "ck_legal_object_versions_offsets" in source
    assert "end_offset >= start_offset" in source


def test_migration_includes_required_indexes():
    source = _migration_source()
    required_indexes = (
        "ix_legal_objects_country_id",
        "ix_legal_objects_tax_type_id",
        "ix_legal_objects_object_type",
        "ix_legal_objects_canonical_path",
        "ix_legal_object_versions_source_version_id",
        "ix_legal_object_versions_text_hash",
        "ix_legal_object_versions_effective_dates",
        "ix_legal_object_lineage_parent_legal_object_id",
        "ix_legal_object_duplicates_primary_legal_object_id",
    )
    for index_name in required_indexes:
        assert index_name in source


def test_migration_downgrade_drops_in_reverse_dependency_order():
    source = _migration_source()
    downgrade = source.split("def downgrade")[1]
    dup_pos = downgrade.index('op.drop_table("legal_object_duplicates")')
    lineage_pos = downgrade.index('op.drop_table("legal_object_lineage")')
    versions_pos = downgrade.index('op.drop_table("legal_object_versions")')
    objects_pos = downgrade.index('op.drop_table("legal_objects")')
    assert dup_pos < lineage_pos < versions_pos < objects_pos


def test_no_repository_service_or_api_files_introduced():
    repo_root = ROOT_DIR / "backend" / "app"
    forbidden_patterns = (
        "legal_object_repository",
        "legal_object_persistence_service",
        "legal_object_routes",
    )
    for path in repo_root.rglob("*.py"):
        name = path.name.lower()
        for pattern in forbidden_patterns:
            assert pattern not in name


@pytest.mark.integration
def test_migration_tables_exist_at_head(engine):
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    for table in LEGAL_OBJECT_TABLES:
        assert table in tables


@pytest.mark.integration
def test_migration_required_columns_exist(engine):
    inspector = inspect(engine)
    legal_objects_cols = {col["name"] for col in inspector.get_columns("legal_objects")}
    assert {
        "legal_object_id",
        "source_document_id",
        "country_id",
        "tax_type_id",
        "object_type",
        "canonical_path",
        "current_version_id",
        "status",
        "created_at",
        "updated_at",
    } <= legal_objects_cols

    version_cols = {col["name"] for col in inspector.get_columns("legal_object_versions")}
    assert {
        "legal_object_version_id",
        "legal_object_id",
        "source_version_id",
        "parent_legal_object_id",
        "structural_unit_id",
        "object_label",
        "object_title",
        "start_offset",
        "end_offset",
        "raw_text",
        "text_hash",
        "effective_from",
        "effective_to",
        "version_status",
        "extraction_status",
        "created_at",
    } <= version_cols


@pytest.mark.integration
def test_migration_foreign_keys_exist(engine):
    inspector = inspect(engine)
    fk_map = {
        table: {
            fk["constrained_columns"][0]: fk["referred_table"]
            for fk in inspector.get_foreign_keys(table)
        }
        for table in LEGAL_OBJECT_TABLES
    }
    assert fk_map["legal_objects"]["source_document_id"] == "source_documents"
    assert fk_map["legal_object_versions"]["legal_object_id"] == "legal_objects"
    assert fk_map["legal_object_versions"]["source_version_id"] == "source_versions"
    assert fk_map["legal_object_lineage"]["legal_object_id"] == "legal_objects"
    assert fk_map["legal_object_duplicates"]["primary_legal_object_id"] == "legal_objects"


@pytest.mark.integration
def test_migration_indexes_exist(engine):
    inspector = inspect(engine)
    indexes = {table: {idx["name"] for idx in inspector.get_indexes(table)} for table in LEGAL_OBJECT_TABLES}
    assert "ix_legal_objects_country_id" in indexes["legal_objects"]
    assert "ix_legal_object_versions_text_hash" in indexes["legal_object_versions"]
    assert "ix_legal_object_lineage_parent_legal_object_id" in indexes["legal_object_lineage"]
    assert "ix_legal_object_duplicates_primary_legal_object_id" in indexes["legal_object_duplicates"]


@pytest.mark.integration
def test_migration_offset_check_constraint_exists(engine):
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'ck_legal_object_versions_offsets'
                """
            )
        ).scalar()
    assert row == 1


@pytest.mark.integration
def test_downgrade_removes_legal_object_tables(migrated_test_database):
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_PATH))
    command.downgrade(alembic_cfg, "-1")

    from app.db.session import engine as app_engine

    inspector = inspect(app_engine)
    tables = set(inspector.get_table_names())
    for table in LEGAL_OBJECT_TABLES:
        assert table not in tables

    command.upgrade(alembic_cfg, "head")

    inspector = inspect(app_engine)
    tables = set(inspector.get_table_names())
    for table in LEGAL_OBJECT_TABLES:
        assert table in tables
