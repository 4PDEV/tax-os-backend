from uuid import uuid4

from app.services.cross_reference import CrossReferenceDetector
from app.services.cross_reference.enums import ReferenceConfidence, ReferenceType


def _detect(text: str, source_version_id=None):
    sid = source_version_id or uuid4()
    return CrossReferenceDetector().detect(source_version_id=sid, text=text)


def test_section_detection_with_target_candidate():
    text = "See Section 42 of the VAT Act."
    results = _detect(text)
    assert len(results) == 1
    ref = results[0]
    assert ref.reference_type is ReferenceType.SECTION
    assert ref.reference_text == "Section 42"
    assert ref.target_candidate == "VAT Act"
    assert ref.confidence is ReferenceConfidence.HIGH


def test_article_detection():
    text = "As set out in Article 8 below."
    results = _detect(text)
    assert len(results) == 1
    assert results[0].reference_type is ReferenceType.ARTICLE
    assert results[0].reference_text == "Article 8"
    assert results[0].confidence is ReferenceConfidence.HIGH


def test_regulation_detection():
    text = "Pursuant to Regulation 5."
    results = _detect(text)
    assert len(results) == 1
    assert results[0].reference_type is ReferenceType.REGULATION
    assert results[0].reference_text == "Regulation 5"
    assert results[0].confidence is ReferenceConfidence.HIGH


def test_schedule_detection():
    text = "Listed in Schedule 3."
    results = _detect(text)
    assert len(results) == 1
    assert results[0].reference_type is ReferenceType.SCHEDULE
    assert results[0].reference_text == "Schedule 3"
    assert results[0].confidence is ReferenceConfidence.HIGH


def test_multiple_references_detected_in_order():
    text = "Section 15 refers to Section 12 and Article 8."
    sid = uuid4()
    results = CrossReferenceDetector().detect(source_version_id=sid, text=text)
    assert len(results) == 3
    assert [r.reference_text for r in results] == ["Section 15", "Section 12", "Article 8"]
    assert all(r.source_version_id == sid for r in results)


def test_section_range_medium_confidence():
    text = "Applies to Sections 12-15 inclusive."
    results = _detect(text)
    assert len(results) == 1
    assert results[0].reference_type is ReferenceType.SECTION
    assert results[0].reference_text == "Sections 12-15"
    assert results[0].confidence is ReferenceConfidence.MEDIUM


def test_low_confidence_vague_reference():
    text = "Subject to the above provision."
    results = _detect(text)
    assert len(results) == 1
    assert results[0].reference_type is ReferenceType.UNKNOWN
    assert results[0].reference_text.lower() == "the above provision"
    assert results[0].confidence is ReferenceConfidence.LOW
    assert results[0].target_candidate is None


def test_empty_text_returns_no_matches():
    sid = uuid4()
    results = CrossReferenceDetector().detect(source_version_id=sid, text="")
    assert results == []


def test_no_match_text_returns_empty_list():
    text = "This paragraph contains no structural references."
    results = _detect(text)
    assert results == []


def test_source_location_and_detector_version_populated():
    text = "Section 1 applies."
    results = _detect(text)
    assert len(results) == 1
    assert results[0].source_location == "0:9"
    assert results[0].detector_version == "1.0.0"
    assert results[0].detected_at is not None


def test_detection_is_deterministic_across_runs():
    text = "Section 42 of the VAT Act and Article 5."
    sid = uuid4()
    first = CrossReferenceDetector().detect(source_version_id=sid, text=text)
    second = CrossReferenceDetector().detect(source_version_id=sid, text=text)
    assert [r.model_dump(exclude={"detected_at"}) for r in first] == [
        r.model_dump(exclude={"detected_at"}) for r in second
    ]
