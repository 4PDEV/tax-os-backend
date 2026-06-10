import inspect
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import IntegrityError

from app.core.datetime_utils import utc_now
from app.models.ranked_evidence_reference import RankedEvidenceReference
from app.models.ranking_result import RankingResult
from app.services.ranking_persistence import (
    CURRENT_CONTRACT_VERSION,
    PROHIBITED_ERROR_CATEGORIES,
    PROHIBITED_TABLE_COLUMNS,
    RANKED_EVIDENCE_ALLOWED_COLUMNS,
    RankingPersistenceError,
    build_hash_payload,
    canonical_json,
    compute_ranking_request_hash,
    create_ranked_evidence_reference,
    create_ranking_request,
    create_ranking_result,
    list_ranked_evidence_references,
    validate_ranking_error_category,
)
from app.services.retrieval_persistence import (
    create_evidence_reference,
    create_retrieval_request,
    create_retrieval_result,
)
from tests.test_retrieval_persistence import _create_request, _default_scope, _seed_citation

pytestmark = pytest.mark.integration

RANKING_TABLES = (
    "ranking_requests",
    "ranking_results",
    "ranked_evidence_references",
)


def _seed_completed_retrieval(db_session, *, result_count=1, with_evidence=True):
    request = _create_request(db_session)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="completed",
        result_count=result_count,
        completed_at=utc_now(),
    )
    evidence = None
    if with_evidence and result_count > 0:
        version, extracted, citation = _seed_citation(db_session)
        evidence = create_evidence_reference(
            db_session,
            retrieval_result_id=result.id,
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=extracted.source_version_id,
            citation_id=citation.citation_id,
            citation_hash=citation.citation_hash,
            deterministic_order_index=1,
        )
    return request, result, evidence


def _create_ranking_request(db_session, retrieval_result_id, **kwargs):
    defaults = {
        "ranking_profile": "CANONICAL",
        "requested_by_actor_type": "worker",
    }
    defaults.update(kwargs)
    return create_ranking_request(
        db_session,
        retrieval_result_id=retrieval_result_id,
        **defaults,
    )


def test_ranking_request_hash_deterministic():
    retrieval_result_id = uuid4()
    hash_one = compute_ranking_request_hash(
        retrieval_result_id=retrieval_result_id,
        ranking_profile="CANONICAL",
        contract_version=CURRENT_CONTRACT_VERSION,
    )
    hash_two = compute_ranking_request_hash(
        retrieval_result_id=retrieval_result_id,
        ranking_profile="CANONICAL",
        contract_version="008B-v2",
    )
    assert hash_one == hash_two


def test_ranking_request_hash_ignores_actor_and_notes(db_session):
    _, retrieval_result, _ = _seed_completed_retrieval(db_session, result_count=0, with_evidence=False)
    first = _create_ranking_request(
        db_session,
        retrieval_result.id,
        requested_by_actor_identifier="worker-1",
        notes="audit note",
    )
    expected = compute_ranking_request_hash(
        retrieval_result_id=retrieval_result.id,
        ranking_profile="CANONICAL",
    )
    assert first.ranking_request_hash == expected


def test_canonical_json_sorted_keys():
    payload = build_hash_payload(
        retrieval_result_id=uuid4(),
        ranking_profile="CANONICAL",
    )
    serialized = canonical_json(payload)
    assert serialized.index('"contract_version"') < serialized.index('"ranking_profile"')


def test_zero_result_completed_ranking_without_rows(db_session):
    _, retrieval_result, _ = _seed_completed_retrieval(db_session, result_count=0, with_evidence=False)
    ranking_request = _create_ranking_request(db_session, retrieval_result.id)
    ranking_result = create_ranking_result(
        db_session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=retrieval_result.id,
        ranking_status="completed",
        rank_count=0,
        completed_at=utc_now(),
    )
    assert ranking_result.ranking_status == "completed"
    assert ranking_result.rank_count == 0
    assert ranking_result.error_category is None
    assert list_ranked_evidence_references(db_session, ranking_result_id=ranking_result.id) == []


