"""TASK-008D controlled ranking execution tests."""

import inspect
import uuid
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import inspect as sa_inspect

from app.core.datetime_utils import utc_now
from app.models.ranked_evidence_reference import RankedEvidenceReference
from app.models.ranking_result import RankingResult
from app.services.ranking_execution import (
    RankingExecutionError,
    apply_ranking_profile,
    execute_controlled_ranking,
    validate_permutation,
)
from app.services.ranking_execution.models import RankingEvidenceRow
from app.services.ranking_persistence import (
    compute_ranking_request_hash,
    create_ranking_request,
    create_ranking_result,
    list_ranked_evidence_references,
    list_results_for_request,
)
from app.services.retrieval_persistence import (
    create_evidence_reference,
    create_retrieval_result,
)
from tests.test_retrieval_persistence import _create_request, _seed_citation


def _seed_completed_retrieval_with_evidence(db_session, evidence_specs):
    request = _create_request(db_session)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="completed",
        result_count=len(evidence_specs),
        completed_at=utc_now(),
    )
    evidence_rows = []
    for index, spec in enumerate(evidence_specs, start=1):
        version, extracted, citation = _seed_citation(db_session)
        if spec.get("effective_from") is not None:
            version.effective_from = spec["effective_from"]
        if spec.get("effective_to") is not None:
            version.effective_to = spec["effective_to"]
        db_session.flush()
        evidence = create_evidence_reference(
            db_session,
            retrieval_result_id=result.id,
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=extracted.source_version_id,
            citation_id=citation.citation_id,
            citation_hash=citation.citation_hash,
            source_document_id=spec.get("source_document_id"),
            object_identifier=spec.get("object_identifier", f"obj-{index}"),
            deterministic_order_index=index,
        )
        evidence_rows.append((evidence, version))
    return request, result, evidence_rows


def _accepted_result(db_session, ranking_request_id):
    results = list_results_for_request(db_session, ranking_request_id=ranking_request_id)
    return next(r for r in results if r.ranking_status == "accepted")


@pytest.mark.integration
def test_zero_evidence_completed_without_error(db_session):
    request = _create_request(db_session)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="completed",
        result_count=0,
        completed_at=utc_now(),
    )
    outcome = execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
    )
    assert outcome.ranking_status == "completed"
    assert outcome.rank_count == 0
    assert outcome.error_category is None
    accepted = _accepted_result(db_session, outcome.ranking_request_id)
    assert list_ranked_evidence_references(db_session, ranking_result_id=accepted.id) == []


@pytest.mark.integration
def test_canonical_identity_permutation(db_session):
    _, result, evidence_rows = _seed_completed_retrieval_with_evidence(
        db_session,
        [{"object_identifier": "a"}],
    )
    outcome = execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
    )
    assert outcome.ranking_status == "completed"
    assert outcome.rank_count == 1
    accepted = _accepted_result(db_session, outcome.ranking_request_id)
    ranked = list_ranked_evidence_references(db_session, ranking_result_id=accepted.id)
    assert len(ranked) == 1
    assert ranked[0].presentation_order_index == 1
    assert ranked[0].retrieval_evidence_reference_id == evidence_rows[0][0].id


@pytest.mark.integration
def test_determinism_same_inputs_same_order(db_session):
    _, result, _ = _seed_completed_retrieval_with_evidence(
        db_session,
        [
            {"object_identifier": "b", "effective_from": date(2024, 6, 1)},
            {"object_identifier": "a", "effective_from": date(2024, 1, 1)},
        ],
    )
    first = execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="EFFECTIVE_DATE_DESC",
        force_replay=True,
        replay_nonce="run-1",
    )
    second = execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="EFFECTIVE_DATE_DESC",
        force_replay=True,
        replay_nonce="run-2",
    )
    first_ranked = list_ranked_evidence_references(
        db_session,
        ranking_result_id=_accepted_result(db_session, first.ranking_request_id).id,
    )
    second_ranked = list_ranked_evidence_references(
        db_session,
        ranking_result_id=_accepted_result(db_session, second.ranking_request_id).id,
    )
    assert [row.presentation_order_index for row in first_ranked] == [
        row.presentation_order_index for row in second_ranked
    ]
    assert [row.retrieval_evidence_reference_id for row in first_ranked] == [
        row.retrieval_evidence_reference_id for row in second_ranked
    ]


def test_effective_date_desc_ordering_unit():
    rows = [
        RankingEvidenceRow(
            retrieval_evidence_reference_id=uuid.uuid4(),
            retrieval_result_id=uuid.uuid4(),
            deterministic_order_index=1,
            legal_object_id="lo_b",
            legal_object_version_id=uuid.uuid4(),
            source_version_id=uuid.uuid4(),
            source_document_id=None,
            citation_hash=None,
            object_identifier="b",
            effective_from=date(2024, 1, 1),
        ),
        RankingEvidenceRow(
            retrieval_evidence_reference_id=uuid.uuid4(),
            retrieval_result_id=uuid.uuid4(),
            deterministic_order_index=2,
            legal_object_id="lo_a",
            legal_object_version_id=uuid.uuid4(),
            source_version_id=uuid.uuid4(),
            source_document_id=None,
            citation_hash=None,
            object_identifier="a",
            effective_from=date(2024, 6, 1),
        ),
    ]
    ordered = apply_ranking_profile(rows, ranking_profile="EFFECTIVE_DATE_DESC")
    assert ordered[0].object_identifier == "a"
    assert ordered[1].object_identifier == "b"


