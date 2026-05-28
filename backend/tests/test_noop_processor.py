from app.models.source_processing_job import SourceProcessingJob
from app.models.source_version import SourceVersion
from app.workers.noop_processor import NoopProcessor


def _job() -> SourceProcessingJob:
    return SourceProcessingJob(
        source_version_id=None,
        job_type="source_ingestion",
    )


def _version() -> SourceVersion:
    return SourceVersion(
        source_document_id=None,
        version_label="v1",
        checksum_sha256="a" * 64,
        storage_path="rw/vat/v1.pdf",
    )


def test_noop_processor_returns_success_result():
    result = NoopProcessor().process(_job(), _version())
    assert result.success is True
    assert result.error_message is None
    assert result.result_json["processor"] == "noop"
    assert result.result_json["outcome"] == "completed"


def test_noop_processor_returns_failure_result():
    result = NoopProcessor(should_fail=True, error_message="test failure").process(_job(), _version())
    assert result.success is False
    assert result.error_message == "test failure"
    assert result.result_json["outcome"] == "failed"
