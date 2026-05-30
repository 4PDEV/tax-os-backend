from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.datetime_utils import utc_now
from app.services.segmentation import (
    BaseSegmenter,
    GenericSegmenter,
    LegislativeSegmenter,
    Segment,
    SegmentationMetadata,
    SegmentationResult,
    SegmentationStatus,
    SegmentMetadata,
    SegmentType,
)


def test_segment_type_has_only_permitted_values():
    assert {s.value for s in SegmentType} == {
        "document",
        "part",
        "chapter",
        "section",
        "article",
        "clause",
        "subclause",
        "paragraph",
        "schedule",
        "unknown",
    }


def test_segmentation_status_has_only_permitted_values():
    assert {s.value for s in SegmentationStatus} == {
        "pending",
        "success",
        "failed",
        "partial",
    }


def _segment(**overrides) -> Segment:
    base = dict(
        segment_id="seg-0000",
        segment_type=SegmentType.DOCUMENT,
        hierarchy_level=0,
        parent_segment_id=None,
        sequence_number=0,
        heading=None,
        raw_text="hello",
        start_offset=0,
        end_offset=5,
    )
    base.update(overrides)
    return Segment(**base)


def test_segment_requires_core_fields_and_allows_metadata():
    segment = _segment()
    assert isinstance(segment.metadata, SegmentMetadata)
    assert segment.segment_type is SegmentType.DOCUMENT


def test_segment_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        _segment(legal_meaning="forbidden")


def test_segment_rejects_inverted_offsets():
    with pytest.raises(ValidationError):
        _segment(start_offset=10, end_offset=2)


def test_segmentation_result_enforces_segment_count_matches():
    with pytest.raises(ValidationError):
        SegmentationResult(
            source_version_id=uuid4(),
            segmentation_status=SegmentationStatus.SUCCESS,
            segmenter_name="generic",
            segmenter_version="1.0.0",
            segmented_at=utc_now(),
            segment_count=5,
            segments=[_segment()],
        )


def test_segmentation_result_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        SegmentationResult(
            source_version_id=uuid4(),
            segmentation_status=SegmentationStatus.PENDING,
            segmenter_name="generic",
            segmenter_version="1.0.0",
            segmented_at=utc_now(),
            segment_count=0,
            segments=[],
            interpretation="not allowed",
        )


def test_segmentation_metadata_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        SegmentationMetadata(summary="forbidden")


def test_legislative_segmenter_is_skeleton():
    seg = LegislativeSegmenter()
    assert isinstance(seg, BaseSegmenter)
    assert seg.can_handle(raw_text="anything") is False
    with pytest.raises(NotImplementedError):
        seg.segment(source_version_id=uuid4(), raw_text="anything")


def test_segmenters_inherit_base_contract():
    for seg in (GenericSegmenter(), LegislativeSegmenter()):
        assert isinstance(seg, BaseSegmenter)
        assert seg.name
        assert seg.version
