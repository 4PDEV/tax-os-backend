from pathlib import Path

REVISION_FILE = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "d4b7f91e62a1_create_monitoring_persistence_tables.py"
)
REVISION_ID = "d4b7f91e62a1"

MONITORING_TABLES = (
    "source_allowlist_entries",
    "monitoring_attempts",
    "monitoring_events",
    "monitoring_candidates",
    "monitoring_candidate_state_transitions",
)


def _migration_source() -> str:
    assert REVISION_FILE.exists(), "monitoring persistence migration file must exist"
    return REVISION_FILE.read_text()


def test_migration_file_exists():
    assert REVISION_FILE.is_file()
    assert REVISION_ID in _migration_source()


def test_migration_creates_all_monitoring_tables():
    source = _migration_source()
    for table in MONITORING_TABLES:
        assert table in source
        assert "create_table" in source


def test_migration_revises_ingestion_head():
    source = _migration_source()
    assert "c9a2f3b81d06" in source
