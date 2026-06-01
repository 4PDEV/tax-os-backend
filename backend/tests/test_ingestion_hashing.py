from app.services.ingestion.hashing import (
    canonical_structure_units_for_hash,
    sha256_structure,
    sha256_text,
)


def test_sha256_text_is_deterministic():
    text = "Section 15 applies to taxable supplies."
    assert sha256_text(text) == sha256_text(text)
    assert sha256_text(text) != sha256_text(text + " ")


def test_sha256_structure_ignores_volatile_fields():
    units_a = [
        {
            "unit_id": "u1",
            "unit_type": "section",
            "unit_label": "15",
            "unit_title": None,
            "full_heading": "Section 15",
            "parent_unit_id": None,
            "hierarchy_level": 1,
            "start_offset": 0,
            "end_offset": 10,
            "raw_text": "Tax is due.",
            "detected_at": "2026-01-01T00:00:00Z",
            "parser_version": "1.0.0",
            "source_version_id": "00000000-0000-0000-0000-000000000001",
        }
    ]
    units_b = [
        {
            **units_a[0],
            "unit_id": "different-id",
            "detected_at": "2099-12-31T23:59:59Z",
            "parser_version": "9.9.9",
            "source_version_id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
        }
    ]
    assert sha256_structure(units_a) == sha256_structure(units_b)


def test_sha256_structure_order_independent_by_start_offset():
    unit_one = {
        "unit_type": "section",
        "unit_label": "1",
        "unit_title": None,
        "full_heading": "Section 1",
        "parent_unit_id": None,
        "hierarchy_level": 0,
        "start_offset": 0,
        "end_offset": 5,
        "raw_text": "AAA",
    }
    unit_two = {
        **unit_one,
        "unit_label": "2",
        "full_heading": "Section 2",
        "start_offset": 5,
        "end_offset": 10,
        "raw_text": "BBB",
    }
    assert sha256_structure([unit_two, unit_one]) == sha256_structure([unit_one, unit_two])


def test_canonical_structure_units_for_hash_strips_volatile_keys():
    units = [{"unit_type": "section", "unit_label": "1", "start_offset": 0, "end_offset": 1, "raw_text": "x"}]
    canonical = canonical_structure_units_for_hash(units)
    assert "unit_id" not in canonical[0]
