from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.datetime_utils import utc_now
from app.services.citation_anchors import (
    BaseCitationAnchorGenerator,
    CanonicalCitationAnchor,
    CitationAnchorGenerationMetadata,
    CitationAnchorGenerationResult,
    CitationAnchorMetadata,
    CitationAnchorType,
    GenerationStatus,
    GenericCitationAnchorGenerator,
    LegislativeCitationAnchorGenerator,
)
from app.services.legal_objects.models import LegalObjectExtractionResult


def test_citation_anchor_type_has_only_permitted_values():
    assert {t.value for t in CitationAnchorType} == {
        "document",
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


def test_generation_status_has_only_permitted_values():
    assert {s.value for s in GenerationStatus} == {
        "pending",
        "success",
        "failed",
        "partial",
    }


def _anchor(**overrides) -> CanonicalCitationAnchor:
    base = dict(
        citation_anchor_id="a" * 64,
        source_version_id=uuid4(),
        legal_object_id="lo-0001",
        source_segment_id="seg-0001",
        anchor_type=CitationAnchorType.SECTION,
        canonical_anchor="SECTION:12",
        display_label="Section 12",
        hierarchy_path=["SECTION:12"],
        sequence_number=1,
        start_offset=0,
        end_offset=10,
        raw_text="Section 12",
    )
    base.update(overrides)
    return CanonicalCitationAnchor(**base)


def test_anchor_requires_core_fields_and_allows_metadata():
    anchor = _anchor()
    assert isinstance(anchor.metadata, CitationAnchorMetadata)
    assert anchor.anchor_type is CitationAnchorType.SECTION


def test_anchor_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        _anchor(authority_rank="forbidden")


def test_anchor_rejects_inverted_offsets():
    with pytest.raises(ValidationError):
        _anchor(start_offset=10, end_offset=2)


def test_anchor_metadata_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        CitationAnchorMetadata(topic_tag="forbidden")


def test_result_enforces_count_matches():
    with pytest.raises(ValidationError):
        CitationAnchorGenerationResult(
            source_version_id=uuid4(),
            generation_status=GenerationStatus.SUCCESS,
            generator_name="generic",
            generator_version="1.0.0",
            generated_at=utc_now(),
            citation_anchor_count=5,
            citation_anchors=[_anchor()],
        )


def test_result_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        CitationAnchorGenerationResult(
            source_version_id=uuid4(),
            generation_status=GenerationStatus.PENDING,
            generator_name="generic",
            generator_version="1.0.0",
            generated_at=utc_now(),
            citation_anchor_count=0,
            citation_anchors=[],
            authority_ranking="forbidden",
        )


def test_generation_metadata_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        CitationAnchorGenerationMetadata(risk_assessment="forbidden")


def test_legislative_generator_is_skeleton():
    generator = LegislativeCitationAnchorGenerator()
    assert isinstance(generator, BaseCitationAnchorGenerator)
    empty = LegalObjectExtractionResult(
        source_version_id=uuid4(),
        extraction_status="success",
        extractor_name="generic",
        extractor_version="1.0.0",
        extracted_at=utc_now(),
        legal_object_count=0,
        legal_objects=[],
    )
    assert generator.can_handle(extraction_result=empty) is False
    with pytest.raises(NotImplementedError):
        generator.generate(extraction_result=empty)


def test_generators_inherit_base_contract():
    for generator in (GenericCitationAnchorGenerator(), LegislativeCitationAnchorGenerator()):
        assert isinstance(generator, BaseCitationAnchorGenerator)
        assert generator.name
        assert generator.version
