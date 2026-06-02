from app.models.extracted_text import ExtractedText
from app.models.parsing_trigger_request import ParsingTriggerRequest
from app.services.ingestion.enums import ParserRunStatus
from app.workers.parsing.result import ParsingProviderResult
from app.workers.parsing.structural import (
    CONTROLLED_STRUCTURAL_PARSER_NAME,
    CONTROLLED_STRUCTURAL_PARSER_VERSION,
    segment_extracted_text_structurally,
)


class ControlledStructuralParsingProvider:
    """Structural segmentation from extracted_text only — no network, files, OCR, or AI."""

    def run_parsing(
        self,
        extracted_text: ExtractedText,
        trigger_request: ParsingTriggerRequest,
    ) -> ParsingProviderResult:
        _ = trigger_request
        try:
            units, envelope = segment_extracted_text_structurally(extracted_text.raw_text)
            return ParsingProviderResult(
                success=True,
                parser_status=ParserRunStatus.SUCCESS.value,
                structure_units=units,
                structure_envelope=envelope,
                notes="controlled structural parsing from extracted_text",
                parser_name=CONTROLLED_STRUCTURAL_PARSER_NAME,
                parser_version=CONTROLLED_STRUCTURAL_PARSER_VERSION,
            )
        except ValueError as exc:
            return ParsingProviderResult(
                success=False,
                error_category=str(exc),
                error_message=str(exc),
                parser_name=CONTROLLED_STRUCTURAL_PARSER_NAME,
                parser_version=CONTROLLED_STRUCTURAL_PARSER_VERSION,
            )
        except Exception as exc:
            return ParsingProviderResult(
                success=False,
                error_category="unknown_failure",
                error_message=str(exc),
                parser_name=CONTROLLED_STRUCTURAL_PARSER_NAME,
                parser_version=CONTROLLED_STRUCTURAL_PARSER_VERSION,
            )
