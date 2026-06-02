from app.models.source_version import SourceVersion

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
    "source_version_missing",
    "source_version_not_eligible",
    "provenance_missing",
    "extraction_already_completed",
    "unsupported_source_type",
    "extraction_pipeline_unavailable",
    "invalid_request",
    "unknown_failure",
}


def validate_actor_type(actor_type: str) -> None:
    if actor_type not in REQUESTED_BY_ACTOR_TYPES:
        raise ValueError(f"invalid requested_by_actor_type: {actor_type}")


def validate_trigger_status(trigger_status: str) -> None:
    if trigger_status not in TRIGGER_STATUSES:
        raise ValueError(f"invalid trigger_status: {trigger_status}")


def validate_trigger_error_category(error_category: str | None) -> None:
    if error_category is not None and error_category not in TRIGGER_ERROR_CATEGORIES:
        raise ValueError(f"invalid error_category: {error_category}")


def validate_source_version_eligibility(version: SourceVersion) -> None:
    # Keep eligibility minimal and explicit for TASK-006N.
    if version.version_status in {"archived", "rejected"}:
        raise ValueError(f"source_version_not_eligible: {version.version_status}")
