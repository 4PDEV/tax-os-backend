from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.change_detection_request import ChangeDetectionRequest
from app.models.change_detection_result import ChangeDetectionResult
from app.models.fetch_result import FetchResult
from app.models.monitoring_candidate import MonitoringCandidate
from app.models.source_document import SourceDocument
from app.models.source_version import SourceVersion

REQUESTED_BY_ACTOR_TYPES = {"user", "system", "worker", "admin", "test"}
DETECTION_STATUSES = {"pending", "completed", "failed", "skipped", "blocked"}
CHANGE_TYPES = {
    "no_change",
    "checksum_changed",
    "metadata_changed",
    "content_changed",
    "structure_changed",
    "removed_or_unavailable",
    "duplicate_detected",
    "new_artifact",
    "unknown",
}
CONFIDENCE_VALUES = {"high", "medium", "low"}
ERROR_CATEGORIES = {
    "missing_previous_artifact",
    "missing_current_artifact",
    "checksum_unavailable",
    "unsupported_content_type",
    "diff_failed",
    "corrupted_artifact",
    "timeout",
    "unknown_failure",
}
REVIEW_REQUIRED_CHANGE_TYPES = {
    "checksum_changed",
    "metadata_changed",
    "content_changed",
    "structure_changed",
    "removed_or_unavailable",
    "new_artifact",
    "unknown",
}


class ChangeDetectionPersistenceError(Exception):
    pass


def _require_non_empty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ChangeDetectionPersistenceError(f"{field_name} is required")


def _validate_actor_type(actor_type: str) -> None:
    if actor_type not in REQUESTED_BY_ACTOR_TYPES:
        raise ChangeDetectionPersistenceError(f"invalid requested_by_actor_type: {actor_type}")


def _validate_detection_status(detection_status: str) -> None:
    if detection_status not in DETECTION_STATUSES:
        raise ChangeDetectionPersistenceError(f"invalid detection_status: {detection_status}")


def _validate_change_type(change_type: str) -> None:
    if change_type not in CHANGE_TYPES:
        raise ChangeDetectionPersistenceError(f"invalid change_type: {change_type}")


def _validate_confidence(confidence: str) -> None:
    if confidence not in CONFIDENCE_VALUES:
        raise ChangeDetectionPersistenceError(f"invalid confidence: {confidence}")


def _validate_error_category(error_category: str | None) -> None:
    if error_category is not None and error_category not in ERROR_CATEGORIES:
        raise ChangeDetectionPersistenceError(f"invalid error_category: {error_category}")


def _validate_review_required_doctrine(change_type: str, review_required: bool) -> None:
    if change_type in REVIEW_REQUIRED_CHANGE_TYPES and not review_required:
        raise ChangeDetectionPersistenceError(
            "review_required must be true for this change_type under TASK-006G doctrine"
        )


def create_change_detection_request(
    session: Session,
    *,
    current_artifact_reference: str,
    requested_by_actor_type: str,
    detection_reason: str,
    previous_artifact_reference: str | None = None,
    requested_by_actor_identifier: str | None = None,
    monitoring_candidate_id: UUID | None = None,
    fetch_result_id: UUID | None = None,
    source_document_id: UUID | None = None,
    source_version_id: UUID | None = None,
    requested_at: datetime | None = None,
    notes: str | None = None,
) -> ChangeDetectionRequest:
    _require_non_empty(current_artifact_reference, "current_artifact_reference")
    _require_non_empty(detection_reason, "detection_reason")
    _validate_actor_type(requested_by_actor_type)

    if monitoring_candidate_id is not None and session.get(MonitoringCandidate, monitoring_candidate_id) is None:
        raise ChangeDetectionPersistenceError(f"monitoring_candidate not found: {monitoring_candidate_id}")
    if fetch_result_id is not None and session.get(FetchResult, fetch_result_id) is None:
        raise ChangeDetectionPersistenceError(f"fetch_result not found: {fetch_result_id}")
    if source_document_id is not None and session.get(SourceDocument, source_document_id) is None:
        raise ChangeDetectionPersistenceError(f"source_document not found: {source_document_id}")
    if source_version_id is not None and session.get(SourceVersion, source_version_id) is None:
        raise ChangeDetectionPersistenceError(f"source_version not found: {source_version_id}")

    request = ChangeDetectionRequest(
        monitoring_candidate_id=monitoring_candidate_id,
        fetch_result_id=fetch_result_id,
        source_document_id=source_document_id,
        source_version_id=source_version_id,
        previous_artifact_reference=previous_artifact_reference,
        current_artifact_reference=current_artifact_reference,
        requested_by_actor_type=requested_by_actor_type,
        requested_by_actor_identifier=requested_by_actor_identifier,
        detection_reason=detection_reason,
        requested_at=requested_at or utc_now(),
        notes=notes,
        created_at=utc_now(),
    )
    session.add(request)
    session.flush()
    return request


