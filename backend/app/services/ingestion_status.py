from app.models.source_version import SourceVersion

INGESTION_STATUS_NOT_STARTED = "not_started"
INGESTION_STATUS_QUEUED = "queued"
INGESTION_STATUS_PROCESSING = "processing"
INGESTION_STATUS_PARSED = "parsed"
INGESTION_STATUS_FAILED = "failed"
INGESTION_STATUS_SUPERSEDED = "superseded"

INGESTION_STATUSES = frozenset(
    {
        INGESTION_STATUS_NOT_STARTED,
        INGESTION_STATUS_QUEUED,
        INGESTION_STATUS_PROCESSING,
        INGESTION_STATUS_PARSED,
        INGESTION_STATUS_FAILED,
        INGESTION_STATUS_SUPERSEDED,
    }
)

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    INGESTION_STATUS_NOT_STARTED: frozenset({INGESTION_STATUS_QUEUED, INGESTION_STATUS_SUPERSEDED}),
    INGESTION_STATUS_QUEUED: frozenset({INGESTION_STATUS_PROCESSING, INGESTION_STATUS_SUPERSEDED}),
    INGESTION_STATUS_PROCESSING: frozenset(
        {INGESTION_STATUS_PARSED, INGESTION_STATUS_FAILED, INGESTION_STATUS_SUPERSEDED}
    ),
    INGESTION_STATUS_FAILED: frozenset({INGESTION_STATUS_QUEUED, INGESTION_STATUS_SUPERSEDED}),
    INGESTION_STATUS_PARSED: frozenset({INGESTION_STATUS_SUPERSEDED}),
    INGESTION_STATUS_SUPERSEDED: frozenset(),
}


class IngestionStatusError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def validate_ingestion_status(status: str) -> None:
    if status not in INGESTION_STATUSES:
        raise IngestionStatusError(f"invalid ingestion status: {status}")


def validate_transition(current_status: str, target_status: str) -> None:
    validate_ingestion_status(current_status)
    validate_ingestion_status(target_status)

    if current_status == target_status:
        raise IngestionStatusError(
            f"ingestion status is already {current_status}"
        )

    allowed = ALLOWED_TRANSITIONS[current_status]
    if target_status not in allowed:
        raise IngestionStatusError(
            f"transition from {current_status} to {target_status} is not allowed"
        )


def transition_ingestion_status(version: SourceVersion, target_status: str) -> SourceVersion:
    validate_transition(version.ingestion_status, target_status)
    version.ingestion_status = target_status
    return version
