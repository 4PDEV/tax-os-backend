from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.source_processing_job import SourceProcessingJob
from app.models.source_version import SourceVersion
from app.services.ingestion_status import INGESTION_STATUS_QUEUED

JOB_TYPE_SOURCE_INGESTION = "source_ingestion"

JOB_STATUS_QUEUED = "queued"
JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELLED = "cancelled"

JOB_STATUSES = frozenset(
    {
        JOB_STATUS_QUEUED,
        JOB_STATUS_PROCESSING,
        JOB_STATUS_COMPLETED,
        JOB_STATUS_FAILED,
        JOB_STATUS_CANCELLED,
    }
)

JOB_TYPES = frozenset({JOB_TYPE_SOURCE_INGESTION})

ACTIVE_JOB_STATUSES = frozenset({JOB_STATUS_QUEUED, JOB_STATUS_PROCESSING})

ALLOWED_JOB_TRANSITIONS: dict[str, frozenset[str]] = {
    JOB_STATUS_QUEUED: frozenset({JOB_STATUS_PROCESSING, JOB_STATUS_CANCELLED}),
    JOB_STATUS_PROCESSING: frozenset({JOB_STATUS_COMPLETED, JOB_STATUS_FAILED}),
    JOB_STATUS_FAILED: frozenset({JOB_STATUS_QUEUED, JOB_STATUS_CANCELLED}),
    JOB_STATUS_COMPLETED: frozenset(),
    JOB_STATUS_CANCELLED: frozenset(),
}


class ProcessingQueueError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def validate_job_type(job_type: str) -> None:
    if job_type not in JOB_TYPES:
        raise ProcessingQueueError(f"invalid job type: {job_type}")


def validate_job_status(job_status: str) -> None:
    if job_status not in JOB_STATUSES:
        raise ProcessingQueueError(f"invalid job status: {job_status}")


def validate_job_transition(current_status: str, target_status: str) -> None:
    validate_job_status(current_status)
    validate_job_status(target_status)

    if current_status == target_status:
        raise ProcessingQueueError(f"job status is already {current_status}")

    allowed = ALLOWED_JOB_TRANSITIONS[current_status]
    if target_status not in allowed:
        raise ProcessingQueueError(
            f"transition from {current_status} to {target_status} is not allowed"
        )


def validate_enqueue(version: SourceVersion, job_type: str) -> None:
    validate_job_type(job_type)
    if version.ingestion_status != INGESTION_STATUS_QUEUED:
        raise ProcessingQueueError(
            "source version must have ingestion_status queued before enqueue"
        )


def has_active_job(jobs: list[SourceProcessingJob], job_type: str) -> bool:
    return any(
        job.job_type == job_type and job.job_status in ACTIVE_JOB_STATUSES for job in jobs
    )


def transition_job_status(
    job: SourceProcessingJob,
    target_status: str,
    *,
    last_error: str | None = None,
) -> SourceProcessingJob:
    validate_job_transition(job.job_status, target_status)

    if (
        job.job_status == JOB_STATUS_FAILED
        and target_status == JOB_STATUS_QUEUED
        and job.attempt_count >= job.max_attempts
    ):
        raise ProcessingQueueError("maximum retry attempts exceeded")

    now = utc_now()
    if target_status == JOB_STATUS_PROCESSING:
        job.attempt_count += 1
        job.started_at = now
        job.last_error = None
    elif target_status == JOB_STATUS_COMPLETED:
        job.completed_at = now
        job.last_error = None
    elif target_status == JOB_STATUS_FAILED:
        job.completed_at = now
        job.last_error = last_error or "processing failed"
    elif target_status == JOB_STATUS_QUEUED:
        job.started_at = None
        job.completed_at = None
        job.locked_at = None
        job.locked_by = None
        job.queued_at = now
    elif target_status == JOB_STATUS_CANCELLED:
        job.completed_at = now

    job.job_status = target_status
    job.updated_at = now
    return job


def claim_processing_job(job: SourceProcessingJob, locked_by: str) -> SourceProcessingJob:
    if not locked_by or not locked_by.strip():
        raise ProcessingQueueError("locked_by is required to claim a processing job")

    if job.job_status != JOB_STATUS_QUEUED:
        raise ProcessingQueueError("only queued jobs can be claimed")

    now = utc_now()
    job.locked_by = locked_by.strip()
    job.locked_at = now
    transition_job_status(job, JOB_STATUS_PROCESSING)
    return job


def claim_next_processing_job(
    db: Session,
    *,
    locked_by: str,
    job_type: str | None = None,
) -> SourceProcessingJob:
    if job_type is not None:
        validate_job_type(job_type)

    query = db.query(SourceProcessingJob).filter(
        SourceProcessingJob.job_status == JOB_STATUS_QUEUED
    )
    if job_type is not None:
        query = query.filter(SourceProcessingJob.job_type == job_type)

    job = (
        query.order_by(
            SourceProcessingJob.priority.desc(),
            SourceProcessingJob.queued_at.asc(),
        )
        .with_for_update(skip_locked=True)
        .first()
    )
    if not job:
        raise ProcessingQueueError("no queued processing job available")

    return claim_processing_job(job, locked_by)
