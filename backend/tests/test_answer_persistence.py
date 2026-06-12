"""TASK-009B answer persistence tests."""

import inspect
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import IntegrityError

from app.core.datetime_utils import utc_now
from app.models.answer_evidence_entry import AnswerEvidenceEntry
from app.services.answer_persistence import (
    CURRENT_CONTRACT_VERSION,
    DEFAULT_ASSEMBLY_CONTRACT_VERSION,
    PROHIBITED_ERROR_CATEGORIES,
    PROHIBITED_TABLE_COLUMNS,
    ANSWER_EVIDENCE_ALLOWED_COLUMNS,
    AnswerPersistenceError,
    build_hash_payload,
    canonical_json,
    compute_answer_request_hash,
    create_answer_evidence_entry,
    create_answer_request,
    create_answer_result,
    create_answer_uncertainty_flag,
    list_evidence_entries_for_result,
    list_results_for_request,
    list_uncertainty_flags_for_result,
    persist_answer_for_ranking_request,
    validate_answer_error_category,
)
from app.services.ranking_execution import execute_controlled_ranking
from app.services.ranking_persistence import create_ranking_request, create_ranking_result
from app.services.retrieval_persistence import create_retrieval_result
from tests.test_controlled_ranking_execution import _seed_completed_retrieval_with_evidence
from app.services.answer_assembly.validation import resolve_ranking_assembly_inputs
from tests.test_retrieval_persistence import _create_request

ANSWER_TABLES = (
    "answer_requests",
    "answer_results",
    "answer_evidence_entries",
    "answer_uncertainty_flags",
)

PROHIBITED_IMPORT_PREFIXES = (
    "from app.services.retrieval_execution",
    "import app.services.retrieval_execution",
    "from app.services.ranking_execution",
    "import app.services.ranking_execution",
    "from app.services.ai",
    "import app.services.ai",
    "from app.services.semantic",
    "import app.services.semantic",
    "from app.services.vector",
    "import app.services.vector",
    "from app.services.citation.assembler",
    "import app.services.citation.assembler",
    "from app.workers.answer_runtime",
    "import app.workers.answer_runtime",
    "from app.workers.ranking_runtime",
    "import app.workers.ranking_runtime",
    "from app.services.response_runtime",
    "import app.services.response_runtime",
    "from fastapi",
    "import fastapi",
    "APIRouter",
)


def _complete_ranking(db_session, evidence_specs):
    _, result, _ = _seed_completed_retrieval_with_evidence(db_session, evidence_specs)
    outcome = execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
    )
    assert outcome.ranking_status == "completed"
    return outcome.ranking_request_id, result.id


def _zero_evidence_ranking(db_session):
    request = _create_request(db_session)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="completed",
        result_count=0,
        completed_at=utc_now(),
    )
    ranking_request = create_ranking_request(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
        requested_by_actor_type="worker",
    )
    create_ranking_result(
        db_session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=result.id,
        ranking_status="accepted",
    )
    create_ranking_result(
        db_session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=result.id,
        ranking_status="completed",
        rank_count=0,
        completed_at=utc_now(),
    )
    return ranking_request.id, result.id


def test_answer_request_hash_deterministic():
    ranking_request_id = uuid4()
    hash_one = compute_answer_request_hash(
        ranking_request_id=ranking_request_id,
        contract_version=CURRENT_CONTRACT_VERSION,
        assembly_contract_version=DEFAULT_ASSEMBLY_CONTRACT_VERSION,
        include_rendered_citation_text=False,
    )
    hash_two = compute_answer_request_hash(
        ranking_request_id=ranking_request_id,
        contract_version=CURRENT_CONTRACT_VERSION,
        assembly_contract_version=DEFAULT_ASSEMBLY_CONTRACT_VERSION,
        include_rendered_citation_text=False,
    )
    assert hash_one == hash_two


def test_answer_request_hash_includes_replay_nonce_when_force_replay():
    ranking_request_id = uuid4()
    default_hash = compute_answer_request_hash(ranking_request_id=ranking_request_id)
    replay_hash = compute_answer_request_hash(
        ranking_request_id=ranking_request_id,
        force_replay=True,
        replay_nonce="nonce-1",
    )
    assert default_hash != replay_hash
    payload = build_hash_payload(
        ranking_request_id=ranking_request_id,
        force_replay=True,
        replay_nonce="nonce-1",
    )
    assert payload["force_replay"] is True
    assert payload["replay_nonce"] == "nonce-1"


def test_canonical_json_sorted_keys():
    payload = build_hash_payload(ranking_request_id=uuid4())
    serialized = canonical_json(payload)
    assert serialized.index('"assembly_contract_version"') < serialized.index('"contract_version"')


