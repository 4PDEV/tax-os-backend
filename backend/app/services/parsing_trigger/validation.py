from app.models.extracted_text import ExtractedText
from app.models.extraction_run import ExtractionRun

REQUESTED_BY_ACTOR_TYPES = {"user", "system", "worker", "admin", "test"}
TRIGGER_STATUSES = {
    "pending",
    "accepted",
    "rejected",
    "queued",
    "started",
    "completed",
    "failed",
    "skipped",
    "duplicate_rejected",
}
TRIGGER_ERROR_CATEGORIES = {
    "extracted_text_missing",
    "extracted_text_not_eligible",
    "extraction_not_completed",
    "parsing_already_completed",
    "unsupported_content_type",
    "parsing_pipeline_unavailable",
    "invalid_request",
    "unknown_failure",
}
EXTRACTION_TERMINAL_SUCCESS_STATUSES = {"success", "partial"}


def validate_actor_type(actor_type: str) -> None:
    if actor_type not in REQUESTED_BY_ACTOR_TYPES:
        raise ValueError(f"invalid requested_by_actor_type: {actor_type}")


def validate_trigger_status(trigger_status: str) -> None:
    if trigger_status not in TRIGGER_STATUSES:
        raise ValueError(f"invalid trigger_status: {trigger_status}")


def validate_trigger_error_category(error_category: str | None) -> None:
    if error_category is not None and error_category not in TRIGGER_ERROR_CATEGORIES:
        raise ValueError(f"invalid error_category: {error_category}")


def validate_extracted_text_eligibility(
    extracted_text: ExtractedText,
    extraction_run: ExtractionRun | None,
) -> None:
    if extraction_run is None:
        raise ValueError("extracted_text_missing")
    if extraction_run.extraction_status not in EXTRACTION_TERMINAL_SUCCESS_STATUSES:
        raise ValueError("extraction_not_completed")
    if not extracted_text.raw_text or not extracted_text.raw_text.strip():
        raise ValueError("extracted_text_not_eligible")
    if not extracted_text.content_hash:
        raise ValueError("extracted_text_not_eligible")
