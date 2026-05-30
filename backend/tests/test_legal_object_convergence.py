from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.datetime_utils import utc_now
from app.services.legal_object_convergence import (
    ConvergenceSource,
    ConvergenceStatus,
    LegalObjectCandidateMapper,
    LegalObjectCandidateValidator,
)
from app.services.legal_object_extraction.enums import LegalObjectExtractionStatus, LegalObjectType
from app.services.legal_object_extraction.identity import generate_legal_object_id, sha256_text
from app.services.legal_object_extraction.models import LegalObjectCandidate
from app.services.legal_objects.enums import LegalObjectType as LegacyLegalObjectType
from app.services.legal_objects.models import LegalObjectCandidate as LegacyLegalObjectCandidate
from app.services.legal_objects.models import LegalObjectMetadata


def _canonical_candidate(
    *,
    source_version_id: str | None = None,
    object_label: str = "Section 15",
    canonical_path: str = "PART I > Section 15",
    raw_text: str = "Tax is due.",
    parent_legal_object_id: str | None = None,
    extraction_status: LegalObjectExtractionStatus = LegalObjectExtractionStatus.SUCCESS,
    text_hash: str | None = None,
    legal_object_id: str | None = None,
    metadata: dict | None = None,
) -> LegalObjectCandidate:
    sid = source_version_id or str(uuid4())
    th = text_hash if text_hash is not None else sha256_text(raw_text)
    lid = legal_object_id or generate_legal_object_id(
        source_version_id=sid,
        canonical_path=canonical_path,
        object_type=LegalObjectType.SECTION.value,
        object_label=object_label,
        start_offset=10,
        text_hash=th,
    )
    return LegalObjectCandidate(
        source_version_id=sid,
        legal_object_id=lid,
        object_type=LegalObjectType.SECTION,
        object_label=object_label,
        object_title=None,
        canonical_path=canonical_path,
        parent_legal_object_id=parent_legal_object_id,
        structural_unit_id="su-0001",
        start_offset=10,
        end_offset=20,
        raw_text=raw_text,
        text_hash=th,
        extraction_status=extraction_status,
        extracted_at=utc_now(),
        extractor_version="1.0.0",
        metadata=metadata or {},
    )


def _legacy_segment_candidate(
    *,
    source_version_id=None,
    object_label: str = "Section 15",
    parent_legal_object_id: str | None = None,
    raw_text: str = "Tax is due.",
) -> LegacyLegalObjectCandidate:
    sid = source_version_id or uuid4()
    return LegacyLegalObjectCandidate(
        legal_object_id="lo-0001",
        source_version_id=sid,
        source_segment_id="seg-0001",
        object_type=LegacyLegalObjectType.SECTION,
        object_label=object_label,
        heading=object_label,
        raw_text=raw_text,
        start_offset=10,
        end_offset=20,
        sequence_number=1,
        parent_legal_object_id=parent_legal_object_id,
        hierarchy_level=1,
        metadata=LegalObjectMetadata(mapped_from_segment_type="section"),
    )


def test_structural_candidate_passes_as_canonical():
    mapper = LegalObjectCandidateMapper()
    candidate = _canonical_candidate()
    result = mapper.from_structural_candidate(candidate)

    assert result.convergence_status == ConvergenceStatus.CANONICAL
    assert result.source_pipeline == ConvergenceSource.STRUCTURAL_UNIT
    assert result.candidate == candidate
    assert not result.warnings


def test_segment_candidate_maps_to_canonical():
    mapper = LegalObjectCandidateMapper()
    legacy = _legacy_segment_candidate()
    result = mapper.from_segment_candidate(legacy)

    assert result.convergence_status == ConvergenceStatus.MAPPED
    assert result.source_pipeline == ConvergenceSource.SEGMENT
    assert result.candidate.object_type == LegalObjectType.SECTION
    assert result.candidate.raw_text == legacy.raw_text
    assert result.candidate.structural_unit_id == legacy.source_segment_id
    assert result.candidate.legal_object_id.startswith("lo_")
    assert result.candidate.legal_object_id != legacy.legal_object_id


def test_segment_candidate_with_parent_is_partial():
    mapper = LegalObjectCandidateMapper()
    legacy = _legacy_segment_candidate(parent_legal_object_id="lo-0000")
    result = mapper.from_segment_candidate(legacy)

    assert result.convergence_status == ConvergenceStatus.PARTIAL
    assert result.candidate.parent_legal_object_id is None
    assert any("parent" in w.lower() for w in result.warnings)


