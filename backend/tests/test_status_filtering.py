import pytest

from app.services.retrieval import LegalObjectRetrievalService
from tests.retrieval_test_helpers import (
    base_request,
    make_candidate,
    persist_candidate,
    seed_source_version,
    set_object_status,
)


@pytest.mark.integration
def test_archived_excluded_by_default(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_object_status(db_session, candidate.legal_object_id, "archived")

    results = LegalObjectRetrievalService().retrieve(db_session, base_request())
    assert not any(row.legal_object_id == candidate.legal_object_id for row in results)


@pytest.mark.integration
def test_archived_included_when_requested(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_object_status(db_session, candidate.legal_object_id, "archived")

    results = LegalObjectRetrievalService().retrieve(
        db_session,
        base_request(include_archived=True),
    )
    assert any(row.legal_object_id == candidate.legal_object_id for row in results)


@pytest.mark.integration
def test_superseded_excluded_by_default(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_object_status(db_session, candidate.legal_object_id, "superseded")

    results = LegalObjectRetrievalService().retrieve(db_session, base_request())
    assert not any(row.legal_object_id == candidate.legal_object_id for row in results)


@pytest.mark.integration
def test_superseded_included_when_requested(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_object_status(db_session, candidate.legal_object_id, "superseded")

    results = LegalObjectRetrievalService().retrieve(
        db_session,
        base_request(include_superseded=True),
    )
    assert any(row.legal_object_id == candidate.legal_object_id for row in results)


@pytest.mark.integration
def test_rejected_always_excluded(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_object_status(db_session, candidate.legal_object_id, "rejected")

    results = LegalObjectRetrievalService().retrieve(
        db_session,
        base_request(include_archived=True, include_superseded=True),
    )
    assert not any(row.legal_object_id == candidate.legal_object_id for row in results)
