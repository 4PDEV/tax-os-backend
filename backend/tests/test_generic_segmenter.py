from uuid import uuid4

from app.services.segmentation.enums import SegmentationStatus, SegmentType
from app.services.segmentation.segmenters.generic import GenericSegmenter

SAMPLE = (
    "Article 1\n"
    "The standard VAT rate is 18%.\n"
    "\n"
    "Article 2\n"
    "Registration is mandatory above the threshold.\n"
    "\n"
    "(a) first condition\n"
    "\n"
    "(b) second condition\n"
)


def _segment(text: str):
    return GenericSegmenter().segment(source_version_id=uuid4(), raw_text=text)


def test_root_document_segment_spans_entire_text():
    result = _segment(SAMPLE)
    root = result.segments[0]
    assert root.segment_type is SegmentType.DOCUMENT
    assert root.hierarchy_level == 0
    assert root.parent_segment_id is None
    assert root.start_offset == 0
    assert root.end_offset == len(SAMPLE)
    assert root.raw_text == SAMPLE


def test_offsets_map_exactly_to_source_text():
    result = _segment(SAMPLE)
    for segment in result.segments:
        assert SAMPLE[segment.start_offset:segment.end_offset] == segment.raw_text


def test_sequence_numbers_are_ordered_and_contiguous():
    result = _segment(SAMPLE)
    sequences = [s.sequence_number for s in result.segments]
    assert sequences == list(range(len(result.segments)))


def test_segment_count_matches_segments_length():
    result = _segment(SAMPLE)
    assert result.segment_count == len(result.segments)
    assert result.segmentation_status is SegmentationStatus.SUCCESS


def test_structural_typing_detects_articles_and_subclauses():
    result = _segment(SAMPLE)
    types = [s.segment_type for s in result.segments[1:]]
    assert SegmentType.ARTICLE in types
    assert SegmentType.SUBCLAUSE in types


def test_hierarchy_preserved_parent_links_are_valid():
    result = _segment(SAMPLE)
    ids = {s.segment_id for s in result.segments}
    for segment in result.segments[1:]:
        assert segment.parent_segment_id in ids


def test_text_fidelity_concatenation_preserved_in_order():
    result = _segment(SAMPLE)
    for segment in result.segments[1:]:
        assert segment.raw_text in SAMPLE


def test_segmentation_is_deterministic_across_runs():
    first = _segment(SAMPLE)
    second = _segment(SAMPLE)
    first_dump = [s.model_dump() for s in first.segments]
    second_dump = [s.model_dump() for s in second.segments]
    assert first_dump == second_dump


def test_empty_text_yields_single_document_segment():
    result = _segment("")
    assert result.segment_count == 1
    assert result.segments[0].segment_type is SegmentType.DOCUMENT
    assert result.segments[0].raw_text == ""
    assert result.segmentation_status is SegmentationStatus.SUCCESS


def test_subclause_nested_under_preceding_article():
    result = _segment(SAMPLE)
    by_id = {s.segment_id: s for s in result.segments}
    subclauses = [s for s in result.segments if s.segment_type is SegmentType.SUBCLAUSE]
    assert subclauses
    for sub in subclauses:
        assert sub.hierarchy_level >= 1
        assert by_id[sub.parent_segment_id].hierarchy_level < sub.hierarchy_level
