from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ChecksumChangeDetectionRequest:
    current_fetch_result_id: UUID
    previous_fetch_result_id: UUID | None
    requested_by_actor_type: str
    requested_by_actor_identifier: str | None
    detection_reason: str
    notes: str | None = None


@dataclass(frozen=True)
class ChangeDetectionEngineResult:
    change_detection_request_id: UUID
    change_detection_result_id: UUID
    change_detected: bool
    change_type: str
    review_required: bool
    confidence: str
    notes: str | None
