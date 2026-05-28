from dataclasses import dataclass
from typing import Protocol

from app.models.source_processing_job import SourceProcessingJob
from app.models.source_version import SourceVersion


@dataclass(frozen=True)
class ProcessingResult:
    success: bool
    result_json: dict | None = None
    error_message: str | None = None


class SourceJobProcessor(Protocol):
    def process(self, job: SourceProcessingJob, version: SourceVersion) -> ProcessingResult:
        """Execute bounded processing for a claimed job and return a finalization outcome."""