@pytest.mark.integration
def test_orchestration_persists_completed_package(db_session):
    ranking_request_id, _ = _complete_ranking(db_session, [{}])
    outcome = persist_answer_for_ranking_request(
        db_session,
        ranking_request_id=ranking_request_id,
    )
    assert outcome.answer_status == "completed"
    assert outcome.rank_count == 1

    results = list_results_for_request(db_session, answer_request_id=outcome.answer_request_id)
    statuses = [row.answer_status for row in results]
    assert statuses == ["accepted", "completed"]

    accepted = results[0]
    evidence = list_evidence_entries_for_result(db_session, answer_result_id=accepted.id)
    assert len(evidence) == 1
    assert evidence[0].presentation_order_index == 1

    terminal = results[1]
    assert terminal.accepted_ranking_result_id is not None
    assert terminal.terminal_ranking_result_id is not None


@pytest.mark.integration
def test_zero_evidence_persistence(db_session):
    ranking_request_id, _ = _zero_evidence_ranking(db_session)
    outcome = persist_answer_for_ranking_request(
        db_session,
        ranking_request_id=ranking_request_id,
    )
    assert outcome.answer_status == "completed"
    assert outcome.rank_count == 0

    results = list_results_for_request(db_session, answer_request_id=outcome.answer_request_id)
    accepted = results[0]
    assert list_evidence_entries_for_result(db_session, answer_result_id=accepted.id) == []
    flags = list_uncertainty_flags_for_result(db_session, answer_result_id=accepted.id)
    assert any(flag.flag_type == "zero_evidence" for flag in flags)


@pytest.mark.integration
def test_duplicate_default_request_rejected(db_session):
    ranking_request_id, _ = _complete_ranking(db_session, [{}])
    persist_answer_for_ranking_request(db_session, ranking_request_id=ranking_request_id)
    second = persist_answer_for_ranking_request(db_session, ranking_request_id=ranking_request_id)
    assert second.answer_status == "duplicate_rejected"
    assert second.error_category == "duplicate_answer"


@pytest.mark.integration
def test_force_replay_allows_second_persistence(db_session):
    ranking_request_id, _ = _complete_ranking(db_session, [{}])
    first = persist_answer_for_ranking_request(db_session, ranking_request_id=ranking_request_id)
    second = persist_answer_for_ranking_request(
        db_session,
        ranking_request_id=ranking_request_id,
        force_replay=True,
        replay_nonce="replay-1",
    )
    assert second.answer_status == "completed"
    assert first.answer_request_id != second.answer_request_id


@pytest.mark.integration
def test_in_flight_accepted_guard(db_session):
    ranking_request_id, retrieval_result_id = _complete_ranking(db_session, [{}])
    answer_request = create_answer_request(
        db_session,
        ranking_request_id=ranking_request_id,
        requested_by_actor_type="worker",
    )
    create_answer_result(
        db_session,
        answer_request_id=answer_request.id,
        ranking_request_id=ranking_request_id,
        retrieval_result_id=retrieval_result_id,
        answer_status="accepted",
    )
    db_session.commit()
    with pytest.raises(AnswerPersistenceError, match="in_flight_accepted_answer_result"):
        persist_answer_for_ranking_request(db_session, ranking_request_id=ranking_request_id)


@pytest.mark.integration
def test_v_b_02_ranked_parent_mismatch_rejected(db_session):
    from app.services.ranking_persistence import create_ranked_evidence_reference

    ranking_request_id, retrieval_result_id = _complete_ranking(db_session, [{}])
    inputs = resolve_ranking_assembly_inputs(db_session, ranking_request_id=ranking_request_id)
    ranked_row = inputs.ranked_rows[0]
    ranked_on_terminal = create_ranked_evidence_reference(
        db_session,
        ranking_result_id=inputs.terminal_ranking_result.id,
        retrieval_result_id=retrieval_result_id,
        retrieval_evidence_reference_id=ranked_row.retrieval_evidence_reference_id,
        presentation_order_index=1,
    )

    answer_request = create_answer_request(
        db_session,
        ranking_request_id=ranking_request_id,
        requested_by_actor_type="worker",
    )
    accepted = create_answer_result(
        db_session,
        answer_request_id=answer_request.id,
        ranking_request_id=ranking_request_id,
        retrieval_result_id=retrieval_result_id,
        answer_status="accepted",
    )
    with pytest.raises(AnswerPersistenceError, match="ranked_evidence_parent_mismatch"):
        create_answer_evidence_entry(
            db_session,
            answer_result_id=accepted.id,
            answer_request_id=answer_request.id,
            ranking_request_id=ranking_request_id,
            ranked_evidence_reference_id=ranked_on_terminal.id,
            retrieval_result_id=retrieval_result_id,
            retrieval_evidence_reference_id=ranked_row.retrieval_evidence_reference_id,
            presentation_order_index=1,
            accepted_ranking_result_id=inputs.accepted_ranking_result.id,
        )


@pytest.mark.integration
def test_pure_pointer_evidence_columns_only(engine):
    inspector = sa_inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("answer_evidence_entries")}
    assert columns == ANSWER_EVIDENCE_ALLOWED_COLUMNS


