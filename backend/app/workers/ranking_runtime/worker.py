"""Ranking runtime worker skeleton (U-01).

Single-worker orchestration envelope around controlled ranking execution only.
OD-021: concurrent worker instances are not authorized.

No queue infrastructure (Celery, Redis, RabbitMQ, Kafka). Documented lifecycle only:
accepted → running → completed | failed
"""

from __future__ import annotations

import threading
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.ranking_execution import RankingExecutionError, execute_controlled_ranking
from app.services.ranking_persistence import CURRENT_CONTRACT_VERSION
from app.services.ranking_persistence.validation import RANKING_PROFILES
from app.workers.ranking_runtime.models import (
    QUEUE_LIFECYCLE_COMPLETED,
    QUEUE_LIFECYCLE_FAILED,
    QUEUE_LIFECYCLE_RUNNING,
    RankingWorkerOutcome,
    RankingWorkerRequest,
)

_execution_lock = threading.Lock()


def _acquire_single_worker_slot() -> bool:
    return _execution_lock.acquire(blocking=False)


def _release_single_worker_slot() -> None:
    _execution_lock.release()


class RankingWorkerError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class RankingWorker:
    """Single-worker ranking orchestration — delegates all ranking logic to execution service."""

    def validate_request(self, request: RankingWorkerRequest) -> None:
        if not isinstance(request.retrieval_result_id, UUID):
            raise RankingWorkerError("invalid retrieval_result_id")
        if request.ranking_profile not in RANKING_PROFILES:
            raise RankingWorkerError(f"invalid ranking_profile: {request.ranking_profile}")
        if not request.contract_version:
            raise RankingWorkerError("contract_version is required")
        if request.force_replay and not request.replay_nonce:
            raise RankingWorkerError("replay_nonce is required when force_replay is true")

    def run(self, db: Session, request: RankingWorkerRequest) -> RankingWorkerOutcome:
        if not _acquire_single_worker_slot():
            raise RankingWorkerError(
                "concurrent ranking worker execution not authorized (OD-021)"
            )
        try:
            self.validate_request(request)
            # Documented lifecycle: accepted (request) → running → completed | failed
            _ = QUEUE_LIFECYCLE_RUNNING
            try:
                outcome = execute_controlled_ranking(
                    db,
                    retrieval_result_id=request.retrieval_result_id,
                    ranking_profile=request.ranking_profile,
                    contract_version=request.contract_version,
                    force_replay=request.force_replay,
                    replay_nonce=request.replay_nonce,
                    requested_by_actor_type="worker",
                )
            except RankingExecutionError as exc:
                raise RankingWorkerError(f"{exc.category}: {exc.message}") from exc

            worker_status = (
                QUEUE_LIFECYCLE_COMPLETED
                if outcome.ranking_status == "completed"
                else QUEUE_LIFECYCLE_FAILED
            )
            return RankingWorkerOutcome(
                ranking_result_id=outcome.ranking_result_id,
                ranking_status=worker_status,
                rank_count=outcome.rank_count,
                error_category=outcome.error_category,
            )
        finally:
            _release_single_worker_slot()


def run_ranking_worker(
    db: Session,
    request: RankingWorkerRequest,
) -> RankingWorkerOutcome:
    """Single execution entrypoint for ranking worker orchestration."""
    worker = RankingWorker()
    return worker.run(db, request)


def build_ranking_worker_request(
    *,
    retrieval_result_id: UUID,
    ranking_profile: str,
    contract_version: str = CURRENT_CONTRACT_VERSION,
    force_replay: bool = False,
    replay_nonce: str | None = None,
) -> RankingWorkerRequest:
    return RankingWorkerRequest(
        retrieval_result_id=retrieval_result_id,
        ranking_profile=ranking_profile,
        contract_version=contract_version,
        force_replay=force_replay,
        replay_nonce=replay_nonce,
    )
