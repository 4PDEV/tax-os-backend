import hashlib
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.datetime_utils import utc_now
from app.services.legal_object_extraction import (
    LegalObjectExtractor,
    LegalObjectExtractionStatus,
    LegalObjectType,
    generate_legal_object_id,
    sha256_text,
)
from app.services.legal_object_extraction.models import LegalObjectCandidate
from app.services.structure_parser.enums import StructuralUnitType
from app.services.structure_parser.models import StructuralUnit


def _unit(
    *,
    unit_id: str,
    unit_type: StructuralUnitType,
    unit_label: str,
    parent_unit_id: str | None = None,
    hierarchy_level: int = 0,
    start_offset: int = 0,
    end_offset: int = 10,
    raw_text: str = "sample text",
    source_version_id=None,
) -> StructuralUnit:
    sid = source_version_id or uuid4()
    return StructuralUnit(
        source_version_id=sid,
        unit_id=unit_id,
        unit_type=unit_type,
        unit_label=unit_label,
        unit_title=None,
        full_heading=unit_label,
        parent_unit_id=parent_unit_id,
        hierarchy_level=hierarchy_level,
        start_offset=start_offset,
        end_offset=end_offset,
        raw_text=raw_text,
        detected_at=utc_now(),
        parser_version="1.0.0",
    )


def test_empty_input_returns_empty_list():
    assert LegalObjectExtractor().extract([]) == []


def test_one_structural_unit_produces_one_candidate():
    units = [_unit(unit_id="su-0000", unit_type=StructuralUnitType.SECTION, unit_label="Section 15")]
    results = LegalObjectExtractor().extract(units)
    assert len(results) == 1
    assert results[0].structural_unit_id == "su-0000"


def test_object_type_mapping():
    units = [
        _unit(unit_id="su-0000", unit_type=StructuralUnitType.SECTION, unit_label="Section 1"),
        _unit(unit_id="su-0001", unit_type=StructuralUnitType.UNKNOWN, unit_label="Unknown block"),
    ]
    results = LegalObjectExtractor().extract(units)
    assert results[0].object_type is LegalObjectType.SECTION
    assert results[1].object_type is LegalObjectType.UNKNOWN


def test_deterministic_legal_object_id_stable():
    sid = uuid4()
    units = [
        _unit(
            unit_id="su-0000",
            unit_type=StructuralUnitType.SECTION,
            unit_label="Section 15",
            raw_text="Section 15 body",
            source_version_id=sid,
        )
    ]
    first = LegalObjectExtractor().extract(units)[0]
    second = LegalObjectExtractor().extract(units)[0]
    assert first.legal_object_id == second.legal_object_id
    assert first.legal_object_id.startswith("lo_")
    assert len(first.legal_object_id) == 35  # lo_ + 32 hex chars


def test_text_hash_is_sha256_of_raw_text():
    raw = "Section 15 registration threshold text"
    units = [_unit(unit_id="su-0000", unit_type=StructuralUnitType.SECTION, unit_label="Section 15", raw_text=raw)]
    result = LegalObjectExtractor().extract(units)[0]
    assert result.text_hash == sha256_text(raw)
    assert result.text_hash == hashlib.sha256(raw.encode("utf-8")).hexdigest()


def test_canonical_path_for_root_unit():
    units = [_unit(unit_id="su-0000", unit_type=StructuralUnitType.PART, unit_label="PART I")]
    result = LegalObjectExtractor().extract(units)[0]
    assert result.canonical_path == "PART I"


def test_canonical_path_for_nested_hierarchy():
    units = [
        _unit(unit_id="su-0000", unit_type=StructuralUnitType.PART, unit_label="PART I", hierarchy_level=0),
        _unit(
            unit_id="su-0001",
            unit_type=StructuralUnitType.CHAPTER,
            unit_label="CHAPTER 1",
            parent_unit_id="su-0000",
            hierarchy_level=1,
        ),
        _unit(
            unit_id="su-0002",
            unit_type=StructuralUnitType.SECTION,
            unit_label="Section 15",
            parent_unit_id="su-0001",
            hierarchy_level=2,
            raw_text="Section 15 body",
        ),
    ]
    results = LegalObjectExtractor().extract(units)
    section = results[2]
    assert section.canonical_path == "PART I > CHAPTER 1 > Section 15"


def test_parent_legal_object_id_resolves_to_candidate_not_structural_id():
    units = [
        _unit(unit_id="su-0000", unit_type=StructuralUnitType.PART, unit_label="PART I"),
        _unit(
            unit_id="su-0001",
            unit_type=StructuralUnitType.SECTION,
            unit_label="Section 15",
            parent_unit_id="su-0000",
        ),
    ]
    results = LegalObjectExtractor().extract(units)
    assert results[1].parent_legal_object_id == results[0].legal_object_id
    assert results[1].parent_legal_object_id != "su-0000"