@pytest.mark.integration
def test_prohibited_columns_absent_from_answer_schema(engine):
    inspector = sa_inspect(engine)
    for table in ANSWER_TABLES:
        columns = {col["name"] for col in inspector.get_columns(table)}
        for prohibited in PROHIBITED_TABLE_COLUMNS:
            assert prohibited not in columns, f"{prohibited} must not exist on {table}"


def test_evidence_model_has_no_provenance_attributes():
    mapper = sa_inspect(AnswerEvidenceEntry)
    column_names = {col.key for col in mapper.columns}
    assert column_names == ANSWER_EVIDENCE_ALLOWED_COLUMNS


@pytest.mark.integration
def test_append_only_multiple_results_preserved(db_session):
    ranking_request_id, retrieval_result_id = _complete_ranking(db_session, [{}])
    answer_request = create_answer_request(
        db_session,
        ranking_request_id=ranking_request_id,
        requested_by_actor_type="worker",
    )
    create_answer_result(
        db_session,
        answer_request_id=answer_request.id,
        ranking_request_id=ranking_request_id,
        retrieval_result_id=retrieval_result_id,
        answer_status="accepted",
    )
    create_answer_result(
        db_session,
        answer_request_id=answer_request.id,
        ranking_request_id=ranking_request_id,
        retrieval_result_id=retrieval_result_id,
        answer_status="completed",
        rank_count=1,
        completed_at=utc_now(),
    )
    results = list_results_for_request(db_session, answer_request_id=answer_request.id)
    assert len(results) == 2


@pytest.mark.integration
def test_duplicate_presentation_order_index_rejected(db_session):
    ranking_request_id, retrieval_result_id = _complete_ranking(db_session, [{}])
    inputs = resolve_ranking_assembly_inputs(db_session, ranking_request_id=ranking_request_id)
    ranked_row = inputs.ranked_rows[0]
    answer_request = create_answer_request(
        db_session,
        ranking_request_id=ranking_request_id,
        requested_by_actor_type="worker",
    )
    accepted = create_answer_result(
        db_session,
        answer_request_id=answer_request.id,
        ranking_request_id=ranking_request_id,
        retrieval_result_id=retrieval_result_id,
        answer_status="accepted",
    )
    create_answer_evidence_entry(
        db_session,
        answer_result_id=accepted.id,
        answer_request_id=answer_request.id,
        ranking_request_id=ranking_request_id,
        ranked_evidence_reference_id=ranked_row.id,
        retrieval_result_id=retrieval_result_id,
        retrieval_evidence_reference_id=ranked_row.retrieval_evidence_reference_id,
        presentation_order_index=1,
        accepted_ranking_result_id=inputs.accepted_ranking_result.id,
    )
    with pytest.raises(IntegrityError):
        create_answer_evidence_entry(
            db_session,
            answer_result_id=accepted.id,
            answer_request_id=answer_request.id,
            ranking_request_id=ranking_request_id,
            ranked_evidence_reference_id=ranked_row.id,
            retrieval_result_id=retrieval_result_id,
            retrieval_evidence_reference_id=ranked_row.retrieval_evidence_reference_id,
            presentation_order_index=1,
            accepted_ranking_result_id=inputs.accepted_ranking_result.id,
        )


@pytest.mark.parametrize("error_category", sorted(PROHIBITED_ERROR_CATEGORIES))
def test_prohibited_error_categories_rejected(error_category):
    with pytest.raises(ValueError, match="prohibited"):
        validate_answer_error_category(error_category)


def test_persistence_module_append_only_no_mutations():
    from app.services import answer_persistence

    source = inspect.getsource(answer_persistence.persistence)
    assert "def update_" not in source
    assert "def delete_" not in source
    assert ".delete(" not in source


def test_answer_persistence_import_guards():
    pkg_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "answer_persistence"
    for filename in ("hashing.py", "persistence.py", "validation.py", "__init__.py"):
        source = (pkg_dir / filename).read_text()
        for token in PROHIBITED_IMPORT_PREFIXES:
            assert token not in source, f"{token} must not appear in {filename}"


@pytest.mark.integration
def test_orchestration_does_not_call_ranking_create_apis(db_session):
    from unittest.mock import patch

    ranking_request_id, _ = _complete_ranking(db_session, [{}])
    with patch("app.services.ranking_persistence.create_ranking_request") as mocked:
        persist_answer_for_ranking_request(db_session, ranking_request_id=ranking_request_id)
        mocked.assert_not_called()


@pytest.mark.integration
def test_uncertainty_flag_persisted(db_session):
    ranking_request_id, _ = _complete_ranking(db_session, [{}])
    outcome = persist_answer_for_ranking_request(db_session, ranking_request_id=ranking_request_id)
    results = list_results_for_request(db_session, answer_request_id=outcome.answer_request_id)
    accepted = results[0]
    flags = list_uncertainty_flags_for_result(db_session, answer_result_id=accepted.id)
    assert isinstance(flags, list)
