from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.change_detection_result import ChangeDetectionResult
from app.models.fetch_result import FetchResult
from app.models.monitoring_candidate import MonitoringCandidate
from app.models.source_document import SourceDocument
from app.models.source_version import SourceVersion
from app.services.source_promotion.request import SourceVersionPromotionRequest

REQUESTED_BY_ACTOR_TYPES = {"user", "system", "worker", "admin", "test"}


@dataclass
class PromotionValidationContext:
    fetch_result: FetchResult | None
    source_document: SourceDocument | None
    monitoring_candidate: MonitoringCandidate | None
    change_detection_result: ChangeDetectionResult | None
    duplicate_source_version: SourceVersion | None
    validation_errors: list[str]


def validate_promotion_request(
    session: Session,
    *,
    request: SourceVersionPromotionRequest,
) -> PromotionValidationContext:
    errors: list[str] = []

    fetch_result = session.get(FetchResult, request.fetch_result_id)
    source_document = session.get(SourceDocument, request.source_document_id)
    monitoring_candidate = None
    change_detection_result = None

    if request.requested_by_actor_type not in REQUESTED_BY_ACTOR_TYPES:
        errors.append(f"invalid requested_by_actor_type: {request.requested_by_actor_type}")
    if not request.promotion_reason or not request.promotion_reason.strip():
        errors.append("promotion_reason is required")

    if fetch_result is None:
        errors.append("fetch_result not found")
    elif fetch_result.fetch_status != "success":
        errors.append("fetch_result must be successful for promotion")
    elif not fetch_result.checksum_sha256:
        errors.append("checksum is required for promotion")
    elif not fetch_result.storage_path:
        errors.append("fetch_result storage_path is required for source_version creation")

    if source_document is None:
        errors.append("source_document not found")

    if request.monitoring_candidate_id is not None:
        monitoring_candidate = session.get(MonitoringCandidate, request.monitoring_candidate_id)
        if monitoring_candidate is None:
            errors.append("monitoring_candidate not found")

    if request.change_detection_result_id is not None:
        change_detection_result = session.get(ChangeDetectionResult, request.change_detection_result_id)
        if change_detection_result is None:
            errors.append("change_detection_result not found")

    if request.effective_from and request.effective_to and request.effective_to < request.effective_from:
        errors.append("effective_to cannot be earlier than effective_from")

    duplicate_source_version = None
    if fetch_result is not None and source_document is not None and fetch_result.checksum_sha256:
        duplicate_source_version = session.execute(
            select(SourceVersion).where(
                SourceVersion.source_document_id == source_document.id,
                SourceVersion.checksum_sha256 == fetch_result.checksum_sha256,
            )
        ).scalar_one_or_none()

    return PromotionValidationContext(
        fetch_result=fetch_result,
        source_document=source_document,
        monitoring_candidate=monitoring_candidate,
        change_detection_result=change_detection_result,
        duplicate_source_version=duplicate_source_version,
        validation_errors=errors,
    )