def test_group_by_source_ordering_unit():
    source_a = uuid.uuid4()
    source_b = uuid.uuid4()
    rows = [
        RankingEvidenceRow(
            retrieval_evidence_reference_id=uuid.uuid4(),
            retrieval_result_id=uuid.uuid4(),
            deterministic_order_index=2,
            legal_object_id="lo_1",
            legal_object_version_id=uuid.uuid4(),
            source_version_id=source_b,
            source_document_id=None,
            citation_hash=None,
            object_identifier="z",
            effective_from=date(2024, 1, 1),
        ),
        RankingEvidenceRow(
            retrieval_evidence_reference_id=uuid.uuid4(),
            retrieval_result_id=uuid.uuid4(),
            deterministic_order_index=1,
            legal_object_id="lo_2",
            legal_object_version_id=uuid.uuid4(),
            source_version_id=source_a,
            source_document_id=None,
            citation_hash=None,
            object_identifier="y",
            effective_from=date(2024, 1, 1),
        ),
    ]
    ordered = apply_ranking_profile(rows, ranking_profile="GROUP_BY_SOURCE")
    expected_source_order = sorted([source_a, source_b], key=str)
    assert ordered[0].source_version_id == expected_source_order[0]
    assert ordered[1].source_version_id == expected_source_order[1]


def test_group_by_document_null_group_last_unit():
    doc_a = uuid.uuid4()
    rows = [
        RankingEvidenceRow(
            retrieval_evidence_reference_id=uuid.uuid4(),
            retrieval_result_id=uuid.uuid4(),
            deterministic_order_index=1,
            legal_object_id="lo_null",
            legal_object_version_id=uuid.uuid4(),
            source_version_id=uuid.uuid4(),
            source_document_id=None,
            citation_hash=None,
            object_identifier="null-doc",
            effective_from=date(2024, 1, 1),
        ),
        RankingEvidenceRow(
            retrieval_evidence_reference_id=uuid.uuid4(),
            retrieval_result_id=uuid.uuid4(),
            deterministic_order_index=2,
            legal_object_id="lo_doc",
            legal_object_version_id=uuid.uuid4(),
            source_version_id=uuid.uuid4(),
            source_document_id=doc_a,
            citation_hash=None,
            object_identifier="has-doc",
            effective_from=date(2024, 1, 1),
        ),
    ]
    ordered = apply_ranking_profile(rows, ranking_profile="GROUP_BY_DOCUMENT")
    assert ordered[0].source_document_id == doc_a
    assert ordered[1].source_document_id is None


def test_permutation_mismatch_detected():
    row_a = RankingEvidenceRow(
        retrieval_evidence_reference_id=uuid.uuid4(),
        retrieval_result_id=uuid.uuid4(),
        deterministic_order_index=1,
        legal_object_id="lo_a",
        legal_object_version_id=uuid.uuid4(),
        source_version_id=uuid.uuid4(),
        source_document_id=None,
        citation_hash=None,
        object_identifier="a",
        effective_from=None,
    )
    row_b = RankingEvidenceRow(
        retrieval_evidence_reference_id=uuid.uuid4(),
        retrieval_result_id=uuid.uuid4(),
        deterministic_order_index=2,
        legal_object_id="lo_b",
        legal_object_version_id=uuid.uuid4(),
        source_version_id=uuid.uuid4(),
        source_document_id=None,
        citation_hash=None,
        object_identifier="b",
        effective_from=None,
    )
    with pytest.raises(RankingExecutionError) as exc_info:
        validate_permutation([row_a, row_b], [row_a], expected_count=2)
    assert exc_info.value.category == "permutation_mismatch"


@pytest.mark.integration
def test_duplicate_default_request_rejected(db_session):
    _, result, _ = _seed_completed_retrieval_with_evidence(db_session, [{}])
    execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
    )
    with pytest.raises(RankingExecutionError, match="duplicate_ranking"):
        execute_controlled_ranking(
            db_session,
            retrieval_result_id=result.id,
            ranking_profile="CANONICAL",
        )


@pytest.mark.integration
def test_force_replay_allows_second_execution(db_session):
    _, result, _ = _seed_completed_retrieval_with_evidence(db_session, [{}])
    execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
    )
    outcome = execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
        force_replay=True,
        replay_nonce="replay-2",
    )
    assert outcome.ranking_status == "completed"


@pytest.mark.integration
def test_in_flight_accepted_guard(db_session):
    _, result, _ = _seed_completed_retrieval_with_evidence(db_session, [{}])
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
    with pytest.raises(RankingExecutionError, match="duplicate_ranking"):
        execute_controlled_ranking(
            db_session,
            retrieval_result_id=result.id,
            ranking_profile="CANONICAL",
        )


