"""TASK-009C answer worker skeleton tests."""

import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.answer_persistence import (
    CURRENT_CONTRACT_VERSION,
    DEFAULT_ASSEMBLY_CONTRACT_VERSION,
    AnswerPersistenceOutcome,
)
from app.services.ranking_execution import execute_controlled_ranking
from app.workers.answer_runtime import (
    DOCUMENTED_QUEUE_LIFECYCLE,
    QUEUE_LIFECYCLE_ACCEPTED,
    QUEUE_LIFECYCLE_COMPLETED,
    QUEUE_LIFECYCLE_FAILED,
    QUEUE_LIFECYCLE_RUNNING,
    AnswerWorker,
    AnswerWorkerError,
    AnswerWorkerOutcome,
    AnswerWorkerRequest,
    build_answer_worker_request,
    run_answer_worker,
)

FORBIDDEN_ANSWER_LOGIC_TOKENS = (
    "assemble_answer_package",
    "resolve_ranking_assembly_inputs",
    "create_answer_request",
    "create_answer_result",
    "create_answer_evidence_entry",
    "create_answer_uncertainty_flag",
    "execute_controlled_ranking",
    "apply_ranking_profile",
)

PROHIBITED_IMPORT_PREFIXES = (
    "from app.services.retrieval_execution",
    "import app.services.retrieval_execution",
    "from app.services.ranking_execution",
    "import app.services.ranking_execution",
    "from app.workers.ranking_runtime",
    "import app.workers.ranking_runtime",
    "from app.workers.retrieval_runtime",
    "import app.workers.retrieval_runtime",
    "from app.services.answer_assembly",
    "import app.services.answer_assembly",
    "from app.services.response_runtime",
    "import app.services.response_runtime",
    "from app.services.ai",
    "import app.services.ai",
    "from app.services.semantic",
    "import app.services.semantic",
    "from app.services.vector",
    "import app.services.vector",
    "from app.services.citation.assembler",
    "import app.services.citation.assembler",
    "from fastapi",
    "import fastapi",
    "APIRouter",
    "import celery",
    "from celery",
    "import redis",
    "from redis",
)


def _complete_ranking(db_session, evidence_specs, **request_kwargs):
    from app.core.datetime_utils import utc_now
    from app.services.retrieval_persistence import create_evidence_reference, create_retrieval_result
    from tests.test_retrieval_persistence import _create_request, _seed_citation

    request = _create_request(db_session, **request_kwargs)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="completed",
        result_count=len(evidence_specs),
        completed_at=utc_now(),
    )
    for index, spec in enumerate(evidence_specs, start=1):
        version, extracted, citation = _seed_citation(db_session)
        if spec.get("effective_from") is not None:
            version.effective_from = spec["effective_from"]
        if spec.get("effective_to") is not None:
            version.effective_to = spec["effective_to"]
        db_session.flush()
        create_evidence_reference(
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
    outcome = execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
    )
    assert outcome.ranking_status == "completed"
    return outcome.ranking_request_id


def test_worker_request_outcome_schemas():
    request = AnswerWorkerRequest(
        ranking_request_id=uuid.uuid4(),
        contract_version=CURRENT_CONTRACT_VERSION,
        assembly_contract_version=DEFAULT_ASSEMBLY_CONTRACT_VERSION,
        force_replay=False,
        replay_nonce=None,
    )
    outcome = AnswerWorkerOutcome(
        answer_request_id=uuid.uuid4(),
        answer_result_id=uuid.uuid4(),
        worker_status=QUEUE_LIFECYCLE_COMPLETED,
        answer_status="completed",
        evidence_entry_count=1,
        uncertainty_flag_count=0,
        error_category=None,
    )
    assert request.contract_version == CURRENT_CONTRACT_VERSION
    assert outcome.evidence_entry_count == 1


def test_documented_queue_lifecycle_states():
    assert DOCUMENTED_QUEUE_LIFECYCLE == frozenset(
        {
            QUEUE_LIFECYCLE_ACCEPTED,
            QUEUE_LIFECYCLE_RUNNING,
            QUEUE_LIFECYCLE_COMPLETED,
            QUEUE_LIFECYCLE_FAILED,
        }
    )