def test_invalid_text_hash_is_rejected():
    mapper = LegalObjectCandidateMapper()
    candidate = _canonical_candidate(text_hash="deadbeef")
    result = mapper.from_structural_candidate(candidate)

    assert result.convergence_status == ConvergenceStatus.REJECTED
    assert any("text_hash" in w for w in result.warnings)


def test_missing_required_fields_rejected_for_unsupported_type():
    mapper = LegalObjectCandidateMapper()
    result = mapper.from_segment_candidate({"not": "a candidate"})

    assert result.convergence_status == ConvergenceStatus.REJECTED
    assert result.source_pipeline == ConvergenceSource.UNKNOWN
    assert "unsupported candidate type" in result.warnings[0]


def test_segment_missing_label_is_rejected():
    mapper = LegalObjectCandidateMapper()
    legacy = _legacy_segment_candidate(object_label="")
    legacy = legacy.model_copy(update={"object_label": None, "heading": None})
    result = mapper.from_segment_candidate(legacy)

    assert result.convergence_status == ConvergenceStatus.REJECTED
    assert "missing object_label" in result.warnings[0]


def test_canonical_identity_generator_is_used():
    mapper = LegalObjectCandidateMapper()
    legacy = _legacy_segment_candidate()
    result = mapper.from_segment_candidate(legacy)

    expected = generate_legal_object_id(
        source_version_id=str(legacy.source_version_id),
        canonical_path=legacy.object_label,
        object_type=LegalObjectType.SECTION.value,
        object_label=legacy.object_label,
        start_offset=legacy.start_offset,
        text_hash=sha256_text(legacy.raw_text),
    )
    assert result.candidate.legal_object_id == expected


def test_warnings_are_preserved():
    mapper = LegalObjectCandidateMapper()
    legacy = _legacy_segment_candidate()
    legacy = legacy.model_copy(
        update={"object_type": LegacyLegalObjectType.ORDER}
    )
    result = mapper.from_segment_candidate(legacy)

    assert result.convergence_status in (ConvergenceStatus.MAPPED, ConvergenceStatus.PARTIAL)
    assert any("order" in w.lower() for w in result.warnings)
    assert result.candidate.object_type == LegalObjectType.UNKNOWN


def test_no_persistence_module_exists():
    import app.services.legal_object_convergence as convergence

    assert not hasattr(convergence, "repository")
    assert "LegalObjectCandidateMapper" in dir(convergence)


def test_deterministic_repeated_convergence():
    mapper = LegalObjectCandidateMapper()
    legacy = _legacy_segment_candidate()
    first = mapper.from_segment_candidate(legacy)
    second = mapper.from_segment_candidate(legacy)

    assert first.candidate.legal_object_id == second.candidate.legal_object_id
    assert first.candidate.canonical_path == second.candidate.canonical_path
    assert first.convergence_status == second.convergence_status


def test_validator_rejects_invalid_identity():
    validator = LegalObjectCandidateValidator()
    candidate = _canonical_candidate(legal_object_id="lo_wrong")
    result = validator.validate(candidate)

    assert not result.valid
    assert any("legal_object_id" in e for e in result.errors)


def test_validator_detects_duplicate_ids():
    validator = LegalObjectCandidateValidator()
    candidate = _canonical_candidate()
    warnings = validator.check_duplicate_ids([candidate, candidate])

    assert len(warnings) == 1
    assert "duplicate" in warnings[0]


def test_converged_model_forbids_extra_fields():
    candidate = _canonical_candidate()
    with pytest.raises(ValidationError):
        from app.services.legal_object_convergence.models import ConvergedLegalObjectCandidate

        ConvergedLegalObjectCandidate(
            candidate=candidate,
            source_pipeline=ConvergenceSource.STRUCTURAL_UNIT,
            convergence_status=ConvergenceStatus.CANONICAL,
            extra_field="not allowed",
        )


def test_structural_partial_status_preserved():
    mapper = LegalObjectCandidateMapper()
    candidate = _canonical_candidate(
        extraction_status=LegalObjectExtractionStatus.PARTIAL,
        metadata={"extraction_warning": "parent missing"},
    )
    result = mapper.from_structural_candidate(candidate)

    assert result.convergence_status == ConvergenceStatus.PARTIAL
