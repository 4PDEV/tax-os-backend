from uuid import UUID

from app.models.extraction_run import ExtractionRun
from app.models.parsed_structure import ParsedStructure
from app.models.parser_run import ParserRun
from app.models.source_version import SourceVersion
from app.services.ingestion.enums import ParserRunStatus

REQUESTED_BY_ACTOR_TYPES = {"user", "system", "worker", "admin", "test"}
PROMOTION_STATUSES = {
    "pending",
    "accepted",
    "rejected",
    "promoted",
    "failed",
    "skipped",
    "duplicate_rejected",
}
PROMOTION_ERROR_CATEGORIES = {
    "parsed_structure_missing",
    "parser_run_incomplete",
    "provenance_incomplete",
    "duplicate_promotion",
    "invalid_request",
    "promotion_pipeline_unavailable",
    "unknown_failure",
}
PARSER_RUN_TERMINAL_SUCCESS_STATUSES = {
    ParserRunStatus.SUCCESS.value,
    ParserRunStatus.PARTIAL.value,
}


def validate_actor_type(actor_type: str) -> None:
    if actor_type not in REQUESTED_BY_ACTOR_TYPES:
        raise ValueError(f"invalid requested_by_actor_type: {actor_type}")


def validate_promotion_status(promotion_status: str) -> None:
    if promotion_status not in PROMOTION_STATUSES:
        raise ValueError(f"invalid promotion_status: {promotion_status}")


def validate_promotion_error_category(error_category: str | None) -> None:
    if error_category is not None and error_category not in PROMOTION_ERROR_CATEGORIES:
        raise ValueError(f"invalid error_category: {error_category}")


def validate_parsed_structure_eligibility(
    parsed_structure: ParsedStructure,
    parser_run: ParserRun | None,
    extraction_run: ExtractionRun | None,
    source_version: SourceVersion | None,
    *,
    source_version_id: UUID | None = None,
) -> None:
    if parser_run is None:
        raise ValueError("parsed_structure_missing")
    if parser_run.parser_status not in PARSER_RUN_TERMINAL_SUCCESS_STATUSES:
        raise ValueError("parser_run_incomplete")
    if extraction_run is None:
        raise ValueError("provenance_incomplete")
    if source_version is None:
        raise ValueError("provenance_incomplete")
    if source_version_id is not None and parsed_structure.source_version_id != source_version_id:
        raise ValueError("provenance_incomplete")
    if not parsed_structure.structure_hash:
        raise ValueError("provenance_incomplete")
