from unittest.mock import MagicMock

import pytest

from app.models.source_processing_job import SourceProcessingJob
from app.models.source_version import SourceVersion
from app.services.ingestion_status import INGESTION_STATUS_PROCESSING
from app.services.ingestion_status import INGESTION_STATUS_QUEUED
from app.services.processing_queue import (
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    JOB_STATUS_PROCESSING,
    JOB_STATUS_QUEUED,
    JOB_TYPE_SOURCE_INGESTION,
    ProcessingQueueError,
    claim_processing_job,
    complete_processing_job,
    fail_processing_job,
    has_active_job,
    transition_job_status,
    validate_enqueue,
)


def _version(ingestion_status: str = INGESTION_STATUS_QUEUED) -> SourceVersion:
    return SourceVersion(
        source_document_id=None,
        version_label="v1",
        checksum_sha256="a" * 64,
        storage_path="rw/vat/v1.pdf",
        ingestion_status=ingestion_status,
    )


def _job(status: str = JOB_STATUS_QUEUED, attempt_count: int = 0, max_attempts: int = 3) -> SourceProcessingJob:
    return SourceProcessingJob(
        source_version_id=None,
        job_type=JOB_TYPE_SOURCE_INGESTION,
        job_status=status,
        attempt_count=attempt_count,
        max_attempts=max_attempts,
    )


def test_validate_enqueue_requires_queued_ingestion_status():
    with pytest.raises(ProcessingQueueError):
        validate_enqueue(_version("not_started"), JOB_TYPE_SOURCE_INGESTION)


def test_has_active_job_detects_queued_or_processing():
    jobs = [
        _job(JOB_STATUS_QUEUED),
        _job(JOB_STATUS_COMPLETED),
    ]
    assert has_active_job(jobs, JOB_TYPE_SOURCE_INGESTION) is True


def test_transition_increments_attempt_count_on_processing():
    job = _job(JOB_STATUS_QUEUED)
    transition_job_status(job, JOB_STATUS_PROCESSING)
    assert job.attempt_count == 1
    assert job.started_at is not None


def test_transition_rejects_retry_when_max_attempts_exceeded():
    job = _job(JOB_STATUS_FAILED, attempt_count=3, max_attempts=3)
    with pytest.raises(ProcessingQueueError):
        transition_job_status(job, JOB_STATUS_QUEUED)


def test_claim_processing_job_sets_lock_and_processing_state():
    job = _job(JOB_STATUS_QUEUED)
    claim_processing_job(job, "worker-1")
    assert job.job_status == JOB_STATUS_PROCESSING
    assert job.attempt_count == 1
    assert job.locked_by == "worker-1"
    assert job.locked_at is not None
    assert job.started_at is not None


def test_claim_processing_job_rejects_non_queued_job():
    job = _job(JOB_STATUS_PROCESSING, attempt_count=1)
    with pytest.raises(ProcessingQueueError):
        claim_processing_job(job, "worker-1")


def _db_with_version(version: SourceVersion) -> MagicMock:
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = version
    return db


def test_complete_processing_job_sets_metadata_and_ingestion_status():
    job = _job(JOB_STATUS_PROCESSING, attempt_count=1)
    version = _version(INGESTION_STATUS_PROCESSING)
    complete_processing_job(
        _db_with_version(version),
        job,
        completed_by="worker-1",
        result_json={"pages": 12},
    )
    assert job.job_status == JOB_STATUS_COMPLETED
    assert job.completed_by == "worker-1"
    assert job.result_json == {"pages": 12}
    assert job.failed_by is None
    assert version.ingestion_status == "parsed"


def test_fail_processing_job_sets_metadata_and_ingestion_status():
    job = _job(JOB_STATUS_PROCESSING, attempt_count=1)
    version = _version(INGESTION_STATUS_PROCESSING)
    fail_processing_job(
        _db_with_version(version),
        job,
        failed_by="worker-1",
        last_error="parser error",
        result_json={"stage": "ocr"},
    )
    assert job.job_status == JOB_STATUS_FAILED
    assert job.failed_by == "worker-1"
    assert job.last_error == "parser error"
    assert version.ingestion_status == "failed"


def test_complete_rejects_non_processing_job():
    job = _job(JOB_STATUS_QUEUED)
    with pytest.raises(ProcessingQueueError):
        complete_processing_job(
            _db_with_version(_version(INGESTION_STATUS_PROCESSING)),
            job,
            completed_by="worker-1",
            result_json={},
        )


def test_transition_completed_sets_completed_at():
    job = _job(JOB_STATUS_PROCESSING, attempt_count=1)
    transition_job_status(job, JOB_STATUS_COMPLETED)
    assert job.job_status == JOB_STATUS_COMPLETED
    assert job.completed_at is not None
