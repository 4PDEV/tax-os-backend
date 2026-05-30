from uuid import uuid4

from app.services.structure_parser import StructuralParser
from app.services.structure_parser.enums import StructuralUnitType

HIERARCHY_SAMPLE = (
    "PART I\n"
    "GENERAL\n"
    "\n"
    "CHAPTER 1\n"
    "Introductory provisions.\n"
    "\n"
    "Section 15 — Registration Threshold\n"
    "The threshold is RWF 20,000,000.\n"
    "\n"
    "Section 16\n"
    "Other provisions apply.\n"
    "\n"
    "Schedule A\n"
    "Listed items.\n"
)


def _parse(text: str, source_version_id=None):
    sid = source_version_id or uuid4()
    return StructuralParser().parse(source_version_id=sid, text=text)


def test_part_chapter_section_article_schedule_detection():
    results = _parse(HIERARCHY_SAMPLE)
    types = [u.unit_type for u in results]
    assert StructuralUnitType.PART in types
    assert StructuralUnitType.CHAPTER in types
    assert StructuralUnitType.SECTION in types
    assert StructuralUnitType.SCHEDULE in types


def test_hierarchy_parent_child_relationships():
    results = _parse(HIERARCHY_SAMPLE)
    by_id = {u.unit_id: u for u in results}
    part = next(u for u in results if u.unit_type is StructuralUnitType.PART)
    chapter = next(u for u in results if u.unit_type is StructuralUnitType.CHAPTER)
    section15 = next(u for u in results if u.unit_label == "Section 15")
    assert chapter.parent_unit_id == part.unit_id
    assert section15.parent_unit_id == chapter.unit_id
    assert by_id[chapter.parent_unit_id].hierarchy_level < chapter.hierarchy_level
    assert chapter.hierarchy_level < section15.hierarchy_level


def test_ordering_preserved_by_document_position():
    results = _parse(HIERARCHY_SAMPLE)
    offsets = [u.start_offset for u in results]
    assert offsets == sorted(offsets)
    labels = [u.unit_label for u in results]
    assert labels.index("PART I") < labels.index("CHAPTER 1") < labels.index("Section 15")


def test_heading_extraction_with_title():
    results = _parse(HIERARCHY_SAMPLE)
    section15 = next(u for u in results if u.unit_label == "Section 15")
    assert section15.unit_title == "Registration Threshold"
    assert "Registration Threshold" in section15.full_heading


def test_offsets_and_raw_text_preserved():
    text = HIERARCHY_SAMPLE
    results = _parse(text)
    for unit in results:
        assert text[unit.start_offset:unit.end_offset] == unit.raw_text
        assert unit.end_offset >= unit.start_offset


def test_article_detection():
    text = "Article 5 — Definitions\nDefined terms apply.\n"
    results = _parse(text)
    assert len(results) == 1
    assert results[0].unit_type is StructuralUnitType.ARTICLE
    assert results[0].unit_label == "Article 5"
    assert results[0].unit_title == "Definitions"


def test_empty_text_returns_no_units():
    assert _parse("") == []


def test_no_structural_headings_returns_empty():
    assert _parse("Plain paragraph with no structural markers.\n") == []


def test_parse_is_deterministic_across_runs():
    sid = uuid4()
    first = StructuralParser().parse(source_version_id=sid, text=HIERARCHY_SAMPLE)
    second = StructuralParser().parse(source_version_id=sid, text=HIERARCHY_SAMPLE)
    assert [u.model_dump(exclude={"detected_at"}) for u in first] == [
        u.model_dump(exclude={"detected_at"}) for u in second
    ]


def test_parser_version_and_source_version_id_populated():
    sid = uuid4()
    results = _parse(HIERARCHY_SAMPLE, source_version_id=sid)
    assert results
    assert all(u.source_version_id == sid for u in results)
    assert all(u.parser_version == "1.0.0" for u in results)