def test_missing_structural_parent_produces_partial_status():
    units = [
        _unit(
            unit_id="su-0009",
            unit_type=StructuralUnitType.SECTION,
            unit_label="Section 99",
            parent_unit_id="su-missing",
        )
    ]
    result = LegalObjectExtractor().extract(units)[0]
    assert result.extraction_status is LegalObjectExtractionStatus.PARTIAL
    assert result.parent_legal_object_id is None
    assert result.metadata.get("extraction_warning")


def test_input_ordering_preserved():
    units = [
        _unit(unit_id="su-0000", unit_type=StructuralUnitType.PART, unit_label="PART I", start_offset=0, end_offset=10),
        _unit(
            unit_id="su-0001",
            unit_type=StructuralUnitType.SECTION,
            unit_label="Section 1",
            parent_unit_id="su-0000",
            start_offset=10,
            end_offset=20,
        ),
        _unit(
            unit_id="su-0002",
            unit_type=StructuralUnitType.SECTION,
            unit_label="Section 2",
            parent_unit_id="su-0000",
            start_offset=20,
            end_offset=30,
        ),
    ]
    results = LegalObjectExtractor().extract(units)
    assert [r.structural_unit_id for r in results] == ["su-0000", "su-0001", "su-0002"]
    assert [r.start_offset for r in results] == [0, 10, 20]


def test_raw_text_and_offsets_preserved_exactly():
    raw = "Section 15 — exact body text\nline two"
    units = [
        _unit(
            unit_id="su-0000",
            unit_type=StructuralUnitType.SECTION,
            unit_label="Section 15",
            start_offset=42,
            end_offset=42 + len(raw),
            raw_text=raw,
        )
    ]
    result = LegalObjectExtractor().extract(units)[0]
    assert result.raw_text == raw
    assert result.start_offset == 42
    assert result.end_offset == 42 + len(raw)


def test_no_random_uuid_in_legal_object_id():
    units = [_unit(unit_id="su-0000", unit_type=StructuralUnitType.ARTICLE, unit_label="Article 5")]
    result = LegalObjectExtractor().extract(units)[0]
    assert result.legal_object_id.startswith("lo_")
    hex_part = result.legal_object_id[3:]
    assert len(hex_part) == 32
    assert all(c in "0123456789abcdef" for c in hex_part)


def test_pydantic_model_forbids_extra_fields():
    with pytest.raises(ValidationError):
        LegalObjectCandidate(
            source_version_id="sv-1",
            legal_object_id="lo_" + "a" * 32,
            object_type=LegalObjectType.SECTION,
            object_label="Section 1",
            object_title=None,
            canonical_path="Section 1",
            parent_legal_object_id=None,
            structural_unit_id="su-0000",
            start_offset=0,
            end_offset=5,
            raw_text="text",
            text_hash=sha256_text("text"),
            extraction_status=LegalObjectExtractionStatus.SUCCESS,
            extracted_at=utc_now(),
            extractor_version="1.0.0",
            interpretation="forbidden",
        )


def test_repeated_extraction_produces_identical_ids_and_paths():
    sid = uuid4()
    units = [
        _unit(unit_id="su-0000", unit_type=StructuralUnitType.PART, unit_label="PART I", source_version_id=sid),
        _unit(
            unit_id="su-0001",
            unit_type=StructuralUnitType.SECTION,
            unit_label="Section 15",
            parent_unit_id="su-0000",
            source_version_id=sid,
        ),
    ]
    first = LegalObjectExtractor().extract(units)
    second = LegalObjectExtractor().extract(units)
    assert [(c.legal_object_id, c.canonical_path) for c in first] == [
        (c.legal_object_id, c.canonical_path) for c in second
    ]


def test_generate_legal_object_id_function_directly():
    id_a = generate_legal_object_id(
        source_version_id="sv-1",
        canonical_path="PART I > Section 15",
        object_type="section",
        object_label="Section 15",
        start_offset=100,
        text_hash="abc123",
    )
    id_b = generate_legal_object_id(
        source_version_id="sv-1",
        canonical_path="PART I > Section 15",
        object_type="section",
        object_label="Section 15",
        start_offset=100,
        text_hash="abc123",
    )
    id_c = generate_legal_object_id(
        source_version_id="sv-1",
        canonical_path="PART I > Section 15",
        object_type="section",
        object_label="Section 15",
        start_offset=101,
        text_hash="abc123",
    )
    assert id_a == id_b
    assert id_a != id_c
