from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.source_processing_job import SourceProcessingJob
from app.models.source_version import SourceVersion
from app.services.processing_queue import (
    ProcessingQueueError,
    claim_next_processing_job,
    complete_processing_job,
    fail_processing_job,
)
from app.workers.contract import SourceJobProcessor

OUTCOME_NO_JOB = "no_job"
OUTCOME_COMPLETED = "completed"
OUTCOME_FAILED = "failed"


class WorkerRunnerError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class WorkerRunResult:
    outcome: str
    job: SourceProcessingJob | None = None


def run_next_job_once(
    db: Session,
    *,
    worker_id: str,
    processor: SourceJobProcessor,
    job_type: str | None = None,
    commit: bool = True,
) -> WorkerRunResult:
    """
    One-shot worker execution: claim at most one queued job, process, finalize.

    Does not loop and does not run in the background.
    """
    if not worker_id or not worker_id.strip():
        raise WorkerRunnerError("worker_id is required")

    worker_name = worker_id.strip()

    try:
        job = claim_next_processing_job(db, locked_by=worker_name, job_type=job_type)
    except ProcessingQueueError as exc:
        if exc.message == "no queued processing job available":
            return WorkerRunResult(outcome=OUTCOME_NO_JOB, job=None)
        raise WorkerRunnerError(exc.message) from exc

    version = (
        db.query(SourceVersion)
        .filter(SourceVersion.id == job.source_version_id)
        .first()
    )
    if not version:
        raise WorkerRunnerError("source version not found for claimed job")

    processing_result = processor.process(job, version)

    if processing_result.success:
        complete_processing_job(
            db,
            job,
            completed_by=worker_name,
            result_json=processing_result.result_json,
        )
        outcome = OUTCOME_COMPLETED
    else:
        fail_processing_job(
            db,
            job,
            failed_by=worker_name,
            last_error=processing_result.error_message or "processing failed",
            result_json=processing_result.result_json,
        )
        outcome = OUTCOME_FAILED

    if commit:
        db.commit()
    else:
        db.flush()
    db.refresh(job)
    return WorkerRunResult(outcome=outcome, job=job)
