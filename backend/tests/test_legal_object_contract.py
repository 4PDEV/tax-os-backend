from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.datetime_utils import utc_now
from app.services.legal_objects import (
    BaseLegalObjectExtractor,
    ExtractionStatus,
    GenericLegalObjectExtractor,
    LegalObjectCandidate,
    LegalObjectExtractionMetadata,
    LegalObjectExtractionResult,
    LegalObjectMetadata,
    LegalObjectType,
    LegislativeLegalObjectExtractor,
)
from app.services.segmentation.models import SegmentationResult


def test_legal_object_type_has_only_permitted_values():
    assert {t.value for t in LegalObjectType} == {
        "act",
        "regulation",
        "order",
        "notice",
        "judgment",
        "treaty",
        "part",
        "chapter",
        "section",
        "article",
        "clause",
        "subclause",
        "paragraph",
        "schedule",
        "definition",
        "unknown",
    }


def test_extraction_status_has_only_permitted_values():
    assert {s.value for s in ExtractionStatus} == {
        "pending",
        "success",
        "failed",
        "partial",
    }


def _candidate(**overrides) -> LegalObjectCandidate:
    base = dict(
        legal_object_id="lo-0000",
        source_version_id=uuid4(),
        source_segment_id="seg-0000",
        object_type=LegalObjectType.ARTICLE,
        object_label="Article 1",
        heading="Article 1",
        raw_text="Article 1\nText.",
        start_offset=0,
        end_offset=15,
        sequence_number=0,
        parent_legal_object_id=None,
        hierarchy_level=0,
    )
    base.update(overrides)
    return LegalObjectCandidate(**base)


def test_candidate_requires_core_fields_and_allows_metadata():
    candidate = _candidate()
    assert isinstance(candidate.metadata, LegalObjectMetadata)
    assert candidate.object_type is LegalObjectType.ARTICLE


def test_candidate_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        _candidate(legal_effect="forbidden")


def test_candidate_rejects_inverted_offsets():
    with pytest.raises(ValidationError):
        _candidate(start_offset=10, end_offset=2)


def test_candidate_metadata_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        LegalObjectMetadata(tax_topic="forbidden")


def test_result_enforces_count_matches():
    with pytest.raises(ValidationError):
        LegalObjectExtractionResult(
            source_version_id=uuid4(),
            extraction_status=ExtractionStatus.SUCCESS,
            extractor_name="generic",
            extractor_version="1.0.0",
            extracted_at=utc_now(),
            legal_object_count=5,
            legal_objects=[_candidate()],
        )


def test_result_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        LegalObjectExtractionResult(
            source_version_id=uuid4(),
            extraction_status=ExtractionStatus.PENDING,
            extractor_name="generic",
            extractor_version="1.0.0",
            extracted_at=utc_now(),
            legal_object_count=0,
            legal_objects=[],
            authority_rank="forbidden",
        )


def test_result_extraction_metadata_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        LegalObjectExtractionMetadata(risk_assessment="forbidden")


def test_legislative_extractor_is_skeleton():
    extractor = LegislativeLegalObjectExtractor()
    assert isinstance(extractor, BaseLegalObjectExtractor)
    empty = SegmentationResult(
        source_version_id=uuid4(),
        segmentation_status="success",
        segmenter_name="generic",
        segmenter_version="1.0.0",
        segmented_at=utc_now(),
        segment_count=0,
        segments=[],
    )
    assert extractor.can_handle(segmentation_result=empty) is False
    with pytest.raises(NotImplementedError):
        extractor.extract(segmentation_result=empty)


def test_extractors_inherit_base_contract():
    for extractor in (GenericLegalObjectExtractor(), LegislativeLegalObjectExtractor()):
        assert isinstance(extractor, BaseLegalObjectExtractor)
        assert extractor.name
        assert extractor.version
