from pathlib import Path

import pytest
from sqlalchemy import inspect

from app.models import (
    LegalObject,
    LegalObjectDuplicate,
    LegalObjectLineage,
    LegalObjectVersion,
)
from app.models import __all__ as models_all


MODELS = {
    "legal_objects": (LegalObject, "legal_objects"),
    "legal_object_versions": (LegalObjectVersion, "legal_object_versions"),
    "legal_object_lineage": (LegalObjectLineage, "legal_object_lineage"),
    "legal_object_duplicates": (LegalObjectDuplicate, "legal_object_duplicates"),
}


def _column_names(model) -> set[str]:
    return {column.name for column in inspect(model).columns}


def _column(model, name):
    return inspect(model).columns[name]


def _fk_targets(model) -> set[str]:
    targets: set[str] = set()
    for column in inspect(model).columns:
        for fk in column.foreign_keys:
            targets.add(f"{fk.column.table.name}.{fk.column.name}")
    return targets


def test_all_four_models_import_successfully():
    for model, _ in MODELS.values():
        assert model.__tablename__


@pytest.mark.parametrize(
    ("model", "table_name"),
    [MODELS[name] for name in MODELS],
)
def test_table_names(model, table_name):
    assert model.__tablename__ == table_name


def test_legal_object_required_columns_and_pk():
    cols = _column_names(LegalObject)
    required = {
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
    }
    assert required <= cols
    assert _column(LegalObject, "legal_object_id").primary_key is True
    assert _column(LegalObject, "legal_object_id").default is None
    assert _column(LegalObject, "canonical_path").nullable is False
    assert _column(LegalObject, "tax_type_id").nullable is True
    assert _column(LegalObject, "current_version_id").nullable is True


def test_legal_object_foreign_keys():
    targets = _fk_targets(LegalObject)
    assert "source_documents.id" in targets
    assert "countries.id" in targets
    assert "tax_types.id" in targets
    assert "legal_object_versions.legal_object_version_id" in targets


def test_legal_object_version_required_columns_and_pk():
    cols = _column_names(LegalObjectVersion)
    required = {
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
    }
    assert required <= cols
    assert _column(LegalObjectVersion, "legal_object_version_id").primary_key is True
    assert _column(LegalObjectVersion, "raw_text").nullable is False
    assert _column(LegalObjectVersion, "text_hash").nullable is False
    assert _column(LegalObjectVersion, "parent_legal_object_id").nullable is True
    assert _column(LegalObjectVersion, "object_title").nullable is True
    assert _column(LegalObjectVersion, "effective_from").nullable is True


def test_legal_object_version_foreign_keys():
    targets = _fk_targets(LegalObjectVersion)
    assert "legal_objects.legal_object_id" in targets
    assert "source_versions.id" in targets


def test_legal_object_lineage_required_columns():
    cols = _column_names(LegalObjectLineage)
    required = {
        "id",
        "legal_object_id",
        "parent_legal_object_id",
        "supersedes_legal_object_id",
        "superseded_by_legal_object_id",
        "relationship_type",
        "source_version_id",
        "created_at",
    }
    assert required <= cols
    assert _column(LegalObjectLineage, "id").primary_key is True
    assert _column(LegalObjectLineage, "parent_legal_object_id").nullable is True
    assert _column(LegalObjectLineage, "supersedes_legal_object_id").nullable is True
    assert _column(LegalObjectLineage, "superseded_by_legal_object_id").nullable is True


def test_legal_object_lineage_foreign_keys():
    targets = _fk_targets(LegalObjectLineage)
    assert sum(1 for t in targets if t == "legal_objects.legal_object_id") >= 1
    assert "source_versions.id" in targets


def test_legal_object_duplicate_required_columns():
    cols = _column_names(LegalObjectDuplicate)
    required = {
        "id",
        "primary_legal_object_id",
        "duplicate_legal_object_id",
        "duplicate_type",
        "text_hash_match",
        "canonical_path_match",
        "resolution_status",
        "created_at",
        "notes",
    }
    assert required <= cols
    assert _column(LegalObjectDuplicate, "id").primary_key is True
    assert _column(LegalObjectDuplicate, "notes").nullable is True
    assert _column(LegalObjectDuplicate, "text_hash_match").nullable is False


def test_legal_object_duplicate_foreign_keys():
    targets = _fk_targets(LegalObjectDuplicate)
    assert "legal_objects.legal_object_id" in targets


def test_models_included_in_models_init():
    assert "LegalObject" in models_all
    assert "LegalObjectVersion" in models_all
    assert "LegalObjectLineage" in models_all
    assert "LegalObjectDuplicate" in models_all


def test_legal_object_migration_file_exists():
    migrations_dir = Path(__file__).resolve().parents[1] / "migrations" / "versions"
    migration = migrations_dir / "f7c2d9e41a83_create_legal_object_persistence_tables.py"
    assert migration.is_file()
