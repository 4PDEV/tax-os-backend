from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = ROOT_DIR / "backend" / "migrations" / "versions"

REVISION_FILE = MIGRATIONS_DIR / "b8d4e1a92c05_add_legal_object_integrity_constraints.py"
REVISION_ID = "b8d4e1a92c05"
PARENT_REVISION = "f7c2d9e41a83"


def _migration_source() -> str:
    assert REVISION_FILE.exists()
    return REVISION_FILE.read_text()


def test_integrity_migration_file_exists():
    assert REVISION_FILE.is_file()
    assert REVISION_ID in _migration_source()
    assert f'Revises: {PARENT_REVISION}' in _migration_source() or PARENT_REVISION in _migration_source()


def test_integrity_migration_adds_status_checks():
    source = _migration_source()
    assert "ck_legal_objects_status" in source
    assert "ck_legal_object_versions_version_status" in source
    assert "draft" in source and "superseded" in source


def test_integrity_migration_adds_unique_object_hash():
    source = _migration_source()
    assert "uq_legal_object_versions_object_hash" in source
    assert "legal_object_id" in source
    assert "text_hash" in source


def test_integrity_migration_downgrade_drops_constraints():
    source = _migration_source()
    downgrade = source.split("def downgrade")[1]
    assert "uq_legal_object_versions_object_hash" in downgrade
    assert "ck_legal_object_versions_version_status" in downgrade
    assert "ck_legal_objects_status" in downgrade
