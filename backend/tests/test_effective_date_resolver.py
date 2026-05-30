from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.services.effective_date import (
    EffectiveDateResolutionRequest,
    EffectiveDateResolutionResult,
    EffectiveDateResolver,
    LegalObjectResolutionNotFoundError,
    ResolutionStatus,
)
from tests.retrieval_test_helpers import (
    add_version_row,
    make_candidate,
    persist_candidate,
    seed_source_version,
    set_object_status,
    set_version_effective_dates,
)


def resolution_request(**overrides) -> EffectiveDateResolutionRequest:
    defaults = {
        "jurisdiction_code": "RW",
        "tax_type_code": "VAT",
        "effective_on": date(2024, 6, 1),
        "limit": 100,
        "offset": 0,
    }
    defaults.update(overrides)
    return EffectiveDateResolutionRequest(**defaults)


def test_request_model_forbids_extra_fields():
    with pytest.raises(ValidationError):
        EffectiveDateResolutionRequest(
            jurisdiction_code="RW",
            effective_on=date(2024, 1, 1),
            extra_field="not allowed",
        )


def test_no_ai_or_semantic_modules_in_effective_date_package():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "app" / "services" / "effective_date"
    forbidden = ("embedding", "pgvector", "semantic", "rag", "openai")
    for path in root.rglob("*.py"):
        assert not any(token in path.name.lower() for token in forbidden)


@pytest.mark.integration
def test_single_applicable_version(db_session):
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

    results = EffectiveDateResolver().resolve(
        db_session,
        resolution_request(effective_on=date(2024, 6, 1)),
    )
    match = next(r for r in results if r.legal_object_id == candidate.legal_object_id)
    assert match.resolution_status == ResolutionStatus.APPLICABLE


@pytest.mark.integration
def test_no_applicable_version(db_session):
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

    results = EffectiveDateResolver().resolve(
        db_session,
        resolution_request(effective_on=date(2024, 6, 1)),
    )
    match = next(r for r in results if r.legal_object_id == candidate.legal_object_id)
    assert match.resolution_status == ResolutionStatus.NOT_APPLICABLE


@pytest.mark.integration
def test_open_ended_effective_to(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_version_effective_dates(
        db_session,
        candidate.legal_object_id,
        effective_from=date(2024, 1, 1),
        effective_to=None,
    )

    result = EffectiveDateResolver().resolve_by_legal_object_id(
        db_session,
        candidate.legal_object_id,
        date(2030, 1, 1),
        jurisdiction_code="RW",
        tax_type_code="VAT",
    )
    assert result.resolution_status == ResolutionStatus.APPLICABLE


@pytest.mark.integration
def test_null_effective_from_unbounded_past(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_version_effective_dates(
        db_session,
        candidate.legal_object_id,
        effective_from=None,
        effective_to=date(2024, 12, 31),
    )

    result = EffectiveDateResolver().resolve_by_legal_object_id(
        db_session,
        candidate.legal_object_id,
        date(2024, 6, 1),
        jurisdiction_code="RW",
        tax_type_code="VAT",
    )
    assert result.resolution_status == ResolutionStatus.APPLICABLE


@pytest.mark.integration
def test_ambiguous_overlapping_versions(db_session):
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

    result = EffectiveDateResolver().resolve_by_legal_object_id(
        db_session,
        candidate.legal_object_id,
        date(2024, 6, 1),
        jurisdiction_code="RW",
        tax_type_code="VAT",
    )
    assert result.resolution_status == ResolutionStatus.AMBIGUOUS_OVERLAP


@pytest.mark.integration
def test_missing_effective_dates(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )

    result = EffectiveDateResolver().resolve_by_legal_object_id(
        db_session,
        candidate.legal_object_id,
        date(2024, 6, 1),
        jurisdiction_code="RW",
        tax_type_code="VAT",
    )
    assert result.resolution_status == ResolutionStatus.MISSING_EFFECTIVE_DATE


@pytest.mark.integration
def test_integrity_failure(db_session):
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

    result = EffectiveDateResolver().resolve_by_legal_object_id(
        db_session,
        candidate.legal_object_id,
        date(2024, 6, 1),
        jurisdiction_code="RW",
        tax_type_code="VAT",
    )
    assert result.resolution_status == ResolutionStatus.INTEGRITY_FAILED


@pytest.mark.integration
def test_superseded_excluded_by_default(db_session):
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
    set_object_status(db_session, candidate.legal_object_id, "superseded")

    results = EffectiveDateResolver().resolve(
        db_session,
        resolution_request(effective_on=date(2024, 6, 1)),
    )
    assert not any(r.legal_object_id == candidate.legal_object_id for r in results)


@pytest.mark.integration
def test_archived_excluded_by_default(db_session):
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
    set_object_status(db_session, candidate.legal_object_id, "archived")

    results = EffectiveDateResolver().resolve(
        db_session,
        resolution_request(effective_on=date(2024, 6, 1)),
    )
    assert not any(r.legal_object_id == candidate.legal_object_id for r in results)


@pytest.mark.integration
def test_deterministic_ordering(db_session):
    _, _, _, version = seed_source_version(db_session)
    first = persist_candidate(
        db_session,
        make_candidate(
            source_version_id=str(version.id),
            object_label="Section A",
            structural_unit_id="su-a",
            canonical_path="PART I > Section A",
        ),
    )
    second = persist_candidate(
        db_session,
        make_candidate(
            source_version_id=str(version.id),
            object_label="Section B",
            structural_unit_id="su-b",
            canonical_path="PART I > Section B",
        ),
    )
    set_version_effective_dates(
        db_session,
        first.legal_object_id,
        effective_from=date(2024, 2, 1),
        effective_to=date(2024, 12, 31),
    )
    set_version_effective_dates(
        db_session,
        second.legal_object_id,
        effective_from=date(2024, 1, 1),
        effective_to=date(2024, 12, 31),
    )

    results = EffectiveDateResolver().resolve(
        db_session,
        resolution_request(effective_on=date(2024, 6, 1)),
    )
    applicable = [
        r
        for r in results
        if r.resolution_status == ResolutionStatus.APPLICABLE
    ]
    ids = [r.legal_object_id for r in applicable]
    assert ids.index(second.legal_object_id) < ids.index(first.legal_object_id)


@pytest.mark.integration
def test_resolve_by_id_not_found(db_session):
    seed_source_version(db_session)
    with pytest.raises(LegalObjectResolutionNotFoundError):
        EffectiveDateResolver().resolve_by_legal_object_id(
            db_session,
            "lo_missing",
            date(2024, 6, 1),
            jurisdiction_code="RW",
        )
