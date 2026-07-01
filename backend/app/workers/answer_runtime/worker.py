"""Answer runtime worker skeleton (TASK-009C).

Single-worker orchestration envelope around answer persistence only.
OD-021: concurrent worker instances are not authorized.

No queue infrastructure (Celery, Redis, RabbitMQ, Kafka). Documented lifecycle only:
accepted → running → completed | failed
"""

from __future__ import annotations

import threading
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.answer_persistence import (
    CURRENT_CONTRACT_VERSION,
    DEFAULT_ASSEMBLY_CONTRACT_VERSION,
    AnswerPersistenceError,
    AnswerPersistenceOutcome,
    list_evidence_entries_for_result,
    list_results_for_request,
    list_uncertainty_flags_for_result,
    persist_answer_for_ranking_request,
)
from app.workers.answer_runtime.models import (
    QUEUE_LIFECYCLE_COMPLETED,
    QUEUE_LIFECYCLE_FAILED,
    QUEUE_LIFECYCLE_RUNNING,
    AnswerWorkerError,
    AnswerWorkerOutcome,
    AnswerWorkerRequest,
)

_execution_lock = threading.Lock()


def _acquire_single_worker_slot() -> bool:
    return _execution_lock.acquire(blocking=False)


def _release_single_worker_slot() -> None:
    _execution_lock.release()


def _enrich_counts(
    db: Session,
    *,
    answer_request_id: UUID,
    persistence_outcome: AnswerPersistenceOutcome,
) -> tuple[int, int]:
    if persistence_outcome.answer_status != "completed":
        return 0, 0

    results = list_results_for_request(db, answer_request_id=answer_request_id)
    accepted_rows = [row for row in results if row.answer_status == "accepted"]
    if len(accepted_rows) != 1:
        return 0, 0

    accepted = accepted_rows[0]
    evidence_entry_count = len(
        list_evidence_entries_for_result(db, answer_result_id=accepted.id)
    )
    uncertainty_flag_count = len(
        list_uncertainty_flags_for_result(db, answer_result_id=accepted.id)
    )
    return evidence_entry_count, uncertainty_flag_count


def _map_persistence_outcome(
    db: Session,
    persistence_outcome: AnswerPersistenceOutcome,
) -> AnswerWorkerOutcome:
    if persistence_outcome.answer_status == "completed":
        worker_status = QUEUE_LIFECYCLE_COMPLETED
        evidence_entry_count, uncertainty_flag_count = _enrich_counts(
            db,
            answer_request_id=persistence_outcome.answer_request_id,
            persistence_outcome=persistence_outcome,
        )
        return AnswerWorkerOutcome(
            answer_request_id=persistence_outcome.answer_request_id,
            answer_result_id=persistence_outcome.answer_result_id,
            worker_status=worker_status,
            answer_status="completed",
            evidence_entry_count=evidence_entry_count,
            uncertainty_flag_count=uncertainty_flag_count,
            error_category=None,
        )

    worker_status = QUEUE_LIFECYCLE_FAILED
    return AnswerWorkerOutcome(
        answer_request_id=persistence_outcome.answer_request_id,
        answer_result_id=persistence_outcome.answer_result_id,
        worker_status=worker_status,
        answer_status=persistence_outcome.answer_status,
        evidence_entry_count=0,
        uncertainty_flag_count=0,
        error_category=persistence_outcome.error_category,
    )


class AnswerWorker:
    """Single-worker answer orchestration — delegates all persistence to 009B service."""

    def validate_request(self, request: AnswerWorkerRequest) -> None:
        if not isinstance(request.ranking_request_id, UUID):
            raise AnswerWorkerError("invalid ranking_request_id")
        if not request.contract_version:
            raise AnswerWorkerError("contract_version is required")
        if not request.assembly_contract_version:
            raise AnswerWorkerError("assembly_contract_version is required")
        if request.force_replay and not request.replay_nonce:
            raise AnswerWorkerError("replay_nonce is required when force_replay is true")

    def run(self, db: Session, request: AnswerWorkerRequest) -> AnswerWorkerOutcome:
        if not _acquire_single_worker_slot():
            raise AnswerWorkerError(
                "concurrent answer worker execution not authorized (OD-021)"
            )
        try:
            self.validate_request(request)
            # Documented lifecycle: accepted (request) → running → completed | failed
            _ = QUEUE_LIFECYCLE_RUNNING
            try:
                persistence_outcome = persist_answer_for_ranking_request(
                    db,
                    ranking_request_id=request.ranking_request_id,
                    contract_version=request.contract_version,
                    assembly_contract_version=request.assembly_contract_version,
                    include_rendered_citation_text=request.include_rendered_citation_text,
                    force_replay=request.force_replay,
                    replay_nonce=request.replay_nonce,
                    requested_by_actor_type="worker",
                )
            except AnswerPersistenceError as exc:
                raise AnswerWorkerError(str(exc)) from exc

            return _map_persistence_outcome(db, persistence_outcome)
        finally:
            _release_single_worker_slot()


def run_answer_worker(
    db: Session,
    request: AnswerWorkerRequest,
) -> AnswerWorkerOutcome:
    """Single execution entrypoint for answer worker orchestration."""
    worker = AnswerWorker()
    return worker.run(db, request)


def build_answer_worker_request(
    *,
    ranking_request_id: UUID,
    contract_version: str = CURRENT_CONTRACT_VERSION,
    assembly_contract_version: str = DEFAULT_ASSEMBLY_CONTRACT_VERSION,
    include_rendered_citation_text: bool = False,
    force_replay: bool = False,
    replay_nonce: str | None = None,
) -> AnswerWorkerRequest:
    return AnswerWorkerRequest(
        ranking_request_id=ranking_request_id,
        contract_version=contract_version,
        assembly_contract_version=assembly_contract_version,
        include_rendered_citation_text=include_rendered_citation_text,
        force_replay=force_replay,
        replay_nonce=replay_nonce,
    )
