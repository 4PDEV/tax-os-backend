from app.models.source_processing_job import SourceProcessingJob
from app.models.source_version import SourceVersion
from app.workers.contract import ProcessingResult

PROCESSOR_NAME = "noop"


class NoopProcessor:
    """Deterministic no-op processor for queue lifecycle verification."""

    def __init__(self, *, should_fail: bool = False, error_message: str = "noop processing failure"):
        self.should_fail = should_fail
        self.error_message = error_message

    def process(self, job: SourceProcessingJob, version: SourceVersion) -> ProcessingResult:
        base_result = {
            "processor": PROCESSOR_NAME,
            "job_id": str(job.id),
            "source_version_id": str(version.id),
            "version_label": version.version_label,
        }
        if self.should_fail:
            return ProcessingResult(
                success=False,
                result_json={**base_result, "outcome": "failed"},
                error_message=self.error_message,
            )
        return ProcessingResult(
            success=True,
            result_json={**base_result, "outcome": "completed"},
        )
