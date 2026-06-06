import inspect
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import IntegrityError

from app.core.datetime_utils import utc_now
from app.models.legal_object import LegalObject
from app.models.retrieval_evidence_reference import RetrievalEvidenceReference
from app.models.retrieval_request import RetrievalRequest
from app.models.retrieval_result import RetrievalResult
from app.services.citation_execution import compute_citation_hash, create_citation, render_citation
from app.services.retrieval_persistence import (
    PROHIBITED_TABLE_COLUMNS,
    RetrievalPersistenceError,
    build_hash_payload,
    canonical_json,
    compute_request_hash,
    create_evidence_reference,
    create_retrieval_request,
    create_retrieval_result,
    find_existing_default_request,
    get_request_by_hash,
    get_result,
    list_evidence_references,
    normalize_scope_envelope,
    validate_evidence_metadata,
)
from tests.test_citation_worker_skeleton import _seed_legal_object_version

pytestmark = pytest.mark.integration

RETRIEVAL_TABLES = (
    "retrieval_requests",
    "retrieval_results",
    "retrieval_evidence_references",
)


def _default_scope(**kwargs):
    base = {
        "legal_object_id": None,
        "legal_object_type": None,
        "object_identifier": None,
        "source_document_id": None,
        "source_version_id": None,
    }
    base.update(kwargs)
    return base


def _create_request(db_session, *, scope=None, force_replay=False, replay_nonce=None, **kwargs):
    defaults = {
        "retrieval_mode": "LATEST_VERSION",
        "jurisdiction_code": "RW",
        "scope_envelope": scope or _default_scope(),
        "include_canonical_text": False,
        "include_rendered_citation_text": False,
        "requested_by_actor_type": "worker",
        "force_replay": force_replay,
        "replay_nonce": replay_nonce,
    }
    defaults.update(kwargs)
    return create_retrieval_request(db_session, **defaults)


