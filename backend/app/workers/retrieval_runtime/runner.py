from sqlalchemy.orm import Session

from app.workers.retrieval_runtime.controlled_provider import ControlledRetrievalRuntimeProvider
from app.workers.retrieval_runtime.dry_run_provider import DryRunRetrievalRuntimeProvider
from app.workers.retrieval_runtime.result import RetrievalRuntimeRunSummary
from app.workers.retrieval_runtime.worker import (
    EXECUTION_MODE_CONTROLLED_EXECUTION,
    EXECUTION_MODE_DRY_RUN,
    RetrievalRuntimeWorker,
    RetrievalRuntimeWorkerError,
)


def run_retrieval_runtime_dry_run(
    db: Session,
    *,
    worker_name: str = "retrieval-runtime-worker",
    worker_version: str = "0.1.0",
    dry_run: bool = True,
) -> RetrievalRuntimeRunSummary:
    if not dry_run:
        raise RetrievalRuntimeWorkerError(
            "dry_run=True is required for run_retrieval_runtime_dry_run"
        )
    worker = RetrievalRuntimeWorker(
        provider=DryRunRetrievalRuntimeProvider(),
        mode=EXECUTION_MODE_DRY_RUN,
    )
    return worker.run(db, worker_name=worker_name, worker_version=worker_version)


def run_controlled_retrieval_execution(
    db: Session,
    *,
    worker_name: str = "retrieval-runtime-worker",
    worker_version: str = "0.1.0",
    controlled_execution: bool = True,
) -> RetrievalRuntimeRunSummary:
    if not controlled_execution:
        raise RetrievalRuntimeWorkerError(
            "controlled_execution=True is required for run_controlled_retrieval_execution"
        )
    worker = RetrievalRuntimeWorker(
        provider=ControlledRetrievalRuntimeProvider(),
        mode=EXECUTION_MODE_CONTROLLED_EXECUTION,
    )
    return worker.run(db, worker_name=worker_name, worker_version=worker_version)