def persist_change_detection_result(
    session: Session,
    *,
    change_detection_request_id: UUID,
    detection_status: str,
    change_detected: bool,
    change_type: str,
    previous_checksum_sha256: str | None,
    current_checksum_sha256: str | None,
    metadata_diff_json: dict | None,
    structural_diff_summary: str | None,
    confidence: str,
    review_required: bool,
    detector_name: str,
    detector_version: str,
    detected_at: datetime,
    notes: str | None = None,
    error_category: str | None = None,
    error_message: str | None = None,
) -> ChangeDetectionResult:
    _require_non_empty(detector_name, "detector_name")
    _require_non_empty(detector_version, "detector_version")
    _validate_detection_status(detection_status)
    _validate_change_type(change_type)
    _validate_confidence(confidence)
    _validate_error_category(error_category)
    _validate_review_required_doctrine(change_type, review_required)

    request = session.get(ChangeDetectionRequest, change_detection_request_id)
    if request is None:
        raise ChangeDetectionPersistenceError(
            f"change_detection_request not found: {change_detection_request_id}"
        )

    result = ChangeDetectionResult(
        change_detection_request_id=change_detection_request_id,
        detection_status=detection_status,
        change_detected=change_detected,
        change_type=change_type,
        previous_checksum_sha256=previous_checksum_sha256,
        current_checksum_sha256=current_checksum_sha256,
        metadata_diff_json=metadata_diff_json,
        structural_diff_summary=structural_diff_summary,
        confidence=confidence,
        review_required=review_required,
        detector_name=detector_name,
        detector_version=detector_version,
        detected_at=detected_at,
        notes=notes,
        error_category=error_category,
        error_message=error_message,
        created_at=utc_now(),
    )
    session.add(result)
    session.flush()
    _ = request
    return result


def get_change_detection_request(
    session: Session,
    *,
    change_detection_request_id: UUID,
) -> ChangeDetectionRequest | None:
    return session.get(ChangeDetectionRequest, change_detection_request_id)


def list_change_detection_results_for_request(
    session: Session,
    *,
    change_detection_request_id: UUID,
) -> list[ChangeDetectionResult]:
    return list(
        session.execute(
            select(ChangeDetectionResult)
            .where(ChangeDetectionResult.change_detection_request_id == change_detection_request_id)
            .order_by(ChangeDetectionResult.created_at.asc(), ChangeDetectionResult.id.asc())
        ).scalars()
    )


def get_latest_change_detection_result_for_request(
    session: Session,
    *,
    change_detection_request_id: UUID,
) -> ChangeDetectionResult | None:
    return session.execute(
        select(ChangeDetectionResult)
        .where(ChangeDetectionResult.change_detection_request_id == change_detection_request_id)
        .order_by(ChangeDetectionResult.created_at.desc(), ChangeDetectionResult.id.desc())
        .limit(1)
    ).scalar_one_or_none()