@pytest.mark.integration
def test_retrieval_result_missing(db_session):
    with pytest.raises(RankingExecutionError, match="retrieval_result_missing"):
        execute_controlled_ranking(
            db_session,
            retrieval_result_id=uuid.uuid4(),
            ranking_profile="CANONICAL",
        )


@pytest.mark.integration
def test_retrieval_not_completed(db_session):
    request = _create_request(db_session)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="accepted",
    )
    with pytest.raises(RankingExecutionError, match="retrieval_result_not_completed"):
        execute_controlled_ranking(
            db_session,
            retrieval_result_id=result.id,
            ranking_profile="CANONICAL",
        )


@pytest.mark.integration
def test_profile_not_allowed(db_session):
    _, result, _ = _seed_completed_retrieval_with_evidence(db_session, [{}])
    with pytest.raises(RankingExecutionError, match="profile_not_allowed"):
        execute_controlled_ranking(
            db_session,
            retrieval_result_id=result.id,
            ranking_profile="SEMANTIC_RANK",
        )


@pytest.mark.integration
def test_evidence_count_mismatch(db_session):
    request = _create_request(db_session)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="completed",
        result_count=2,
        completed_at=utc_now(),
    )
    with pytest.raises(RankingExecutionError, match="evidence_reference_missing"):
        execute_controlled_ranking(
            db_session,
            retrieval_result_id=result.id,
            ranking_profile="CANONICAL",
        )


@pytest.mark.integration
def test_failed_execution_persists_canonical_error(db_session):
    _, result, _ = _seed_completed_retrieval_with_evidence(db_session, [{}])
    with patch(
        "app.services.ranking_execution.execution.apply_ranking_profile",
        side_effect=RankingExecutionError("permutation_mismatch", "injected"),
    ):
        outcome = execute_controlled_ranking(
            db_session,
            retrieval_result_id=result.id,
            ranking_profile="CANONICAL",
        )
    assert outcome.ranking_status == "failed"
    assert outcome.error_category == "permutation_mismatch"
    failed = db_session.get(RankingResult, outcome.ranking_result_id)
    assert failed is not None
    assert failed.ranking_status == "failed"


@pytest.mark.integration
def test_append_only_lifecycle_history(db_session):
    _, result, _ = _seed_completed_retrieval_with_evidence(db_session, [{}])
    outcome = execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
    )
    results = list_results_for_request(db_session, ranking_request_id=outcome.ranking_request_id)
    statuses = [row.ranking_status for row in results]
    assert statuses == ["accepted", "completed"]


@pytest.mark.integration
def test_ranked_rows_are_pure_pointers(db_session):
    _, result, evidence_rows = _seed_completed_retrieval_with_evidence(db_session, [{}])
    outcome = execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
    )
    accepted = _accepted_result(db_session, outcome.ranking_request_id)
    ranked = list_ranked_evidence_references(db_session, ranking_result_id=accepted.id)[0]
    evidence = evidence_rows[0][0]
    assert ranked.ranking_result_id == accepted.id
    assert ranked.retrieval_result_id == result.id
    assert ranked.retrieval_evidence_reference_id == evidence.id
    assert ranked.presentation_order_index == 1
    column_names = {col.key for col in sa_inspect(RankedEvidenceReference).columns}
    assert "legal_object_id" not in column_names
    assert "citation_hash" not in column_names


def test_no_prohibited_imports_in_ranking_execution():
    service_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "ranking_execution"
    forbidden_prefixes = (
        "from app.services.answer",
        "import app.services.answer",
        "from app.services.ai",
        "import app.services.ai",
        "from app.services.semantic",
        "import app.services.semantic",
        "from app.services.vector",
        "import app.services.vector",
        "from app.services.retrieval_execution",
        "import app.services.retrieval_execution",
        "from app.services.citation.assembler",
        "import app.services.citation.assembler",
    )
    for path in service_dir.glob("*.py"):
        for line in path.read_text().splitlines():
            stripped = line.strip().lower()
            if not stripped.startswith(("import ", "from ")):
                continue
            for prefix in forbidden_prefixes:
                assert not stripped.startswith(prefix), f"{prefix} forbidden in {path.name}: {line}"


def test_ranking_runtime_worker_has_no_duplicate_ranking_logic():
    worker_dir = Path(__file__).resolve().parents[1] / "app" / "workers" / "ranking_runtime"
    if not worker_dir.exists():
        return
    sources = "".join(path.read_text() for path in worker_dir.glob("*.py")).lower()
    for token in ("apply_ranking_profile", "sort_canonical", "validate_permutation"):
        assert token not in sources, f"{token} must not appear in ranking_runtime worker"


def test_replay_hash_differs_with_nonce():
    retrieval_result_id = uuid.uuid4()
    first = compute_ranking_request_hash(
        retrieval_result_id=retrieval_result_id,
        ranking_profile="CANONICAL",
        force_replay=True,
        replay_nonce="nonce-1",
    )
    second = compute_ranking_request_hash(
        retrieval_result_id=retrieval_result_id,
        ranking_profile="CANONICAL",
        force_replay=True,
        replay_nonce="nonce-2",
    )
    assert first != second
