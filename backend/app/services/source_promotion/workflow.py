from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.source_version import SourceVersion
from app.models.source_version_promotion import SourceVersionPromotion
from app.services.source_promotion.errors import SourcePromotionError
from app.services.source_promotion.request import SourceVersionPromotionRequest
from app.services.source_promotion.result import SourceVersionPromotionResult
from app.services.source_promotion.validation import validate_promotion_request


def _build_version_label(request: SourceVersionPromotionRequest) -> str:
    if request.proposed_version_label and request.proposed_version_label.strip():
        return request.proposed_version_label.strip()
    return f"promoted-{utc_now().strftime('%Y%m%d%H%M%S')}"


def _persist_promotion_record(
    session: Session,
    *,
    request: SourceVersionPromotionRequest,
    promotion_status: str,
    checksum_sha256: str | None,
    source_version_id,
    notes: str | None,
) -> SourceVersionPromotion:
    record = SourceVersionPromotion(
        source_version_id=source_version_id,
        source_document_id=request.source_document_id,
        fetch_result_id=request.fetch_result_id,
        monitoring_candidate_id=request.monitoring_candidate_id,
        change_detection_result_id=request.change_detection_result_id,
        promotion_status=promotion_status,
        requested_by_actor_type=request.requested_by_actor_type,
        requested_by_actor_identifier=request.requested_by_actor_identifier,
        promotion_reason=request.promotion_reason,
        checksum_sha256=checksum_sha256,
        created_at=utc_now(),
        completed_at=utc_now(),
        notes=notes,
    )
    session.add(record)
    session.flush()
    return record


def promote_source_version(
    session: Session,
    *,
    request: SourceVersionPromotionRequest,
) -> SourceVersionPromotionResult:
    validation = validate_promotion_request(session, request=request)
    checksum = validation.fetch_result.checksum_sha256 if validation.fetch_result is not None else None

    if validation.validation_errors:
        if validation.fetch_result is not None and validation.source_document is not None:
            _persist_promotion_record(
                session,
                request=request,
                promotion_status="rejected",
                checksum_sha256=checksum,
                source_version_id=None,
                notes=request.notes,
            )
        return SourceVersionPromotionResult(
            source_version_id=None,
            promotion_status="rejected",
            review_required=True,
            validation_errors=validation.validation_errors,
            promoted_at=None,
            source_document_id=request.source_document_id,
            fetch_result_id=request.fetch_result_id,
            checksum_sha256=checksum,
            notes=request.notes,
        )

    if validation.duplicate_source_version is not None:
        _persist_promotion_record(
            session,
            request=request,
            promotion_status="duplicate_rejected",
            checksum_sha256=checksum,
            source_version_id=None,
            notes=request.notes,
        )
        return SourceVersionPromotionResult(
            source_version_id=None,
            promotion_status="duplicate_rejected",
            review_required=False,
            validation_errors=[],
            promoted_at=None,
            source_document_id=request.source_document_id,
            fetch_result_id=request.fetch_result_id,
            checksum_sha256=checksum,
            notes=request.notes,
        )

    try:
        source_version = SourceVersion(
            source_document_id=request.source_document_id,
            version_label=_build_version_label(request),
            publication_date=request.publication_date,
            effective_from=request.effective_from,
            effective_to=request.effective_to,
            enforcement_date=None,
            retrieved_at=validation.fetch_result.fetched_at or utc_now(),
            checksum_sha256=validation.fetch_result.checksum_sha256,  # type: ignore[arg-type]
            storage_path=validation.fetch_result.storage_path,  # type: ignore[arg-type]
            mime_type=validation.fetch_result.content_type,
            file_size=validation.fetch_result.content_length,
            version_status="active",
            notes=(
                f"promoted_from_fetch_result={request.fetch_result_id};"
                f"monitoring_candidate_id={request.monitoring_candidate_id};"
                f"change_detection_result_id={request.change_detection_result_id}"
            ),
            supersedes_version_id=None,
        )
        session.add(source_version)
        session.flush()

        _persist_promotion_record(
            session,
            request=request,
            promotion_status="approved",
            checksum_sha256=source_version.checksum_sha256,
            source_version_id=source_version.id,
            notes=request.notes,
        )
        return SourceVersionPromotionResult(
            source_version_id=source_version.id,
            promotion_status="approved",
            review_required=False,
            validation_errors=[],
            promoted_at=utc_now(),
            source_document_id=request.source_document_id,
            fetch_result_id=request.fetch_result_id,
            checksum_sha256=source_version.checksum_sha256,
            notes=request.notes,
        )
    except Exception as exc:
        _persist_promotion_record(
            session,
            request=request,
            promotion_status="failed",
            checksum_sha256=checksum,
            source_version_id=None,
            notes=f"{request.notes or ''} workflow_error={exc}".strip(),
        )
        raise SourcePromotionError(str(exc)) from exc