def test_pure_pointer_ranked_row_persists(db_session):
    _, retrieval_result, evidence = _seed_completed_retrieval(db_session)
    ranking_request = _create_ranking_request(db_session, retrieval_result.id)
    ranking_result = create_ranking_result(
        db_session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=retrieval_result.id,
        ranking_status="completed",
        rank_count=1,
        completed_at=utc_now(),
    )
    ranked = create_ranked_evidence_reference(
        db_session,
        ranking_result_id=ranking_result.id,
        retrieval_result_id=retrieval_result.id,
        retrieval_evidence_reference_id=evidence.id,
        presentation_order_index=1,
    )
    assert ranked.ranking_result_id == ranking_result.id
    assert ranked.retrieval_result_id == retrieval_result.id
    assert ranked.retrieval_evidence_reference_id == evidence.id
    assert ranked.presentation_order_index == 1


def test_duplicate_presentation_order_index_rejected(db_session):
    _, retrieval_result, evidence = _seed_completed_retrieval(db_session)
    ranking_request = _create_ranking_request(db_session, retrieval_result.id)
    ranking_result = create_ranking_result(
        db_session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=retrieval_result.id,
        ranking_status="completed",
        rank_count=2,
        completed_at=utc_now(),
    )
    create_ranked_evidence_reference(
        db_session,
        ranking_result_id=ranking_result.id,
        retrieval_result_id=retrieval_result.id,
        retrieval_evidence_reference_id=evidence.id,
        presentation_order_index=1,
    )
    with pytest.raises(IntegrityError):
        create_ranked_evidence_reference(
            db_session,
            ranking_result_id=ranking_result.id,
            retrieval_result_id=retrieval_result.id,
            retrieval_evidence_reference_id=evidence.id,
            presentation_order_index=1,
        )


def test_duplicate_evidence_reference_rejected(db_session):
    _, retrieval_result, evidence = _seed_completed_retrieval(db_session)
    ranking_request = _create_ranking_request(db_session, retrieval_result.id)
    ranking_result = create_ranking_result(
        db_session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=retrieval_result.id,
        ranking_status="completed",
        rank_count=2,
        completed_at=utc_now(),
    )
    create_ranked_evidence_reference(
        db_session,
        ranking_result_id=ranking_result.id,
        retrieval_result_id=retrieval_result.id,
        retrieval_evidence_reference_id=evidence.id,
        presentation_order_index=1,
    )
    with pytest.raises(IntegrityError):
        create_ranked_evidence_reference(
            db_session,
            ranking_result_id=ranking_result.id,
            retrieval_result_id=retrieval_result.id,
            retrieval_evidence_reference_id=evidence.id,
            presentation_order_index=2,
        )


def test_composite_membership_rejects_cross_result_evidence(db_session):
    _, retrieval_result_a, evidence_a = _seed_completed_retrieval(db_session)
    _, retrieval_result_b, _ = _seed_completed_retrieval(db_session)
    ranking_request = _create_ranking_request(db_session, retrieval_result_b.id)
    ranking_result = create_ranking_result(
        db_session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=retrieval_result_b.id,
        ranking_status="completed",
        rank_count=1,
        completed_at=utc_now(),
    )
    with pytest.raises(RankingPersistenceError, match="evidence_reference_retrieval_result_mismatch"):
        create_ranked_evidence_reference(
            db_session,
            ranking_result_id=ranking_result.id,
            retrieval_result_id=retrieval_result_b.id,
            retrieval_evidence_reference_id=evidence_a.id,
            presentation_order_index=1,
        )


def test_composite_fk_rejects_wrong_retrieval_result_id(db_session):
    _, retrieval_result, evidence = _seed_completed_retrieval(db_session)
    ranking_request = _create_ranking_request(db_session, retrieval_result.id)
    ranking_result = create_ranking_result(
        db_session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=retrieval_result.id,
        ranking_status="completed",
        rank_count=1,
        completed_at=utc_now(),
    )
    other_result_id = uuid4()
    with pytest.raises(IntegrityError):
        ranked = RankedEvidenceReference(
            ranking_result_id=ranking_result.id,
            retrieval_result_id=other_result_id,
            retrieval_evidence_reference_id=evidence.id,
            presentation_order_index=1,
            created_at=utc_now(),
        )
        db_session.add(ranked)
        db_session.flush()


@pytest.mark.parametrize("error_category", sorted(PROHIBITED_ERROR_CATEGORIES))
def test_prohibited_error_categories_rejected(error_category):
    with pytest.raises(ValueError, match="prohibited"):
        validate_ranking_error_category(error_category)


def test_canonical_error_category_accepted(db_session):
    _, retrieval_result, _ = _seed_completed_retrieval(db_session, result_count=0, with_evidence=False)
    ranking_request = _create_ranking_request(db_session, retrieval_result.id)
    failed = create_ranking_result(
        db_session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=retrieval_result.id,
        ranking_status="failed",
        error_category="retrieval_result_not_completed",
        error_message="upstream not completed",
        completed_at=utc_now(),
    )
    assert failed.error_category == "retrieval_result_not_completed"