def _seed_citation(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    legal_object = db_session.get(LegalObject, version.legal_object_id)
    rendered = render_citation(
        db_session,
        legal_object=legal_object,
        legal_object_version_id=version.legal_object_version_id,
    )
    citation_hash = compute_citation_hash(
        source_version_id=rendered.source_version_id,
        legal_object_id=rendered.legal_object_id,
        legal_object_version_id=rendered.legal_object_version_id,
        location_reference=rendered.location_reference,
    )
    citation, _ = create_citation(
        db_session,
        citation_id=rendered.citation_id,
        citation_hash=rendered.citation_hash,
        legal_object_id=rendered.legal_object_id,
        legal_object_version_id=rendered.legal_object_version_id,
        source_version_id=rendered.source_version_id,
        location_reference=rendered.location_reference,
        rendered_citation_text=rendered.citation_text,
        assembled_at=rendered.assembled_at,
    )
    return version, extracted, citation


def test_request_hash_deterministic_for_equivalent_envelope():
    scope = _default_scope(legal_object_id="lo_abc")
    hash_one = compute_request_hash(
        retrieval_mode="LATEST_VERSION",
        jurisdiction_code="RW",
        scope_envelope=scope,
        include_canonical_text=False,
        include_rendered_citation_text=False,
        tax_type_code=None,
    )
    hash_two = compute_request_hash(
        retrieval_mode="LATEST_VERSION",
        jurisdiction_code="RW",
        scope_envelope={"legal_object_id": "lo_abc"},
        include_canonical_text=False,
        include_rendered_citation_text=False,
        tax_type_code=None,
    )
    assert hash_one == hash_two


def test_canonical_json_sorted_keys():
    payload = build_hash_payload(
        retrieval_mode="LATEST_VERSION",
        jurisdiction_code="RW",
        scope_envelope=_default_scope(),
        include_canonical_text=True,
        include_rendered_citation_text=False,
    )
    serialized = canonical_json(payload)
    assert serialized.index('"include_canonical_text"') < serialized.index('"jurisdiction_code"')


def test_request_hash_ignores_actor_and_notes(db_session):
    scope = _default_scope()
    first = _create_request(
        db_session,
        scope=scope,
        requested_by_actor_type="worker",
        requested_by_actor_identifier="worker-1",
        notes="audit note A",
    )
    expected = compute_request_hash(
        retrieval_mode="LATEST_VERSION",
        jurisdiction_code="RW",
        scope_envelope=scope,
        include_canonical_text=False,
        include_rendered_citation_text=False,
    )
    assert first.request_hash == expected

    with pytest.raises(RetrievalPersistenceError):
        _create_request(
            db_session,
            scope=scope,
            requested_by_actor_type="admin",
            notes="different note",
        )


def test_force_replay_hash_variation():
    scope = _default_scope()
    hash_one = compute_request_hash(
        retrieval_mode="LATEST_VERSION",
        jurisdiction_code="RW",
        scope_envelope=scope,
        include_canonical_text=False,
        include_rendered_citation_text=False,
        force_replay=True,
        replay_nonce="nonce-a",
    )
    hash_two = compute_request_hash(
        retrieval_mode="LATEST_VERSION",
        jurisdiction_code="RW",
        scope_envelope=scope,
        include_canonical_text=False,
        include_rendered_citation_text=False,
        force_replay=True,
        replay_nonce="nonce-b",
    )
    assert hash_one != hash_two


def test_force_replay_allows_multiple_requests(db_session):
    scope = _default_scope()
    first = _create_request(db_session, scope=scope, force_replay=True, replay_nonce="replay-1")
    second = _create_request(db_session, scope=scope, force_replay=True, replay_nonce="replay-2")
    assert first.request_hash != second.request_hash


def test_partial_unique_duplicate_default_rejected(db_session):
    scope = _default_scope()
    _create_request(db_session, scope=scope)
    with pytest.raises(RetrievalPersistenceError):
        _create_request(db_session, scope=scope)


def test_db_rejects_duplicate_default_request_at_constraint_level(db_session):
    scope = _default_scope()
    now = utc_now()
    request_hash = compute_request_hash(
        retrieval_mode="LATEST_VERSION",
        jurisdiction_code="RW",
        scope_envelope=scope,
        include_canonical_text=False,
        include_rendered_citation_text=False,
    )
    first = RetrievalRequest(
        request_hash=request_hash,
        retrieval_mode="LATEST_VERSION",
        jurisdiction_code="RW",
        scope_envelope=scope,
        requested_by_actor_type="worker",
        requested_at=now,
        force_replay=False,
        include_canonical_text=False,
        include_rendered_citation_text=False,
        created_at=now,
    )
    db_session.add(first)
    db_session.flush()

    second = RetrievalRequest(
        request_hash=request_hash,
        retrieval_mode="LATEST_VERSION",
        jurisdiction_code="RW",
        scope_envelope=scope,
        requested_by_actor_type="admin",
        requested_at=now,
        force_replay=False,
        include_canonical_text=False,
        include_rendered_citation_text=False,
        created_at=now,
    )
    db_session.add(second)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_find_existing_default_request_and_get_by_hash(db_session):
    scope = _default_scope()
    created = _create_request(db_session, scope=scope)
    found = find_existing_default_request(db_session, request_hash=created.request_hash)
    assert found is not None
    assert found.id == created.id
    assert get_request_by_hash(db_session, request_hash=created.request_hash).id == created.id


def test_as_of_date_included_in_hash_only_for_mode():
    scope = _default_scope()
    as_of = date(2024, 1, 15)
    with_date = compute_request_hash(
        retrieval_mode="AS_OF_DATE",
        jurisdiction_code="RW",
        scope_envelope=scope,
        include_canonical_text=False,
        include_rendered_citation_text=False,
        as_of_date=as_of,
    )
    without_date = compute_request_hash(
        retrieval_mode="LATEST_VERSION",
        jurisdiction_code="RW",
        scope_envelope=scope,
        include_canonical_text=False,
        include_rendered_citation_text=False,
        as_of_date=as_of,
    )
    assert with_date != without_date


def test_exact_version_id_included_in_hash_only_for_mode(db_session):
    version, _ = _seed_legal_object_version(db_session)
    scope = _default_scope()
    exact = compute_request_hash(
        retrieval_mode="EXACT_VERSION",
        jurisdiction_code="RW",
        scope_envelope=scope,
        include_canonical_text=False,
        include_rendered_citation_text=False,
        legal_object_version_id=version.legal_object_version_id,
    )
    latest = compute_request_hash(
        retrieval_mode="LATEST_VERSION",
        jurisdiction_code="RW",
        scope_envelope=scope,
        include_canonical_text=False,
        include_rendered_citation_text=False,
        legal_object_version_id=version.legal_object_version_id,
    )
    assert exact != latest


def test_normalize_scope_envelope_explicit_nulls():
    normalized = normalize_scope_envelope({"legal_object_id": "lo_x"})
    assert set(normalized.keys()) == {
        "legal_object_id",
        "legal_object_type",
        "object_identifier",
        "source_document_id",
        "source_version_id",
    }
    assert normalized["legal_object_type"] is None


def test_retrieval_result_lifecycle_and_zero_result_semantics(db_session):
    request = _create_request(db_session)
    pending = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="pending",
    )
    completed_empty = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="completed",
        result_count=0,
        completed_at=utc_now(),
    )
    assert pending.retrieval_status == "pending"
    assert completed_empty.result_count == 0
    assert completed_empty.error_category is None