def test_build_answer_worker_request_defaults():
    ranking_request_id = uuid.uuid4()
    request = build_answer_worker_request(ranking_request_id=ranking_request_id)
    assert request.contract_version == CURRENT_CONTRACT_VERSION
    assert request.assembly_contract_version == DEFAULT_ASSEMBLY_CONTRACT_VERSION
    assert request.force_replay is False


def test_worker_validates_replay_nonce_when_force_replay():
    worker = AnswerWorker()
    with pytest.raises(AnswerWorkerError, match="replay_nonce is required"):
        worker.validate_request(
            AnswerWorkerRequest(
                ranking_request_id=uuid.uuid4(),
                contract_version=CURRENT_CONTRACT_VERSION,
                assembly_contract_version=DEFAULT_ASSEMBLY_CONTRACT_VERSION,
                force_replay=True,
                replay_nonce=None,
            )
        )


def test_worker_delegates_to_persist_answer_for_ranking_request():
    ranking_request_id = uuid.uuid4()
    request = build_answer_worker_request(ranking_request_id=ranking_request_id)
    expected = AnswerPersistenceOutcome(
        answer_request_id=uuid.uuid4(),
        answer_result_id=uuid.uuid4(),
        answer_status="completed",
        rank_count=1,
    )
    with patch(
        "app.workers.answer_runtime.worker.persist_answer_for_ranking_request",
        return_value=expected,
    ) as mocked:
        with patch(
            "app.workers.answer_runtime.worker.list_results_for_request",
            return_value=[],
        ):
            outcome = run_answer_worker(None, request)  # type: ignore[arg-type]
    mocked.assert_called_once()
    assert mocked.call_args.kwargs["ranking_request_id"] == ranking_request_id
    assert mocked.call_args.kwargs["requested_by_actor_type"] == "worker"
    assert outcome.answer_request_id == expected.answer_request_id
    assert outcome.worker_status == QUEUE_LIFECYCLE_COMPLETED
    assert outcome.answer_status == "completed"


def test_worker_maps_failed_persistence_outcome():
    request = build_answer_worker_request(ranking_request_id=uuid.uuid4())
    expected = AnswerPersistenceOutcome(
        answer_request_id=uuid.uuid4(),
        answer_result_id=uuid.uuid4(),
        answer_status="failed",
        rank_count=0,
        error_category="assembly_failed",
        error_message="injected",
    )
    with patch(
        "app.workers.answer_runtime.worker.persist_answer_for_ranking_request",
        return_value=expected,
    ):
        outcome = run_answer_worker(None, request)  # type: ignore[arg-type]
    assert outcome.worker_status == QUEUE_LIFECYCLE_FAILED
    assert outcome.answer_status == "failed"
    assert outcome.error_category == "assembly_failed"
    assert outcome.evidence_entry_count == 0
    assert outcome.uncertainty_flag_count == 0


def test_worker_maps_duplicate_rejected_outcome():
    answer_request_id = uuid.uuid4()
    request = build_answer_worker_request(ranking_request_id=uuid.uuid4())
    expected = AnswerPersistenceOutcome(
        answer_request_id=answer_request_id,
        answer_result_id=uuid.uuid4(),
        answer_status="duplicate_rejected",
        error_category="duplicate_answer",
        error_message="duplicate_default_request_for_hash",
    )
    with patch(
        "app.workers.answer_runtime.worker.persist_answer_for_ranking_request",
        return_value=expected,
    ):
        outcome = run_answer_worker(None, request)  # type: ignore[arg-type]
    assert outcome.worker_status == QUEUE_LIFECYCLE_FAILED
    assert outcome.answer_status == "duplicate_rejected"
    assert outcome.answer_request_id == answer_request_id
    assert outcome.error_category == "duplicate_answer"
    assert outcome.evidence_entry_count == 0
    assert outcome.uncertainty_flag_count == 0


def test_worker_does_not_contain_persistence_or_assembly_logic():
    worker_dir = Path(__file__).resolve().parents[1] / "app" / "workers" / "answer_runtime"
    sources = "".join(path.read_text() for path in worker_dir.glob("*.py")).lower()
    for token in FORBIDDEN_ANSWER_LOGIC_TOKENS:
        assert token.lower() not in sources, f"{token} must not appear in answer_runtime worker"


