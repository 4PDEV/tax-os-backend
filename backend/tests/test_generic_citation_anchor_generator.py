import hashlib
from uuid import uuid4

from app.core.datetime_utils import utc_now
from app.services.citation_anchors.enums import CitationAnchorType, GenerationStatus
from app.services.citation_anchors.generators.generic import GenericCitationAnchorGenerator
from app.services.legal_objects.enums import ExtractionStatus, LegalObjectType
from app.services.legal_objects.extractors.generic import GenericLegalObjectExtractor
from app.services.legal_objects.models import LegalObjectCandidate, LegalObjectExtractionResult
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


def _pipeline(text: str, source_version_id=None):
    sid = source_version_id or uuid4()
    seg = GenericSegmenter().segment(source_version_id=sid, raw_text=text)
    legal = GenericLegalObjectExtractor().extract(segmentation_result=seg)
    anchors = GenericCitationAnchorGenerator().generate(extraction_result=legal)
    return legal, anchors


def test_count_matches_and_status_success():
    legal, result = _pipeline(SAMPLE)
    assert result.citation_anchor_count == len(result.citation_anchors)
    assert result.citation_anchor_count == legal.legal_object_count
    assert result.generation_status is GenerationStatus.SUCCESS


def test_source_version_id_preserved():
    sid = uuid4()
    legal, result = _pipeline(SAMPLE, source_version_id=sid)
    assert result.source_version_id == sid
    for anchor in result.citation_anchors:
        assert anchor.source_version_id == sid


def test_legal_object_and_segment_ids_preserved():
    legal, result = _pipeline(SAMPLE)
    legal_by_seq = {o.sequence_number: o for o in legal.legal_objects}
    for anchor in result.citation_anchors:
        candidate = legal_by_seq[anchor.sequence_number]
        assert anchor.legal_object_id == candidate.legal_object_id
        assert anchor.source_segment_id == candidate.source_segment_id


def test_raw_text_and_offsets_preserved():
    legal, result = _pipeline(SAMPLE)
    legal_by_id = {o.legal_object_id: o for o in legal.legal_objects}
    for anchor in result.citation_anchors:
        candidate = legal_by_id[anchor.legal_object_id]
        assert anchor.raw_text == candidate.raw_text
        assert anchor.start_offset == candidate.start_offset
        assert anchor.end_offset == candidate.end_offset


def test_canonical_anchor_is_slash_joined_hierarchy_path():
    legal, result = _pipeline(SAMPLE)
    for anchor in result.citation_anchors:
        assert anchor.canonical_anchor == "/".join(anchor.hierarchy_path)


def test_citation_anchor_id_is_deterministic_sha256():
    legal, result = _pipeline(SAMPLE)
    for anchor in result.citation_anchors:
        raw = (
            f"{anchor.source_version_id}|{anchor.legal_object_id}|"
            f"{anchor.canonical_anchor}|{anchor.start_offset}|{anchor.end_offset}"
        )
        assert anchor.citation_anchor_id == hashlib.sha256(raw.encode("utf-8")).hexdigest()


def test_generation_is_deterministic_across_runs():
    sid = uuid4()
    _, first = _pipeline(SAMPLE, source_version_id=sid)
    _, second = _pipeline(SAMPLE, source_version_id=sid)
    assert [a.model_dump() for a in first.citation_anchors] == [a.model_dump() for a in second.citation_anchors]


def test_parent_child_path_building():
    legal, result = _pipeline(SAMPLE)
    legal_by_id = {o.legal_object_id: o for o in legal.legal_objects}
    anchors_by_object = {a.legal_object_id: a for a in result.citation_anchors}
    for anchor in result.citation_anchors:
        candidate = legal_by_id[anchor.legal_object_id]
        if candidate.parent_legal_object_id is None:
            assert len(anchor.hierarchy_path) == 1
        else:
            parent_anchor = anchors_by_object[candidate.parent_legal_object_id]
            assert anchor.hierarchy_path == parent_anchor.hierarchy_path + [anchor.hierarchy_path[-1]]


