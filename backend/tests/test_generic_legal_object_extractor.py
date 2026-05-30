from uuid import uuid4

from app.services.legal_objects.enums import ExtractionStatus, LegalObjectType
from app.services.legal_objects.extractors.generic import GenericLegalObjectExtractor
from app.services.segmentation.enums import SegmentType
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


def _segmented(text: str, source_version_id=None):
    sid = source_version_id or uuid4()
    return GenericSegmenter().segment(source_version_id=sid, raw_text=text)


def _extract(text: str, source_version_id=None):
    seg = _segmented(text, source_version_id)
    return seg, GenericLegalObjectExtractor().extract(segmentation_result=seg)


def test_one_object_per_segment_and_count_matches():
    seg, result = _extract(SAMPLE)
    assert result.legal_object_count == len(result.legal_objects)
    assert result.legal_object_count == seg.segment_count
    assert result.extraction_status is ExtractionStatus.SUCCESS


def test_source_version_id_preserved():
    sid = uuid4()
    seg, result = _extract(SAMPLE, source_version_id=sid)
    assert result.source_version_id == sid
    for obj in result.legal_objects:
        assert obj.source_version_id == sid


def test_source_segment_id_preserved():
    seg, result = _extract(SAMPLE)
    segment_ids = [s.segment_id for s in seg.segments]
    object_segment_ids = [o.source_segment_id for o in result.legal_objects]
    assert object_segment_ids == segment_ids


def test_raw_text_and_offsets_preserved_from_segments():
    seg, result = _extract(SAMPLE)
    by_segment = {s.segment_id: s for s in seg.segments}
    for obj in result.legal_objects:
        source_segment = by_segment[obj.source_segment_id]
        assert obj.raw_text == source_segment.raw_text
        assert obj.start_offset == source_segment.start_offset
        assert obj.end_offset == source_segment.end_offset
        assert SAMPLE[obj.start_offset:obj.end_offset] == obj.raw_text


def test_segment_type_surface_mapping():
    seg, result = _extract(SAMPLE)
    by_segment = {s.segment_id: s for s in seg.segments}
    expected = {
        SegmentType.DOCUMENT: LegalObjectType.UNKNOWN,
        SegmentType.PART: LegalObjectType.PART,
        SegmentType.CHAPTER: LegalObjectType.CHAPTER,
        SegmentType.SECTION: LegalObjectType.SECTION,
        SegmentType.ARTICLE: LegalObjectType.ARTICLE,
        SegmentType.CLAUSE: LegalObjectType.CLAUSE,
        SegmentType.SUBCLAUSE: LegalObjectType.SUBCLAUSE,
        SegmentType.PARAGRAPH: LegalObjectType.PARAGRAPH,
        SegmentType.SCHEDULE: LegalObjectType.SCHEDULE,
        SegmentType.UNKNOWN: LegalObjectType.UNKNOWN,
    }
    for obj in result.legal_objects:
        seg_type = by_segment[obj.source_segment_id].segment_type
        assert obj.object_type is expected[seg_type]


def test_hierarchy_level_preserved_from_segments():
    seg, result = _extract(SAMPLE)
    by_segment = {s.segment_id: s for s in seg.segments}
    for obj in result.legal_objects:
        assert obj.hierarchy_level == by_segment[obj.source_segment_id].hierarchy_level


def test_parent_child_relationship_preserved():
    seg, result = _extract(SAMPLE)
    seg_to_obj = {s.segment_id: o.legal_object_id for s, o in zip(seg.segments, result.legal_objects)}
    by_segment = {s.segment_id: s for s in seg.segments}
    for obj, source_segment in zip(result.legal_objects, seg.segments):
        if source_segment.parent_segment_id is None:
            assert obj.parent_legal_object_id is None
        else:
            assert obj.parent_legal_object_id == seg_to_obj[source_segment.parent_segment_id]


def test_document_segment_maps_to_unknown_object():
    seg, result = _extract(SAMPLE)
    root = result.legal_objects[0]
    assert root.object_type is LegalObjectType.UNKNOWN
    assert root.metadata.mapped_from_segment_type == "document"
    assert root.metadata.confidence_of_structural_mapping == 0.0


def test_extraction_is_deterministic_across_runs():
    sid = uuid4()
    seg_a = GenericSegmenter().segment(source_version_id=sid, raw_text=SAMPLE)
    seg_b = GenericSegmenter().segment(source_version_id=sid, raw_text=SAMPLE)
    first = GenericLegalObjectExtractor().extract(segmentation_result=seg_a)
    second = GenericLegalObjectExtractor().extract(segmentation_result=seg_b)
    assert [o.model_dump() for o in first.legal_objects] == [o.model_dump() for o in second.legal_objects]


def test_empty_text_yields_single_unknown_object():
    seg, result = _extract("")
    assert result.legal_object_count == 1
    assert result.legal_objects[0].object_type is LegalObjectType.UNKNOWN
    assert result.legal_objects[0].raw_text == ""
