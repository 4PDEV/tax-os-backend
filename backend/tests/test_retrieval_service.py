from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.datetime_utils import utc_now
from app.services.retrieval import (
    LegalObjectNotFoundError,
    LegalObjectRetrievalRequest,
    LegalObjectRetrievalResult,
    LegalObjectRetrievalService,
    PROHIBITED_RETRIEVAL_CAPABILITIES,
)
from tests.retrieval_test_helpers import (
    base_request,
    make_candidate,
    persist_candidate,
    seed_source_version,
)


def test_request_model_forbids_extra_fields():
    with pytest.raises(ValidationError):
        LegalObjectRetrievalRequest(
            jurisdiction_code="RW",
            extra_field="not allowed",
        )


def test_result_model_forbids_extra_fields():
    with pytest.raises(ValidationError):
        LegalObjectRetrievalResult(
            legal_object_id="lo_test",
            source_document_id=uuid4(),
            source_version_id=uuid4(),
            object_type="section",
            object_identifier="su-0001:Section 15",
            status="active",
            effective_from=None,
            effective_to=None,
            canonical_text="text",
            integrity_hash="a" * 64,
            text_hash="b" * 64,
            retrieval_timestamp=utc_now(),
            extra_field="not allowed",
        )


def test_no_semantic_retrieval_modules_introduced():
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1] / "app" / "services" / "retrieval"
    forbidden = ("embedding", "pgvector", "semantic", "rag", "bm25", "vector")
    for path in repo_root.rglob("*.py"):
        name = path.name.lower()
        assert not any(token in name for token in forbidden)
    for capability in ("embeddings", "pgvector", "semantic_similarity", "rag"):
        assert capability in PROHIBITED_RETRIEVAL_CAPABILITIES


@pytest.mark.integration
def test_retrieve_by_id(db_session):
    _, _, document, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    service = LegalObjectRetrievalService()
    result = service.retrieve_by_id(db_session, candidate.legal_object_id)

    assert result.legal_object_id == candidate.legal_object_id
    assert result.source_document_id == document.id
    assert result.source_version_id == version.id
    assert result.canonical_text == candidate.raw_text
    assert result.text_hash == candidate.text_hash
    assert result.object_identifier == "su-0001:Section 15"


@pytest.mark.integration
def test_retrieve_by_id_not_found(db_session):
    seed_source_version(db_session)
    with pytest.raises(LegalObjectNotFoundError):
        LegalObjectRetrievalService().retrieve_by_id(db_session, "lo_nonexistent")


@pytest.mark.integration
def test_retrieve_active_only(db_session):
    _, _, _, version = seed_source_version(db_session)
    active = persist_candidate(
        db_session,
        make_candidate(
            source_version_id=str(version.id),
            object_label="Section 1",
            structural_unit_id="su-0001",
            canonical_path="PART I > Section 1",
        ),
    )
    draft = persist_candidate(
        db_session,
        make_candidate(
            source_version_id=str(version.id),
            object_label="Section 2",
            structural_unit_id="su-0002",
            canonical_path="PART I > Section 2",
        ),
    )
    from tests.retrieval_test_helpers import set_object_status

    set_object_status(db_session, draft.legal_object_id, "draft")

    results = LegalObjectRetrievalService().retrieve_active(
        db_session,
        base_request(),
    )
    ids = {row.legal_object_id for row in results}
    assert active.legal_object_id in ids
    assert draft.legal_object_id not in ids


@pytest.mark.integration
def test_deterministic_ordering(db_session):
    _, _, _, version = seed_source_version(db_session)
    second = persist_candidate(
        db_session,
        make_candidate(
            source_version_id=str(version.id),
            object_label="Section B",
            structural_unit_id="su-b",
            canonical_path="PART I > Section B",
        ),
    )
    first = persist_candidate(
        db_session,
        make_candidate(
            source_version_id=str(version.id),
            object_label="Section A",
            structural_unit_id="su-a",
            canonical_path="PART I > Section A",
        ),
    )

    results = LegalObjectRetrievalService().retrieve(db_session, base_request())
    ids = [row.legal_object_id for row in results]
    assert ids.index(first.legal_object_id) < ids.index(second.legal_object_id)


@pytest.mark.integration
def test_retrieve_preserves_traceability_fields(db_session):
    _, _, document, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    result = LegalObjectRetrievalService().retrieve(db_session, base_request())[0]

    assert result.source_document_id == document.id
    assert result.source_version_id == version.id
    assert result.integrity_hash
    assert result.text_hash
    assert result.retrieval_timestamp is not None
    assert result.legal_object_id == candidate.legal_object_id
