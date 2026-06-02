from typing import Protocol

from app.models.extracted_text import ExtractedText
from app.models.parsing_trigger_request import ParsingTriggerRequest
from app.workers.parsing.result import ParsingProviderResult


class ParsingProvider(Protocol):
    def run_parsing(
        self,
        extracted_text: ExtractedText,
        trigger_request: ParsingTriggerRequest,
    ) -> ParsingProviderResult:
        """Return deterministic parsing lifecycle outcome for one trigger."""


class DryRunParsingProvider:
    """Synthetic provider for internal validation only.

    Must never perform real parsing, structural extraction, NLP, or legal interpretation.
    """

    def run_parsing(
        self,
        extracted_text: ExtractedText,
        trigger_request: ParsingTriggerRequest,
    ) -> ParsingProviderResult:
        _ = extracted_text
        return ParsingProviderResult(
            success=True,
            notes=f"dry-run synthetic parsing for trigger={trigger_request.id}",
        )