def test_ranked_evidence_columns_are_pure_pointer_only(engine):
    inspector = sa_inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("ranked_evidence_references")}
    assert columns == RANKED_EVIDENCE_ALLOWED_COLUMNS


def test_prohibited_columns_absent_from_ranking_schema(engine):
    inspector = sa_inspect(engine)
    for table in RANKING_TABLES:
        columns = {col["name"] for col in inspector.get_columns(table)}
        for prohibited in PROHIBITED_TABLE_COLUMNS:
            assert prohibited not in columns, f"{prohibited} must not exist on {table}"


def test_ranked_model_has_no_provenance_attributes():
    mapper = sa_inspect(RankedEvidenceReference)
    column_names = {col.key for col in mapper.columns}
    assert column_names == RANKED_EVIDENCE_ALLOWED_COLUMNS


def test_append_only_multiple_results_preserved(db_session):
    _, retrieval_result, _ = _seed_completed_retrieval(db_session, result_count=0, with_evidence=False)
    ranking_request = _create_ranking_request(db_session, retrieval_result.id)
    create_ranking_result(
        db_session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=retrieval_result.id,
        ranking_status="accepted",
    )
    create_ranking_result(
        db_session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=retrieval_result.id,
        ranking_status="completed",
        rank_count=0,
        completed_at=utc_now(),
    )
    results = db_session.query(RankingResult).filter_by(ranking_request_id=ranking_request.id).all()
    assert len(results) == 2


def test_duplicate_default_ranking_request_hash_rejected(db_session):
    _, retrieval_result, _ = _seed_completed_retrieval(db_session, result_count=0, with_evidence=False)
    _create_ranking_request(db_session, retrieval_result.id)
    with pytest.raises(RankingPersistenceError, match="duplicate_default_request_for_hash"):
        _create_ranking_request(db_session, retrieval_result.id)


def test_force_replay_allows_duplicate_hash(db_session):
    _, retrieval_result, _ = _seed_completed_retrieval(db_session, result_count=0, with_evidence=False)
    first = _create_ranking_request(db_session, retrieval_result.id, force_replay=False)
    second = _create_ranking_request(
        db_session,
        retrieval_result.id,
        force_replay=True,
        replay_nonce="replay-1",
    )
    assert first.ranking_request_hash != second.ranking_request_hash


def test_fk_targets_retrieval_results_and_evidence(db_session):
    _, retrieval_result, evidence = _seed_completed_retrieval(db_session)
    ranking_request = _create_ranking_request(db_session, retrieval_result.id)
    ranking_result = create_ranking_result(
        db_session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=retrieval_result.id,
        ranking_status="completed",
        rank_count=1,
        completed_at=utc_now(),
    )
    ranked = create_ranked_evidence_reference(
        db_session,
        ranking_result_id=ranking_result.id,
        retrieval_result_id=retrieval_result.id,
        retrieval_evidence_reference_id=evidence.id,
        presentation_order_index=1,
    )
    assert ranking_request.retrieval_result_id == retrieval_result.id
    assert ranking_result.retrieval_result_id == retrieval_result.id
    assert ranked.retrieval_evidence_reference_id == evidence.id


def test_persistence_module_append_only_no_mutations():
    from app.services import ranking_persistence

    source = inspect.getsource(ranking_persistence.persistence)
    assert "def update_" not in source
    assert "def delete_" not in source
    assert ".delete(" not in source


def test_no_ranking_execution_in_persistence_package():
    pkg_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "ranking_persistence"
    forbidden = (
        "app.services.answer",
        "app.services.ai",
        "app.services.semantic",
        "app.services.vector",
        "CitationAssembler",
        "retrieval_execution",
    )
    for filename in ("hashing.py", "persistence.py", "validation.py"):
        source = (pkg_dir / filename).read_text().lower()
        for token in forbidden:
            assert token.lower() not in source, f"{token} must not appear in {filename}"


def test_no_worker_or_api_modules_added():
    backend_root = Path(__file__).resolve().parents[1] / "app"
    assert not (backend_root / "workers" / "ranking_runtime").exists()
    ranking_api_hits = list(backend_root.glob("**/ranking*api*.py"))
    assert ranking_api_hits == []
