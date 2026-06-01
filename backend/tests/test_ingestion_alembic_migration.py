from pathlib import Path

REVISION_FILE = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "c9a2f3b81d06_create_ingestion_persistence_tables.py"
)
REVISION_ID = "c9a2f3b81d06"

INGESTION_TABLES = (
    "extraction_runs",
    "extracted_texts",
    "parser_runs",
    "parsed_structures",
    "ingestion_state_transitions",
)


def _migration_source() -> str:
    assert REVISION_FILE.exists(), "ingestion persistence migration revision file must exist"
    return REVISION_FILE.read_text()


def test_migration_file_exists():
    assert REVISION_FILE.is_file()
    assert REVISION_ID in _migration_source()


def test_migration_creates_all_ingestion_tables():
    source = _migration_source()
    for table in INGESTION_TABLES:
        assert table in source
        assert "create_table" in source


def test_migration_revises_legal_object_integrity_head():
    source = _migration_source()
    assert 'down_revision' in source
    assert "b8d4e1a92c05" in source