def test_append_only_multiple_results_preserved(db_session):
    request = _create_request(db_session)
    create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="accepted",
    )
    create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="completed",
        result_count=1,
        completed_at=utc_now(),
    )
    results = db_session.query(RetrievalResult).filter_by(retrieval_request_id=request.id).all()
    assert len(results) == 2


def test_evidence_reference_with_valid_citation(db_session):
    version, extracted, citation = _seed_citation(db_session)
    request = _create_request(db_session)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="completed",
        result_count=1,
        completed_at=utc_now(),
    )
    ref = create_evidence_reference(
        db_session,
        retrieval_result_id=result.id,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        citation_id=citation.citation_id,
        citation_hash=citation.citation_hash,
        deterministic_order_index=1,
        evidence_metadata={"object_label": "Section 1"},
    )
    assert ref.citation_id == citation.citation_id
    listed = list_evidence_references(db_session, retrieval_result_id=result.id)
    assert len(listed) == 1
    assert get_result(db_session, retrieval_result_id=result.id).id == result.id


def test_citation_mismatch_raises_provenance_error(db_session):
    version, extracted, citation = _seed_citation(db_session)
    request = _create_request(db_session)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="accepted",
    )
    with pytest.raises(RetrievalPersistenceError, match="citation_hash_mismatch"):
        create_evidence_reference(
            db_session,
            retrieval_result_id=result.id,
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=extracted.source_version_id,
            citation_id=citation.citation_id,
            citation_hash="0" * 64,
            deterministic_order_index=1,
        )


def test_citation_mismatch_persisted_as_failed_result(db_session):
    version, extracted, citation = _seed_citation(db_session)
    request = _create_request(db_session)
    accepted = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="accepted",
    )
    try:
        create_evidence_reference(
            db_session,
            retrieval_result_id=accepted.id,
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=extracted.source_version_id,
            citation_id=citation.citation_id,
            citation_hash="badhash",
            deterministic_order_index=1,
        )
    except RetrievalPersistenceError:
        failed = create_retrieval_result(
            db_session,
            retrieval_request_id=request.id,
            retrieval_status="failed",
            error_category="provenance_incomplete",
            error_message="citation_hash_mismatch",
            completed_at=utc_now(),
        )
        assert failed.retrieval_status == "failed"
        assert failed.error_category == "provenance_incomplete"


def test_citation_id_hash_pairing_required(db_session):
    version, extracted, citation = _seed_citation(db_session)
    request = _create_request(db_session)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="accepted",
    )
    with pytest.raises(RetrievalPersistenceError, match="citation_id_and_hash_must_be_paired"):
        create_evidence_reference(
            db_session,
            retrieval_result_id=result.id,
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=extracted.source_version_id,
            citation_id=citation.citation_id,
            citation_hash=None,
            deterministic_order_index=1,
        )


