from typing import Protocol

from app.models.extraction_trigger_request import ExtractionTriggerRequest
from app.models.source_version import SourceVersion
from app.workers.extraction.result import ExtractionProviderResult


class ExtractionProvider(Protocol):
    def run_extraction(
        self,
        source_version: SourceVersion,
        trigger_request: ExtractionTriggerRequest,
    ) -> ExtractionProviderResult:
        """Return deterministic extraction lifecycle outcome for one trigger."""


class DryRunExtractionProvider:
    """Synthetic provider for internal validation only.

    This provider must never perform network IO, OCR, parsing, or source content extraction.
    """

    def run_extraction(
        self,
        source_version: SourceVersion,
        trigger_request: ExtractionTriggerRequest,
    ) -> ExtractionProviderResult:
        _ = source_version
        return ExtractionProviderResult(
            success=True,
            notes=f"dry-run synthetic extraction for trigger={trigger_request.id}",
        )