def test_answer_worker_import_guards():
    worker_dir = Path(__file__).resolve().parents[1] / "app" / "workers" / "answer_runtime"
    forbidden_create_tokens = (
        "create_answer_request",
        "create_answer_result",
        "create_answer_evidence_entry",
        "create_answer_uncertainty_flag",
        "assemble_answer_package",
        "resolve_ranking_assembly_inputs",
    )
    for path in worker_dir.glob("*.py"):
        text = path.read_text()
        for token in forbidden_create_tokens:
            assert token not in text, f"{token} must not appear in {path.name}"
        for line in text.splitlines():
            stripped = line.strip().lower()
            if not stripped.startswith(("import ", "from ")):
                continue
            for prefix in PROHIBITED_IMPORT_PREFIXES:
                assert not stripped.startswith(prefix.lower()), (
                    f"{prefix} forbidden in {path.name}: {line}"
                )


def test_answer_runtime_has_no_queue_modules():
    worker_dir = Path(__file__).resolve().parents[1] / "app" / "workers" / "answer_runtime"
    names = {path.name for path in worker_dir.iterdir()}
    assert "queue.py" not in names
    assert "broker.py" not in names
    assert "tasks.py" not in names


def test_od021_concurrent_worker_rejected():
    request = build_answer_worker_request(ranking_request_id=uuid.uuid4())
    worker = AnswerWorker()
    with patch(
        "app.workers.answer_runtime.worker._acquire_single_worker_slot",
        return_value=False,
    ):
        with pytest.raises(AnswerWorkerError, match="OD-021"):
            worker.run(None, request)  # type: ignore[arg-type]


@pytest.mark.integration
def test_od021_mutex_released_after_successful_run(db_session):
    """R-1: mutex released after first run — second sequential invocation proceeds without OD-021."""
    ranking_request_id = _complete_ranking(db_session, [{}])
    request = build_answer_worker_request(ranking_request_id=ranking_request_id)

    first = run_answer_worker(db_session, request)
    assert first.worker_status == QUEUE_LIFECYCLE_COMPLETED
    assert first.answer_status == "completed"

    second = run_answer_worker(db_session, request)
    assert second.worker_status == QUEUE_LIFECYCLE_FAILED
    assert second.answer_status == "duplicate_rejected"


@pytest.mark.integration
def test_worker_end_to_end_completed(db_session):
    ranking_request_id = _complete_ranking(db_session, [{}])
    request = build_answer_worker_request(ranking_request_id=ranking_request_id)
    outcome = run_answer_worker(db_session, request)
    assert outcome.worker_status == QUEUE_LIFECYCLE_COMPLETED
    assert outcome.answer_status == "completed"
    assert outcome.evidence_entry_count == 1
    assert outcome.error_category is None


@pytest.mark.integration
def test_worker_zero_evidence_counts(db_session):
    from tests.test_answer_persistence import _zero_evidence_ranking

    ranking_request_id, _ = _zero_evidence_ranking(db_session)
    request = build_answer_worker_request(ranking_request_id=ranking_request_id)
    outcome = run_answer_worker(db_session, request)
    assert outcome.worker_status == QUEUE_LIFECYCLE_COMPLETED
    assert outcome.answer_status == "completed"
    assert outcome.evidence_entry_count == 0
    assert outcome.uncertainty_flag_count >= 1


@pytest.mark.integration
def test_worker_duplicate_rejected_same_answer_request_id(db_session):
    ranking_request_id = _complete_ranking(db_session, [{}])
    request = build_answer_worker_request(ranking_request_id=ranking_request_id)
    first = run_answer_worker(db_session, request)
    second = run_answer_worker(db_session, request)
    assert first.worker_status == QUEUE_LIFECYCLE_COMPLETED
    assert first.answer_status == "completed"
    assert second.worker_status == QUEUE_LIFECYCLE_FAILED
    assert second.answer_status == "duplicate_rejected"
    assert second.answer_request_id == first.answer_request_id


@pytest.mark.integration
def test_worker_propagates_pre_persistence_failure(db_session):
    request = build_answer_worker_request(ranking_request_id=uuid.uuid4())
    with pytest.raises(AnswerWorkerError, match="ranking_request_missing"):
        run_answer_worker(db_session, request)
