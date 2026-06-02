from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.extraction_trigger_request import ExtractionTriggerRequest
from app.models.extraction_trigger_result import ExtractionTriggerResult
from app.models.source_version import SourceVersion
from app.services.extraction_trigger.hashing import compute_trigger_hash
from app.services.extraction_trigger.validation import (
    validate_actor_type,
    validate_source_version_eligibility,
    validate_trigger_error_category,
    validate_trigger_status,
)


class ExtractionTriggerPersistenceError(Exception):
    pass


def find_existing_trigger_by_hash(
    session: Session,
    *,
    trigger_hash: str,
) -> ExtractionTriggerRequest | None:
    return session.execute(
        select(ExtractionTriggerRequest)
        .where(ExtractionTriggerRequest.trigger_hash == trigger_hash)
        .order_by(ExtractionTriggerRequest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def find_default_trigger_for_source_version(
    session: Session,
    *,
    source_version_id: UUID,
) -> ExtractionTriggerRequest | None:
    return session.execute(
        select(ExtractionTriggerRequest)
        .where(
            ExtractionTriggerRequest.source_version_id == source_version_id,
            ExtractionTriggerRequest.force_reprocess.is_(False),
        )
        .order_by(ExtractionTriggerRequest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def source_version_has_completed_extraction(
    session: Session,
    *,
    source_version_id: UUID,
) -> bool:
    """True when any trigger result for this source_version reached completed status."""
    completed = session.execute(
        select(ExtractionTriggerResult.id)
        .where(
            ExtractionTriggerResult.source_version_id == source_version_id,
            ExtractionTriggerResult.trigger_status == "completed",
        )
        .limit(1)
    ).scalar_one_or_none()
    return completed is not None


def create_extraction_trigger_request(
    session: Session,
    *,
    source_version_id: UUID,
    requested_by_actor_type: str,
    trigger_reason: str,
    requested_by_actor_identifier: str | None = None,
    requested_at: datetime | None = None,
    rerun_allowed: bool = False,
    force_reprocess: bool = False,
    notes: str | None = None,
) -> ExtractionTriggerRequest:
    validate_actor_type(requested_by_actor_type)
    if not trigger_reason or not trigger_reason.strip():
        raise ExtractionTriggerPersistenceError("trigger_reason is required")

    source_version = session.get(SourceVersion, source_version_id)
    if source_version is None:
        raise ExtractionTriggerPersistenceError("source_version_missing")
    try:
        validate_source_version_eligibility(source_version)
    except ValueError as exc:
        raise ExtractionTriggerPersistenceError(str(exc)) from exc

    if not force_reprocess:
        existing_default = find_default_trigger_for_source_version(
            session, source_version_id=source_version_id
        )
        if existing_default is not None:
            raise ExtractionTriggerPersistenceError(
                "duplicate_default_trigger_for_source_version"
            )

    trigger_hash = compute_trigger_hash(
        source_version_id=source_version_id,
        force_reprocess=force_reprocess,
    )

    request = ExtractionTriggerRequest(
        source_version_id=source_version_id,
        requested_by_actor_type=requested_by_actor_type,
        requested_by_actor_identifier=requested_by_actor_identifier,
        trigger_reason=trigger_reason.strip(),
        requested_at=requested_at or utc_now(),
        rerun_allowed=rerun_allowed,
        force_reprocess=force_reprocess,
        trigger_hash=trigger_hash,
        notes=notes,
        created_at=utc_now(),
    )
    session.add(request)
    session.flush()
    return request


def persist_extraction_trigger_result(
    session: Session,
    *,
    extraction_trigger_request_id: UUID,
    trigger_status: str,
    extraction_run_id: UUID | None = None,
    queued_at: datetime | None = None,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    error_category: str | None = None,
    error_message: str | None = None,
    notes: str | None = None,
) -> ExtractionTriggerResult:
    validate_trigger_status(trigger_status)
    validate_trigger_error_category(error_category)

    request = session.get(ExtractionTriggerRequest, extraction_trigger_request_id)
    if request is None:
        raise ExtractionTriggerPersistenceError(
            f"extraction_trigger_request not found: {extraction_trigger_request_id}"
        )

    result = ExtractionTriggerResult(
        extraction_trigger_request_id=extraction_trigger_request_id,
        source_version_id=request.source_version_id,
        trigger_status=trigger_status,
        extraction_run_id=extraction_run_id,
        queued_at=queued_at,
        started_at=started_at,
        completed_at=completed_at,
        error_category=error_category,
        error_message=error_message,
        notes=notes,
        created_at=utc_now(),
    )
    session.add(result)
    session.flush()
    return result


def get_extraction_trigger_request(
    session: Session,
    *,
    extraction_trigger_request_id: UUID,
) -> ExtractionTriggerRequest | None:
    return session.get(ExtractionTriggerRequest, extraction_trigger_request_id)


def list_trigger_results_for_request(
    session: Session,
    *,
    extraction_trigger_request_id: UUID,
) -> list[ExtractionTriggerResult]:
    return (
        session.execute(
            select(ExtractionTriggerResult)
            .where(ExtractionTriggerResult.extraction_trigger_request_id == extraction_trigger_request_id)
            .order_by(ExtractionTriggerResult.created_at.asc())
        )
        .scalars()
        .all()
    )


def get_latest_trigger_result_for_request(
    session: Session,
    *,
    extraction_trigger_request_id: UUID,
) -> ExtractionTriggerResult | None:
    return session.execute(
        select(ExtractionTriggerResult)
        .where(ExtractionTriggerResult.extraction_trigger_request_id == extraction_trigger_request_id)
        .order_by(ExtractionTriggerResult.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
