from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.extracted_text import ExtractedText
from app.models.extraction_run import ExtractionRun
from app.models.parsing_trigger_request import ParsingTriggerRequest
from app.models.parsing_trigger_result import ParsingTriggerResult
from app.models.parser_run import ParserRun
from app.services.parsing_trigger.hashing import compute_trigger_hash
from app.services.parsing_trigger.validation import (
    validate_actor_type,
    validate_extracted_text_eligibility,
    validate_trigger_error_category,
    validate_trigger_status,
)


class ParsingTriggerPersistenceError(Exception):
    pass


def extracted_text_has_completed_parsing(
    session: Session,
    *,
    extracted_text_id: UUID,
) -> bool:
    """True when any trigger result for this extracted_text reached completed status."""
    completed = session.execute(
        select(ParsingTriggerResult.id)
        .where(
            ParsingTriggerResult.extracted_text_id == extracted_text_id,
            ParsingTriggerResult.trigger_status == "completed",
        )
        .limit(1)
    ).scalar_one_or_none()
    return completed is not None


def find_existing_default_trigger_for_extracted_text(
    session: Session,
    *,
    extracted_text_id: UUID,
) -> ParsingTriggerRequest | None:
    return session.execute(
        select(ParsingTriggerRequest)
        .where(
            ParsingTriggerRequest.extracted_text_id == extracted_text_id,
            ParsingTriggerRequest.force_reparse.is_(False),
        )
        .order_by(ParsingTriggerRequest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def create_parsing_trigger_request(
    session: Session,
    *,
    extracted_text_id: UUID,
    requested_by_actor_type: str,
    trigger_reason: str,
    requested_by_actor_identifier: str | None = None,
    requested_at: datetime | None = None,
    rerun_allowed: bool = False,
    force_reparse: bool = False,
    notes: str | None = None,
) -> ParsingTriggerRequest:
    validate_actor_type(requested_by_actor_type)
    if not trigger_reason or not trigger_reason.strip():
        raise ParsingTriggerPersistenceError("invalid_request")

    extracted_text = session.get(ExtractedText, extracted_text_id)
    if extracted_text is None:
        raise ParsingTriggerPersistenceError("extracted_text_missing")

    extraction_run = session.get(ExtractionRun, extracted_text.extraction_run_id)
    try:
        validate_extracted_text_eligibility(extracted_text, extraction_run)
    except ValueError as exc:
        raise ParsingTriggerPersistenceError(str(exc)) from exc

    if not force_reparse:
        existing_default = find_existing_default_trigger_for_extracted_text(
            session, extracted_text_id=extracted_text_id
        )
        if existing_default is not None:
            raise ParsingTriggerPersistenceError(
                "duplicate_default_trigger_for_extracted_text"
            )

    trigger_hash = compute_trigger_hash(
        extracted_text_id=extracted_text_id,
        force_reparse=force_reparse,
    )

    request = ParsingTriggerRequest(
        extracted_text_id=extracted_text_id,
        requested_by_actor_type=requested_by_actor_type,
        requested_by_actor_identifier=requested_by_actor_identifier,
        trigger_reason=trigger_reason.strip(),
        requested_at=requested_at or utc_now(),
        rerun_allowed=rerun_allowed,
        force_reparse=force_reparse,
        trigger_hash=trigger_hash,
        notes=notes,
        created_at=utc_now(),
    )
    session.add(request)
    session.flush()
    return request


def persist_parsing_trigger_result(
    session: Session,
    *,
    parsing_trigger_request_id: UUID,
    trigger_status: str,
    parser_run_id: UUID | None = None,
    queued_at: datetime | None = None,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    error_category: str | None = None,
    error_message: str | None = None,
    notes: str | None = None,
) -> ParsingTriggerResult:
    validate_trigger_status(trigger_status)
    validate_trigger_error_category(error_category)

    request = session.get(ParsingTriggerRequest, parsing_trigger_request_id)
    if request is None:
        raise ParsingTriggerPersistenceError(
            f"parsing_trigger_request not found: {parsing_trigger_request_id}"
        )

    if parser_run_id is not None:
        parser_run = session.get(ParserRun, parser_run_id)
        if parser_run is None:
            raise ParsingTriggerPersistenceError(f"parser_run not found: {parser_run_id}")

    result = ParsingTriggerResult(
        parsing_trigger_request_id=parsing_trigger_request_id,
        extracted_text_id=request.extracted_text_id,
        trigger_status=trigger_status,
        parser_run_id=parser_run_id,
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


def get_parsing_trigger_request(
    session: Session,
    *,
    parsing_trigger_request_id: UUID,
) -> ParsingTriggerRequest | None:
    return session.get(ParsingTriggerRequest, parsing_trigger_request_id)


def list_trigger_results_for_request(
    session: Session,
    *,
    parsing_trigger_request_id: UUID,
) -> list[ParsingTriggerResult]:
    return (
        session.execute(
            select(ParsingTriggerResult)
            .where(ParsingTriggerResult.parsing_trigger_request_id == parsing_trigger_request_id)
            .order_by(ParsingTriggerResult.created_at.asc())
        )
        .scalars()
        .all()
    )


def get_latest_trigger_result_for_request(
    session: Session,
    *,
    parsing_trigger_request_id: UUID,
) -> ParsingTriggerResult | None:
    return session.execute(
        select(ParsingTriggerResult)
        .where(ParsingTriggerResult.parsing_trigger_request_id == parsing_trigger_request_id)
        .order_by(ParsingTriggerResult.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
