from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.extraction_run import ExtractionRun
from app.models.legal_object import LegalObject
from app.models.legal_object_promotion_request import LegalObjectPromotionRequest
from app.models.legal_object_promotion_result import LegalObjectPromotionResult
from app.models.parsed_structure import ParsedStructure
from app.models.parser_run import ParserRun
from app.models.source_version import SourceVersion
from app.services.legal_object_promotion.hashing import compute_promotion_hash
from app.services.legal_object_promotion.validation import (
    validate_actor_type,
    validate_parsed_structure_eligibility,
    validate_promotion_error_category,
    validate_promotion_status,
)


class LegalObjectPromotionPersistenceError(Exception):
    pass


def find_existing_default_promotion(
    session: Session,
    *,
    parsed_structure_id: UUID,
) -> LegalObjectPromotionRequest | None:
    return session.execute(
        select(LegalObjectPromotionRequest)
        .where(
            LegalObjectPromotionRequest.parsed_structure_id == parsed_structure_id,
            LegalObjectPromotionRequest.force_repromotion.is_(False),
        )
        .order_by(LegalObjectPromotionRequest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def create_promotion_request(
    session: Session,
    *,
    parsed_structure_id: UUID,
    source_version_id: UUID,
    requested_by_actor_type: str,
    promotion_reason: str,
    requested_by_actor_identifier: str | None = None,
    requested_at: datetime | None = None,
    force_repromotion: bool = False,
    notes: str | None = None,
) -> LegalObjectPromotionRequest:
    validate_actor_type(requested_by_actor_type)
    if not promotion_reason or not promotion_reason.strip():
        raise LegalObjectPromotionPersistenceError("invalid_request")

    parsed_structure = session.get(ParsedStructure, parsed_structure_id)
    if parsed_structure is None:
        raise LegalObjectPromotionPersistenceError("parsed_structure_missing")

    source_version = session.get(SourceVersion, source_version_id)
    if source_version is None:
        raise LegalObjectPromotionPersistenceError("provenance_incomplete")

    parser_run = session.get(ParserRun, parsed_structure.parser_run_id)
    extraction_run = (
        session.get(ExtractionRun, parser_run.extraction_run_id) if parser_run is not None else None
    )
    try:
        validate_parsed_structure_eligibility(
            parsed_structure,
            parser_run,
            extraction_run,
            source_version,
            source_version_id=source_version_id,
        )
    except ValueError as exc:
        raise LegalObjectPromotionPersistenceError(str(exc)) from exc

    if not force_repromotion:
        existing_default = find_existing_default_promotion(
            session, parsed_structure_id=parsed_structure_id
        )
        if existing_default is not None:
            raise LegalObjectPromotionPersistenceError(
                "duplicate_default_promotion_for_parsed_structure"
            )

    promotion_hash = compute_promotion_hash(
        parsed_structure_id=parsed_structure_id,
        force_repromotion=force_repromotion,
    )

    request = LegalObjectPromotionRequest(
        parsed_structure_id=parsed_structure_id,
        source_version_id=source_version_id,
        promotion_reason=promotion_reason.strip(),
        requested_by_actor_type=requested_by_actor_type,
        requested_by_actor_identifier=requested_by_actor_identifier,
        requested_at=requested_at or utc_now(),
        force_repromotion=force_repromotion,
        promotion_hash=promotion_hash,
        notes=notes,
        created_at=utc_now(),
    )
    session.add(request)
    session.flush()
    return request


def persist_promotion_result(
    session: Session,
    *,
    legal_object_promotion_request_id: UUID,
    promotion_status: str,
    legal_object_id: str | None = None,
    promoted_at: datetime | None = None,
    error_category: str | None = None,
    error_message: str | None = None,
    notes: str | None = None,
) -> LegalObjectPromotionResult:
    validate_promotion_status(promotion_status)
    validate_promotion_error_category(error_category)

    request = session.get(LegalObjectPromotionRequest, legal_object_promotion_request_id)
    if request is None:
        raise LegalObjectPromotionPersistenceError(
            f"legal_object_promotion_request not found: {legal_object_promotion_request_id}"
        )

    if legal_object_id is not None:
        legal_object = session.get(LegalObject, legal_object_id)
        if legal_object is None:
            raise LegalObjectPromotionPersistenceError(
                f"legal_object not found: {legal_object_id}"
            )

    result = LegalObjectPromotionResult(
        legal_object_promotion_request_id=legal_object_promotion_request_id,
        parsed_structure_id=request.parsed_structure_id,
        promotion_status=promotion_status,
        legal_object_id=legal_object_id,
        promoted_at=promoted_at,
        error_category=error_category,
        error_message=error_message,
        notes=notes,
        created_at=utc_now(),
    )
    session.add(result)
    session.flush()
    return result


def get_promotion_request(
    session: Session,
    *,
    legal_object_promotion_request_id: UUID,
) -> LegalObjectPromotionRequest | None:
    return session.get(LegalObjectPromotionRequest, legal_object_promotion_request_id)


def list_results_for_request(
    session: Session,
    *,
    legal_object_promotion_request_id: UUID,
) -> list[LegalObjectPromotionResult]:
    return (
        session.execute(
            select(LegalObjectPromotionResult)
            .where(
                LegalObjectPromotionResult.legal_object_promotion_request_id
                == legal_object_promotion_request_id
            )
            .order_by(LegalObjectPromotionResult.created_at.asc())
        )
        .scalars()
        .all()
    )


def get_latest_result_for_request(
    session: Session,
    *,
    legal_object_promotion_request_id: UUID,
) -> LegalObjectPromotionResult | None:
    return session.execute(
        select(LegalObjectPromotionResult)
        .where(
            LegalObjectPromotionResult.legal_object_promotion_request_id
            == legal_object_promotion_request_id
        )
        .order_by(LegalObjectPromotionResult.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
