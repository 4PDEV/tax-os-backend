from datetime import date

import pytest

from app.services.retrieval import InvalidEffectiveDateError, LegalObjectRetrievalService
from app.services.retrieval.filters import python_version_effective_on
from tests.retrieval_test_helpers import (
    base_request,
    make_candidate,
    persist_candidate,
    seed_source_version,
    set_version_effective_dates,
)


def test_python_effective_date_filter_boundaries():
    assert python_version_effective_on(
        effective_from=date(2024, 1, 1),
        effective_to=date(2024, 12, 31),
        effective_on=date(2024, 6, 1),
    )
    assert not python_version_effective_on(
        effective_from=date(2024, 1, 1),
        effective_to=date(2024, 3, 31),
        effective_on=date(2024, 6, 1),
    )
    assert python_version_effective_on(
        effective_from=None,
        effective_to=None,
        effective_on=date(2024, 6, 1),
    )


def test_retrieve_effective_requires_effective_on():
    with pytest.raises(InvalidEffectiveDateError):
        LegalObjectRetrievalService().retrieve_effective(None, None, base_request())  # type: ignore[arg-type]


@pytest.mark.integration
def test_retrieve_effective_on_date(db_session):
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

    service = LegalObjectRetrievalService()
    inside = service.retrieve_effective(
        db_session,
        date(2024, 6, 15),
        base_request(),
    )
    assert any(row.legal_object_id == candidate.legal_object_id for row in inside)

    outside = service.retrieve_effective(
        db_session,
        date(2025, 1, 1),
        base_request(),
    )
    assert not any(row.legal_object_id == candidate.legal_object_id for row in outside)


@pytest.mark.integration
def test_null_effective_dates_treated_as_unbounded(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )

    results = LegalObjectRetrievalService().retrieve_effective(
        db_session,
        date(2030, 1, 1),
        base_request(),
    )
    assert any(row.legal_object_id == candidate.legal_object_id for row in results)


@pytest.mark.integration
def test_retrieve_with_effective_on_in_request(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_version_effective_dates(
        db_session,
        candidate.legal_object_id,
        effective_from=date(2023, 1, 1),
        effective_to=date(2023, 12, 31),
    )

    results = LegalObjectRetrievalService().retrieve(
        db_session,
        base_request(effective_on=date(2023, 6, 1)),
    )
    assert len(results) == 1
    assert results[0].legal_object_id == candidate.legal_object_id
