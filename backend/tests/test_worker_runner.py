import pytest

from app.models.country import Country
from app.models.source_document import SourceDocument
from app.models.source_processing_job import SourceProcessingJob
from app.models.source_version import SourceVersion
from app.models.tax_type import TaxType
from app.services.ingestion_status import INGESTION_STATUS_QUEUED
from app.services.processing_queue import JOB_STATUS_COMPLETED, JOB_STATUS_FAILED, JOB_STATUS_QUEUED
from app.storage.checksum import sha256_bytes
from app.storage.local import LocalFileStorage
from app.workers import OUTCOME_COMPLETED, OUTCOME_FAILED, OUTCOME_NO_JOB, NoopProcessor, run_next_job_once

pytestmark = pytest.mark.integration


def _seed_queued_job(db_session, storage_root, *, content: bytes = b"worker harness content"):
    country = Country(code="RW", name="Rwanda", status="active")
    db_session.add(country)
    db_session.flush()

    tax_type = TaxType(country_id=country.id, code="VAT", name="VAT", status="active")
    db_session.add(tax_type)
    db_session.flush()

    document = SourceDocument(
        country_id=country.id,
        tax_type_id=tax_type.id,
        source_type="law",
        authority_level="national",
        title="VAT Law",
        status="active",
    )
    db_session.add(document)
    db_session.flush()

    checksum = sha256_bytes(content)
    version = SourceVersion(
        source_document_id=document.id,
        version_label="v1",
        checksum_sha256=checksum,
        storage_path="rw/vat/worker.pdf",
        mime_type="application/pdf",
        file_size=len(content),
        ingestion_status=INGESTION_STATUS_QUEUED,
    )
    db_session.add(version)
    db_session.flush()

    storage = LocalFileStorage(storage_root)
    storage.save_bytes("rw/vat/worker.pdf", content)

    job = SourceProcessingJob(
        source_version_id=version.id,
        job_type="source_ingestion",
        job_status=JOB_STATUS_QUEUED,
    )
    db_session.add(job)
    db_session.flush()
    return job, version


def test_run_next_job_once_completes_lifecycle(db_session, tmp_path):
    job, version = _seed_queued_job(db_session, tmp_path)

    result = run_next_job_once(
        db_session, worker_id="noop-worker-1", processor=NoopProcessor(), commit=False
    )

    assert result.outcome == OUTCOME_COMPLETED
    assert result.job is not None
    assert result.job.id == job.id
    assert result.job.job_status == JOB_STATUS_COMPLETED
    assert result.job.completed_by == "noop-worker-1"
    assert result.job.result_json["processor"] == "noop"

    db_session.refresh(version)
    assert version.ingestion_status == "parsed"


def test_run_next_job_once_fails_when_processor_reports_failure(db_session, tmp_path):
    job, version = _seed_queued_job(db_session, tmp_path, content=b"worker failure content")

    result = run_next_job_once(
        db_session,
        worker_id="noop-worker-fail",
        processor=NoopProcessor(should_fail=True, error_message="deterministic noop failure"),
        commit=False,
    )

    assert result.outcome == OUTCOME_FAILED
    assert result.job is not None
    assert result.job.id == job.id
    assert result.job.job_status == JOB_STATUS_FAILED
    assert result.job.failed_by == "noop-worker-fail"
    assert result.job.last_error == "deterministic noop failure"

    db_session.refresh(version)
    assert version.ingestion_status == "failed"


def test_run_next_job_once_returns_no_job_when_queue_empty(db_session):
    result = run_next_job_once(
        db_session, worker_id="noop-worker-idle", processor=NoopProcessor(), commit=False
    )

    assert result.outcome == OUTCOME_NO_JOB
    assert result.job is None