def test_anchor_type_surface_mapping():
    legal, result = _pipeline(SAMPLE)
    legal_by_id = {o.legal_object_id: o for o in legal.legal_objects}
    expected = {
        LegalObjectType.PART: CitationAnchorType.PART,
        LegalObjectType.CHAPTER: CitationAnchorType.CHAPTER,
        LegalObjectType.SECTION: CitationAnchorType.SECTION,
        LegalObjectType.ARTICLE: CitationAnchorType.ARTICLE,
        LegalObjectType.CLAUSE: CitationAnchorType.CLAUSE,
        LegalObjectType.SUBCLAUSE: CitationAnchorType.SUBCLAUSE,
        LegalObjectType.PARAGRAPH: CitationAnchorType.PARAGRAPH,
        LegalObjectType.SCHEDULE: CitationAnchorType.SCHEDULE,
        LegalObjectType.DEFINITION: CitationAnchorType.DEFINITION,
        LegalObjectType.UNKNOWN: CitationAnchorType.UNKNOWN,
    }
    for anchor in result.citation_anchors:
        candidate = legal_by_id[anchor.legal_object_id]
        assert anchor.anchor_type is expected[candidate.object_type]


def test_display_label_is_stable_and_titlecased():
    legal, result = _pipeline(SAMPLE)
    first_labels = [a.display_label for a in result.citation_anchors]
    _, second = _pipeline(SAMPLE)
    second_labels = [a.display_label for a in second.citation_anchors]
    assert first_labels == second_labels
    for anchor in result.citation_anchors:
        assert anchor.display_label.split(" ", 1)[0] == anchor.anchor_type.value.title()


def _result_with_missing_parent():
    sid = uuid4()
    candidate = LegalObjectCandidate(
        legal_object_id="lo-0009",
        source_version_id=sid,
        source_segment_id="seg-0009",
        object_type=LegalObjectType.CLAUSE,
        object_label="(1)",
        heading="(1)",
        raw_text="(1) orphaned clause",
        start_offset=5,
        end_offset=24,
        sequence_number=9,
        parent_legal_object_id="lo-9999",  # not present in collection
        hierarchy_level=2,
    )
    return LegalObjectExtractionResult(
        source_version_id=sid,
        extraction_status=ExtractionStatus.SUCCESS,
        extractor_name="generic",
        extractor_version="1.0.0",
        extracted_at=utc_now(),
        legal_object_count=1,
        legal_objects=[candidate],
    )


def test_missing_parent_generates_current_only_with_warning():
    result = GenericCitationAnchorGenerator().generate(extraction_result=_result_with_missing_parent())
    assert result.citation_anchor_count == 1
    anchor = result.citation_anchors[0]
    assert anchor.hierarchy_path == ["CLAUSE:(1)"]
    assert anchor.canonical_anchor == "CLAUSE:(1)"
    assert anchor.metadata.anchor_generation_warnings
    assert result.metadata.anchor_generation_warnings


def test_unsafe_separators_removed_from_components():
    sid = uuid4()
    candidate = LegalObjectCandidate(
        legal_object_id="lo-0000",
        source_version_id=sid,
        source_segment_id="seg-0000",
        object_type=LegalObjectType.SECTION,
        object_label="12/3 a",
        heading="12/3 a",
        raw_text="12/3 a text",
        start_offset=0,
        end_offset=11,
        sequence_number=0,
        parent_legal_object_id=None,
        hierarchy_level=0,
    )
    extraction = LegalObjectExtractionResult(
        source_version_id=sid,
        extraction_status=ExtractionStatus.SUCCESS,
        extractor_name="generic",
        extractor_version="1.0.0",
        extracted_at=utc_now(),
        legal_object_count=1,
        legal_objects=[candidate],
    )
    result = GenericCitationAnchorGenerator().generate(extraction_result=extraction)
    anchor = result.citation_anchors[0]
    assert anchor.canonical_anchor == "SECTION:123-a"
    assert "/" not in anchor.hierarchy_path[0].split(":", 1)[1]
