"""Retrieval runtime worker (TASK-007D dry-run skeleton).

OD-021: single-worker assumption is acceptable. Concurrent retrieval workers require
execution-time advisory locks or row locks keyed by request_hash (future task).

Dry-run ``skipped`` means orchestration completed without retrieval execution — not that the
request was ignored (ineligible requests increment ``requests_skipped`` without a new skipped
result row from ``run()``).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.retrieval_request import RetrievalRequest
from app.services.retrieval_persistence.persistence import (
    create_retrieval_result,
    get_latest_result_for_request,
)
from app.services.retrieval_persistence.validation import (
    RETRIEVAL_MODES,
    validate_actor_type,
)
from app.workers.retrieval_runtime.dry_run_provider import (
    DRY_RUN_RETRIEVAL_RUNTIME_PROVIDER_NAME,
    DRY_RUN_RETRIEVAL_RUNTIME_PROVIDER_VERSION,
    RetrievalRuntimeProvider,
)
from app.workers.retrieval_runtime.result import RetrievalRuntimeRunSummary

EXECUTION_MODE_DRY_RUN = "dry_run"
ALLOWED_EXECUTION_MODES = frozenset({EXECUTION_MODE_DRY_RUN})

TERMINAL_SKIP_STATUSES = frozenset({"completed", "failed", "skipped", "duplicate_rejected"})
DRY_RUN_TERMINAL_STATUS = "skipped"


class RetrievalRuntimeWorkerError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class RetrievalRuntimeWorker:
    def __init__(self, *, provider: RetrievalRuntimeProvider, mode: str):
        if mode not in ALLOWED_EXECUTION_MODES:
            raise RetrievalRuntimeWorkerError(
                f"unsupported retrieval runtime execution mode: {mode}"
            )
        self._provider = provider
        self._mode = mode

    def load_requests(self, db: Session) -> list[RetrievalRequest]:
        stmt = select(RetrievalRequest).order_by(
            RetrievalRequest.created_at.asc(),
            RetrievalRequest.id.asc(),
        )
        return list(db.execute(stmt).scalars().all())

    def is_eligible(self, db: Session, request: RetrievalRequest) -> bool:
        if request.retrieval_mode not in RETRIEVAL_MODES:
            return False
        try:
            validate_actor_type(request.requested_by_actor_type)
        except ValueError:
            return False

        latest = get_latest_result_for_request(db, retrieval_request_id=request.id)
        if latest is not None and latest.retrieval_status in TERMINAL_SKIP_STATUSES:
            if request.force_replay:
                return True
            return False
        return True

    def run(
        self,
        db: Session,
        *,
        worker_name: str = "retrieval-runtime-worker",
        worker_version: str | None = None,
    ) -> RetrievalRuntimeRunSummary:
        resolved_version = worker_version or DRY_RUN_RETRIEVAL_RUNTIME_PROVIDER_VERSION

        requests_seen = processed = skipped = results_created = failures = replayed = 0

        for request in self.load_requests(db):
            requests_seen += 1
            if not self.is_eligible(db, request):
                skipped += 1
                continue

            if request.force_replay:
                replayed += 1

            try:
                create_retrieval_result(
                    db,
                    retrieval_request_id=request.id,
                    retrieval_status="accepted",
                    notes=f"accepted by {worker_name}",
                )
                results_created += 1

                provider_result = self._provider.run_retrieval(db, request)
                provider_name = provider_result.provider_name or DRY_RUN_RETRIEVAL_RUNTIME_PROVIDER_NAME
                provider_version = provider_result.provider_version or resolved_version

                if not provider_result.success:
                    create_retrieval_result(
                        db,
                        retrieval_request_id=request.id,
                        retrieval_status="failed",
                        error_category=provider_result.error_category or "unknown_failure",
                        error_message=provider_result.error_message,
                        notes=provider_result.notes
                        or f"provider failure ({provider_name}@{provider_version})",
                        completed_at=utc_now(),
                    )
                    results_created += 1
                    failures += 1
                    processed += 1
                    continue

                create_retrieval_result(
                    db,
                    retrieval_request_id=request.id,
                    retrieval_status=DRY_RUN_TERMINAL_STATUS,
                    result_count=0,
                    completed_at=utc_now(),
                    notes=provider_result.notes
                    or (
                        f"dry-run retrieval lifecycle completed by {worker_name}; "
                        "no evidence references; no retrieval execution"
                    ),
                )
                results_created += 1
                processed += 1
            except Exception as exc:
                create_retrieval_result(
                    db,
                    retrieval_request_id=request.id,
                    retrieval_status="failed",
                    error_category="unknown_failure",
                    error_message=str(exc),
                    notes=f"worker failure recorded by {worker_name}",
                    completed_at=utc_now(),
                )
                results_created += 1
                failures += 1
                processed += 1

        return RetrievalRuntimeRunSummary(
            requests_seen=requests_seen,
            requests_processed=processed,
            requests_skipped=skipped,
            results_created=results_created,
            failures=failures,
            requests_replayed=replayed,
        )
