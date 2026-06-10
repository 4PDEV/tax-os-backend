"""U-01 ranking worker skeleton tests."""

import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.ranking_execution import RankingExecutionOutcome
from app.workers.ranking_runtime import (
    DOCUMENTED_QUEUE_LIFECYCLE,
    QUEUE_LIFECYCLE_ACCEPTED,
    QUEUE_LIFECYCLE_COMPLETED,
    QUEUE_LIFECYCLE_FAILED,
    QUEUE_LIFECYCLE_RUNNING,
    RankingWorker,
    RankingWorkerError,
    RankingWorkerOutcome,
    RankingWorkerRequest,
    build_ranking_worker_request,
    run_ranking_worker,
)
from tests.test_controlled_ranking_execution import _seed_completed_retrieval_with_evidence

FORBIDDEN_RANKING_LOGIC_TOKENS = (
    "apply_ranking_profile",
    "sort_canonical",
    "sort_effective_date_desc",
    "sort_group_by_source",
    "sort_group_by_document",
    "validate_permutation",
    "load_evidence_rows",
)


def test_worker_request_outcome_schemas():
    request = RankingWorkerRequest(
        retrieval_result_id=uuid.uuid4(),
        ranking_profile="CANONICAL",
        contract_version="008B-v2",
        force_replay=False,
        replay_nonce=None,
    )
    outcome = RankingWorkerOutcome(
        ranking_result_id=uuid.uuid4(),
        ranking_status=QUEUE_LIFECYCLE_COMPLETED,
        rank_count=2,
        error_category=None,
    )
    assert request.ranking_profile == "CANONICAL"
    assert outcome.rank_count == 2


def test_documented_queue_lifecycle_states():
    assert DOCUMENTED_QUEUE_LIFECYCLE == frozenset(
        {
            QUEUE_LIFECYCLE_ACCEPTED,
            QUEUE_LIFECYCLE_RUNNING,
            QUEUE_LIFECYCLE_COMPLETED,
            QUEUE_LIFECYCLE_FAILED,
        }
    )


def test_build_ranking_worker_request_defaults():
    retrieval_result_id = uuid.uuid4()
    request = build_ranking_worker_request(
        retrieval_result_id=retrieval_result_id,
        ranking_profile="CANONICAL",
    )
    assert request.contract_version == "008B-v2"
    assert request.force_replay is False


def test_worker_validates_profile():
    worker = RankingWorker()
    with pytest.raises(RankingWorkerError, match="invalid ranking_profile"):
        worker.validate_request(
            RankingWorkerRequest(
                retrieval_result_id=uuid.uuid4(),
                ranking_profile="AI_RANK",
                contract_version="008B-v2",
            )
        )


def test_worker_delegates_to_execute_controlled_ranking():
    retrieval_result_id = uuid.uuid4()
    request = build_ranking_worker_request(
        retrieval_result_id=retrieval_result_id,
        ranking_profile="CANONICAL",
    )
    expected = RankingExecutionOutcome(
        ranking_request_id=uuid.uuid4(),
        ranking_result_id=uuid.uuid4(),
        ranking_status="completed",
        rank_count=1,
    )
    with patch(
        "app.workers.ranking_runtime.worker.execute_controlled_ranking",
        return_value=expected,
    ) as mocked:
        outcome = run_ranking_worker(None, request)  # type: ignore[arg-type]
    mocked.assert_called_once()
    assert mocked.call_args.kwargs["retrieval_result_id"] == retrieval_result_id
    assert mocked.call_args.kwargs["ranking_profile"] == "CANONICAL"
    assert outcome.ranking_result_id == expected.ranking_result_id
    assert outcome.ranking_status == QUEUE_LIFECYCLE_COMPLETED
    assert outcome.rank_count == 1


def test_worker_maps_failed_execution_outcome():
    request = build_ranking_worker_request(
        retrieval_result_id=uuid.uuid4(),
        ranking_profile="CANONICAL",
    )
    expected = RankingExecutionOutcome(
        ranking_request_id=uuid.uuid4(),
        ranking_result_id=uuid.uuid4(),
        ranking_status="failed",
        rank_count=0,
        error_category="permutation_mismatch",
        error_message="injected",
    )
    with patch(
        "app.workers.ranking_runtime.worker.execute_controlled_ranking",
        return_value=expected,
    ):
        outcome = run_ranking_worker(None, request)  # type: ignore[arg-type]
    assert outcome.ranking_status == QUEUE_LIFECYCLE_FAILED
    assert outcome.error_category == "permutation_mismatch"


def test_worker_does_not_contain_ranking_logic():
    worker_dir = Path(__file__).resolve().parents[1] / "app" / "workers" / "ranking_runtime"
    sources = "".join(path.read_text() for path in worker_dir.glob("*.py")).lower()
    for token in FORBIDDEN_RANKING_LOGIC_TOKENS:
        assert token.lower() not in sources, f"{token} must not appear in ranking_runtime worker"


def test_worker_prohibited_imports():
    worker_dir = Path(__file__).resolve().parents[1] / "app" / "workers" / "ranking_runtime"
    forbidden_prefixes = (
        "from app.services.retrieval_execution",
        "import app.services.retrieval_execution",
        "from app.services.ai",
        "import app.services.ai",
        "from app.services.semantic",
        "import app.services.semantic",
        "from app.services.vector",
        "import app.services.vector",
        "from app.services.answer",
        "import app.services.answer",
        "from app.services.citation.assembler",
        "import app.services.citation.assembler",
    )
    for path in worker_dir.glob("*.py"):
        for line in path.read_text().splitlines():
            stripped = line.strip().lower()
            if not stripped.startswith(("import ", "from ")):
                continue
            for prefix in forbidden_prefixes:
                assert not stripped.startswith(prefix), f"{prefix} forbidden in {path.name}: {line}"


def test_od021_concurrent_worker_rejected():
    request = build_ranking_worker_request(
        retrieval_result_id=uuid.uuid4(),
        ranking_profile="CANONICAL",
    )
    worker = RankingWorker()
    with patch(
        "app.workers.ranking_runtime.worker._acquire_single_worker_slot",
        return_value=False,
    ):
        with pytest.raises(RankingWorkerError, match="OD-021"):
            worker.run(None, request)  # type: ignore[arg-type]


@pytest.mark.integration
def test_worker_end_to_end_delegates_execution(db_session):
    _, result, _ = _seed_completed_retrieval_with_evidence(db_session, [{}])
    request = build_ranking_worker_request(
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
    )
    outcome = run_ranking_worker(db_session, request)
    assert outcome.ranking_status == QUEUE_LIFECYCLE_COMPLETED
    assert outcome.rank_count == 1
    assert outcome.error_category is None


@pytest.mark.integration
def test_worker_propagates_pre_execution_failure(db_session):
    request = build_ranking_worker_request(
        retrieval_result_id=uuid.uuid4(),
        ranking_profile="CANONICAL",
    )
    with pytest.raises(RankingWorkerError, match="retrieval_result_missing"):
        run_ranking_worker(db_session, request)