def test_metadata_whitelist_allows_known_keys():
    validate_evidence_metadata({"structural_path": "s1", "object_label": "Article 5"})


@pytest.mark.parametrize(
    "key",
    [
        "answer_text",
        "legal_conclusion",
        "ranking_score",
        "relevance_score",
        "ai_output",
        "interpretation",
    ],
)
def test_metadata_rejects_prohibited_keys(key):
    with pytest.raises(ValueError, match="prohibited"):
        validate_evidence_metadata({key: "blocked"})


def test_metadata_rejects_unknown_keys():
    with pytest.raises(ValueError, match="unknown"):
        validate_evidence_metadata({"extra_field": "nope"})


def test_create_evidence_rejects_bad_metadata(db_session):
    version, extracted, _ = _seed_citation(db_session)
    request = _create_request(db_session)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="accepted",
    )
    with pytest.raises(RetrievalPersistenceError):
        create_evidence_reference(
            db_session,
            retrieval_result_id=result.id,
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=extracted.source_version_id,
            deterministic_order_index=1,
            evidence_metadata={"ranking_score": 0.9},
        )


def test_deterministic_order_index_uniqueness(db_session):
    version, extracted, _ = _seed_citation(db_session)
    request = _create_request(db_session)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="completed",
        result_count=2,
    )
    create_evidence_reference(
        db_session,
        retrieval_result_id=result.id,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        deterministic_order_index=1,
    )
    with pytest.raises(IntegrityError):
        create_evidence_reference(
            db_session,
            retrieval_result_id=result.id,
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=extracted.source_version_id,
            deterministic_order_index=1,
        )


def test_fk_enforcement_invalid_legal_object(db_session):
    version, extracted, _ = _seed_citation(db_session)
    request = _create_request(db_session)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="accepted",
    )
    with pytest.raises(RetrievalPersistenceError, match="legal_object_missing"):
        create_evidence_reference(
            db_session,
            retrieval_result_id=result.id,
            legal_object_id="missing_object",
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=extracted.source_version_id,
            deterministic_order_index=1,
        )


def test_enum_validation_rejects_invalid_status(db_session):
    request = _create_request(db_session)
    with pytest.raises(RetrievalPersistenceError):
        create_retrieval_result(
            db_session,
            retrieval_request_id=request.id,
            retrieval_status="ranked",
        )


def test_prohibited_columns_absent_from_schema(engine):
    inspector = sa_inspect(engine)
    for table in RETRIEVAL_TABLES:
        columns = {col["name"] for col in inspector.get_columns(table)}
        for prohibited in PROHIBITED_TABLE_COLUMNS:
            assert prohibited not in columns, f"{prohibited} must not exist on {table}"


def test_no_answer_ranking_or_ai_table_names(engine):
    tables = set(sa_inspect(engine).get_table_names())
    for table in RETRIEVAL_TABLES:
        assert table in tables
        assert "answer" not in table
        assert "ranking" not in table
        assert "semantic" not in table


def test_persistence_module_append_only_no_mutations():
    from app.services import retrieval_persistence

    source = inspect.getsource(retrieval_persistence.persistence)
    assert "def update_" not in source
    assert "def delete_" not in source
    assert ".delete(" not in source


def test_no_retrieval_execution_in_persistence_package():
    pkg_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "retrieval_persistence"
    forbidden = (
        "LegalObjectRetrievalService",
        "app.services.retrieval.legal_object",
        "semantic_search",
    )
    for filename in ("hashing.py", "persistence.py"):
        source = (pkg_dir / filename).read_text().lower()
        for token in forbidden:
            assert token.lower() not in source, f"{token} must not appear in {filename}"


def test_evidence_without_citation_allowed(db_session):
    version, extracted, _ = _seed_citation(db_session)
    request = _create_request(db_session)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="completed",
        result_count=1,
    )
    ref = create_evidence_reference(
        db_session,
        retrieval_result_id=result.id,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        deterministic_order_index=1,
    )
    assert ref.citation_id is None
    assert ref.citation_hash is None
