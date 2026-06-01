from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.datetime_utils import utc_now
from app.models.legal_object_version import LegalObjectVersion
from app.services.citation_candidate import (
    CandidateStatus,
    CitationCandidate,
    CitationCandidateBuilder,
    CitationCandidateRequest,
)
from app.services.effective_date import EffectiveDateResolver
from app.services.retrieval import LegalObjectRetrievalService
from tests.retrieval_test_helpers import (
    add_version_row,
    make_candidate,
    persist_candidate,
    seed_source_version,
    set_version_effective_dates,
)


def candidate_request(**overrides) -> CitationCandidateRequest:
    defaults = {
        "jurisdiction_code": "RW",
        "tax_type_code": "VAT",
        "limit": 100,
        "offset": 0,
    }
    defaults.update(overrides)
    return CitationCandidateRequest(**defaults)


def test_request_model_forbids_extra_fields():
    with pytest.raises(ValidationError):
        CitationCandidateRequest(
            jurisdiction_code="RW",
            extra_field="not allowed",
        )


def test_no_persistence_module_introduced():
    from pathlib import Path

    models_dir = Path(__file__).resolve().parents[1] / "app" / "models"
    assert not any("citation_candidate" in path.name for path in models_dir.glob("*.py"))


@pytest.mark.integration
def test_candidate_from_retrieval_result(db_session):
    _, _, document, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_version_effective_dates(
        db_session,
        candidate.legal_object_id,
        effective_from=date(2024, 1, 1),
        effective_to=date(2024, 12, 31),
    )

    results = CitationCandidateBuilder().build(db_session, candidate_request())
    match = next(c for c in results if c.legal_object_id == candidate.legal_object_id)

    assert match.candidate_status == CandidateStatus.READY
    assert match.source_document_id == document.id
    assert match.source_version_id == version.id
    assert match.source_title == "VAT Law"
    assert match.source_type == "law"
    assert match.authority_level == "national"
    assert match.jurisdiction_code == "RW"
    assert match.tax_type_code == "VAT"
    assert match.text_hash
    assert match.integrity_hash
    assert match.canonical_text


@pytest.mark.integration
def test_candidate_from_applicable_resolution(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_version_effective_dates(
        db_session,
        candidate.legal_object_id,
        effective_from=date(2024, 1, 1),
        effective_to=date(2024, 12, 31),
    )

    results = CitationCandidateBuilder().build(
        db_session,
        candidate_request(effective_on=date(2024, 6, 1)),
    )
    match = next(c for c in results if c.legal_object_id == candidate.legal_object_id)
    assert match.candidate_status == CandidateStatus.READY


@pytest.mark.integration
def test_date_ambiguous_maps_to_date_ambiguous(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_version_effective_dates(
        db_session,
        candidate.legal_object_id,
        effective_from=date(2024, 1, 1),
        effective_to=date(2024, 12, 31),
    )
    add_version_row(
        db_session,
        legal_object_id=candidate.legal_object_id,
        source_version_id=version.id,
        raw_text="Overlapping version text.",
        object_label="Section 15",
        structural_unit_id="su-0001",
        effective_from=date(2024, 3, 1),
        effective_to=date(2024, 9, 30),
    )

    results = CitationCandidateBuilder().build(
        db_session,
        candidate_request(
            effective_on=date(2024, 6, 1),
            legal_object_id=candidate.legal_object_id,
        ),
    )
    assert len(results) == 1
    assert results[0].candidate_status == CandidateStatus.DATE_AMBIGUOUS


@pytest.mark.integration
def test_not_applicable_maps_to_date_not_applicable(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_version_effective_dates(
        db_session,
        candidate.legal_object_id,
        effective_from=date(2024, 1, 1),
        effective_to=date(2024, 3, 31),
    )

    results = CitationCandidateBuilder().build(
        db_session,
        candidate_request(
            effective_on=date(2024, 6, 1),
            legal_object_id=candidate.legal_object_id,
        ),
    )
    assert results[0].candidate_status == CandidateStatus.DATE_NOT_APPLICABLE


@pytest.mark.integration
def test_missing_effective_date_maps_correctly(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )

    results = CitationCandidateBuilder().build(
        db_session,
        candidate_request(
            effective_on=date(2024, 6, 1),
            legal_object_id=candidate.legal_object_id,
        ),
    )
    assert results[0].candidate_status == CandidateStatus.MISSING_EFFECTIVE_DATE


@pytest.mark.integration
def test_integrity_failure_maps_correctly(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    stored = set_version_effective_dates(
        db_session,
        candidate.legal_object_id,
        effective_from=date(2024, 1, 1),
        effective_to=date(2024, 12, 31),
    )
    stored.text_hash = "0" * 64
    db_session.flush()

    results = CitationCandidateBuilder().build(
        db_session,
        candidate_request(
            effective_on=date(2024, 6, 1),
            legal_object_id=candidate.legal_object_id,
        ),
    )
    assert results[0].candidate_status == CandidateStatus.INTEGRITY_FAILED


@pytest.mark.integration
def test_source_traceability_failure(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )

    retrieval = LegalObjectRetrievalService().retrieve_by_id(
        db_session,
        candidate.legal_object_id,
    )
    result = CitationCandidateBuilder().build_from_retrieval_result(
        db_session,
        candidate_request(jurisdiction_code="KE"),
        retrieval,
    )
    assert result.candidate_status == CandidateStatus.SOURCE_TRACEABILITY_FAILED


@pytest.mark.integration
def test_build_from_resolution_result_directly(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_version_effective_dates(
        db_session,
        candidate.legal_object_id,
        effective_from=date(2024, 1, 1),
        effective_to=date(2024, 12, 31),
    )

    resolution = EffectiveDateResolver().resolve_by_legal_object_id(
        db_session,
        candidate.legal_object_id,
        date(2024, 6, 1),
        jurisdiction_code="RW",
        tax_type_code="VAT",
    )
    built = CitationCandidateBuilder().build_from_resolution_result(
        db_session,
        candidate_request(effective_on=date(2024, 6, 1)),
        resolution,
    )
    assert built.candidate_status == CandidateStatus.READY
    assert built.object_label == "Section 15"


@pytest.mark.integration
def test_no_database_persistence_performed(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    version_count_before = db_session.query(LegalObjectVersion).count()
    CitationCandidateBuilder().build(db_session, candidate_request())
    assert db_session.query(LegalObjectVersion).count() == version_count_before

    metadata = db_session.bind.dialect.get_table_names  # type: ignore[union-attr]
    table_names = metadata(db_session.connection())
    assert "citation_candidates" not in table_names
