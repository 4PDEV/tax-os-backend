import importlib

import pytest

from app.services.legal_object_schema_contract import (
    DUPLICATE_HANDLING_ASSUMPTIONS,
    IMMUTABILITY_RULES,
    LINEAGE_RULES,
    MIGRATION_EXPECTATIONS,
    PROPOSED_TABLES,
    SCHEMA_CONSTRAINTS,
    SCHEMA_INDEXES,
    SCHEMA_TABLES,
    immutability_rules_are_documented,
    lineage_rules_are_documented,
    schema_contract_is_complete,
)
from app.services.legal_object_schema_contract.constraints import constraints_for_table
from app.services.legal_object_schema_contract.indexes import indexes_for_table
from app.services.legal_object_schema_contract.schema_definition import get_table_definition


@pytest.mark.parametrize("table_name", PROPOSED_TABLES)
def test_contract_defines_all_required_tables(table_name):
    table = get_table_definition(table_name)
    assert table is not None
    assert table.name == table_name
    assert table.purpose


def test_legal_objects_required_fields():
    table = get_table_definition("legal_objects")
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
    assert required <= table.field_names()


def test_legal_object_versions_required_fields():
    table = get_table_definition("legal_object_versions")
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
    assert required <= table.field_names()


def test_legal_object_lineage_required_fields():
    table = get_table_definition("legal_object_lineage")
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
    assert required <= table.field_names()


def test_legal_object_duplicates_required_fields():
    table = get_table_definition("legal_object_duplicates")
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
    assert required <= table.field_names()


def test_required_constraints_listed():
    descriptions = " ".join(c.description.lower() for c in SCHEMA_CONSTRAINTS)
    assert any("legal_object_id" in c.columns for c in SCHEMA_CONSTRAINTS if c.constraint_type.value == "unique")
    assert "source_version_id" in descriptions
    assert "text_hash" in descriptions
    assert "converged" in descriptions
    assert "in-place" in descriptions or "overwrite" in descriptions


def test_required_indexes_listed():
    index_keys = {(idx.table, idx.columns) for idx in SCHEMA_INDEXES}
    assert ("legal_objects", ("country_id",)) in index_keys
    assert ("legal_objects", ("tax_type_id",)) in index_keys
    assert ("legal_objects", ("object_type",)) in index_keys
    assert ("legal_objects", ("canonical_path",)) in index_keys
    assert ("legal_object_versions", ("source_version_id",)) in index_keys
    assert ("legal_object_versions", ("text_hash",)) in index_keys
    assert ("legal_object_versions", ("effective_from", "effective_to")) in index_keys
    assert ("legal_object_lineage", ("parent_legal_object_id",)) in index_keys
    assert ("legal_object_duplicates", ("primary_legal_object_id",)) in index_keys


def test_immutability_rules_present():
    assert immutability_rules_are_documented() is True
    assert any("raw_text" in rule for rule in IMMUTABILITY_RULES)
    assert any("text_hash" in rule for rule in IMMUTABILITY_RULES)
    assert any("historical" in rule.lower() for rule in IMMUTABILITY_RULES)


def test_lineage_rules_present():
    assert lineage_rules_are_documented() is True
    assert any("supersession" in rule.lower() for rule in LINEAGE_RULES)
    assert any("silent merge" in rule.lower() for rule in LINEAGE_RULES)
    assert len(DUPLICATE_HANDLING_ASSUMPTIONS) >= 3
    assert len(MIGRATION_EXPECTATIONS) >= 3


def test_schema_contract_completeness():
    assert schema_contract_is_complete() is True
    assert len(SCHEMA_TABLES) == len(PROPOSED_TABLES)


def test_constraints_and_indexes_per_table():
    for table_name in PROPOSED_TABLES:
        assert constraints_for_table(table_name) or table_name == "legal_object_duplicates"
        if table_name != "legal_objects":
            assert indexes_for_table(table_name) or table_name == "legal_object_lineage"


def test_no_sqlalchemy_or_alembic_in_module():
    module = importlib.import_module("app.services.legal_object_schema_contract")
    source_files = [
        "contract",
        "models",
        "schema_definition",
        "constraints",
        "indexes",
        "immutability",
        "lineage",
    ]
    for name in source_files:
        mod = importlib.import_module(f"app.services.legal_object_schema_contract.{name}")
        text = open(mod.__file__).read()
        assert "from sqlalchemy" not in text.lower()
        assert "import sqlalchemy" not in text.lower()
        assert "from alembic" not in text.lower()
        assert "import alembic" not in text.lower()

    assert not hasattr(module, "Base")
    assert not hasattr(module, "Session")
