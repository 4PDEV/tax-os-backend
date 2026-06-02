from pathlib import Path

from sqlalchemy.orm import Session

from app.workers.extraction.controlled_local_provider import ControlledLocalExtractionProvider
from app.workers.extraction.dry_run_provider import DryRunExtractionProvider
from app.workers.extraction.result import ExtractionRunSummary
from app.workers.extraction.worker import (
    EXECUTION_MODE_CONTROLLED_LOCAL,
    EXECUTION_MODE_DRY_RUN,
    ExtractionWorker,
    ExtractionWorkerError,
)


def run_extraction_dry_run(
    db: Session,
    *,
    worker_name: str = "extraction-worker",
    worker_version: str = "0.1.0",
    dry_run: bool = True,
) -> ExtractionRunSummary:
    if not dry_run:
        raise ExtractionWorkerError("dry_run=True is required for run_extraction_dry_run")
    worker = ExtractionWorker(
        provider=DryRunExtractionProvider(),
        mode=EXECUTION_MODE_DRY_RUN,
    )
    return worker.run(db, worker_name=worker_name, worker_version=worker_version)


def run_controlled_local_extraction(
    db: Session,
    *,
    artifact_root: Path,
    worker_name: str = "extraction-worker",
    worker_version: str = "0.1.0",
    controlled_local: bool = True,
    max_content_size_bytes: int = 1024 * 1024,
) -> ExtractionRunSummary:
    if not controlled_local:
        raise ExtractionWorkerError(
            "controlled_local=True is required for run_controlled_local_extraction"
        )
    worker = ExtractionWorker(
        provider=ControlledLocalExtractionProvider(
            artifact_root=artifact_root,
            max_content_size_bytes=max_content_size_bytes,
        ),
        mode=EXECUTION_MODE_CONTROLLED_LOCAL,
    )
    return worker.run(db, worker_name=worker_name, worker_version=worker_version)
