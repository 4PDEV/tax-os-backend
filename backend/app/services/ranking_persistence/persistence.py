"""Append-only ranking persistence (TASK-008C).

Persistence records ranking intent, lifecycle, and pure-pointer ranked references only —
no ranking execution, no workers, no answer assembly, no AI/semantic ranking.

OD-021: single-worker assumption; concurrent ranking workers not authorized.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.ranked_evidence_reference import RankedEvidenceReference
from app.models.ranking_request import RankingRequest
from app.models.ranking_result import RankingResult
from app.models.retrieval_evidence_reference import RetrievalEvidenceReference
from app.models.retrieval_result import RetrievalResult
from app.services.ranking_persistence.hashing import (
    CURRENT_CONTRACT_VERSION,
    compute_ranking_request_hash,
)
from app.services.ranking_persistence.validation import (
    validate_actor_type,
    validate_ranking_error_category,
    validate_ranking_profile,
    validate_ranking_status,
)


class RankingPersistenceError(Exception):
    pass


def find_existing_default_request(
    session: Session,
    *,
    ranking_request_hash: str,
) -> RankingRequest | None:
    return session.execute(
        select(RankingRequest)
        .where(
            RankingRequest.ranking_request_hash == ranking_request_hash,
            RankingRequest.force_replay.is_(False),
        )
        .order_by(RankingRequest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def create_ranking_request(
    session: Session,
    *,
    retrieval_result_id: UUID,
    ranking_profile: str,
    requested_by_actor_type: str,
    contract_version: str = CURRENT_CONTRACT_VERSION,
    requested_by_actor_identifier: str | None = None,
    requested_at: datetime | None = None,
    force_replay: bool = False,
    notes: str | None = None,
    replay_nonce: str | None = None,
) -> RankingRequest:
    try:
        validate_ranking_profile(ranking_profile)
        validate_actor_type(requested_by_actor_type)
    except ValueError as exc:
        raise RankingPersistenceError(str(exc)) from exc

    retrieval_result = session.get(RetrievalResult, retrieval_result_id)
    if retrieval_result is None:
        raise RankingPersistenceError(f"retrieval_result not found: {retrieval_result_id}")

    ranking_request_hash = compute_ranking_request_hash(
        retrieval_result_id=retrieval_result_id,
        ranking_profile=ranking_profile,
        contract_version=contract_version,
        force_replay=force_replay,
        replay_nonce=replay_nonce,
    )

    if not force_replay:
        existing = find_existing_default_request(session, ranking_request_hash=ranking_request_hash)
        if existing is not None:
            raise RankingPersistenceError("duplicate_default_request_for_hash")

    request = RankingRequest(
        ranking_request_hash=ranking_request_hash,
        retrieval_result_id=retrieval_result_id,
        ranking_profile=ranking_profile,
        contract_version=contract_version,
        requested_by_actor_type=requested_by_actor_type,
        requested_by_actor_identifier=requested_by_actor_identifier,
        requested_at=requested_at or utc_now(),
        force_replay=force_replay,
        notes=notes,
        created_at=utc_now(),
    )
    session.add(request)
    session.flush()
    return request


def create_ranking_result(
    session: Session,
    *,
    ranking_request_id: UUID,
    retrieval_result_id: UUID,
    ranking_status: str,
    rank_count: int | None = None,
    completed_at: datetime | None = None,
    error_category: str | None = None,
    error_message: str | None = None,
    notes: str | None = None,
) -> RankingResult:
    try:
        validate_ranking_status(ranking_status)
        validate_ranking_error_category(error_category)
    except ValueError as exc:
        raise RankingPersistenceError(str(exc)) from exc

    request = session.get(RankingRequest, ranking_request_id)
    if request is None:
        raise RankingPersistenceError(f"ranking_request not found: {ranking_request_id}")

    retrieval_result = session.get(RetrievalResult, retrieval_result_id)
    if retrieval_result is None:
        raise RankingPersistenceError(f"retrieval_result not found: {retrieval_result_id}")

    if request.retrieval_result_id != retrieval_result_id:
        raise RankingPersistenceError("ranking_request_retrieval_result_mismatch")

    result = RankingResult(
        ranking_request_id=ranking_request_id,
        retrieval_result_id=retrieval_result_id,
        ranking_status=ranking_status,
        rank_count=rank_count,
        completed_at=completed_at,
        error_category=error_category,
        error_message=error_message,
        notes=notes,
        created_at=utc_now(),
    )
    session.add(result)
    session.flush()
    return result


def create_ranked_evidence_reference(
    session: Session,
    *,
    ranking_result_id: UUID,
    retrieval_result_id: UUID,
    retrieval_evidence_reference_id: UUID,
    presentation_order_index: int,
) -> RankedEvidenceReference:
    if presentation_order_index < 1:
        raise RankingPersistenceError("invalid_presentation_order_index")

    ranking_result = session.get(RankingResult, ranking_result_id)
    if ranking_result is None:
        raise RankingPersistenceError(f"ranking_result not found: {ranking_result_id}")

    if ranking_result.retrieval_result_id != retrieval_result_id:
        raise RankingPersistenceError("ranking_result_retrieval_result_mismatch")

    evidence = session.get(RetrievalEvidenceReference, retrieval_evidence_reference_id)
    if evidence is None:
        raise RankingPersistenceError(
            f"retrieval_evidence_reference not found: {retrieval_evidence_reference_id}"
        )

    if evidence.retrieval_result_id != retrieval_result_id:
        raise RankingPersistenceError("evidence_reference_retrieval_result_mismatch")

    reference = RankedEvidenceReference(
        ranking_result_id=ranking_result_id,
        retrieval_result_id=retrieval_result_id,
        retrieval_evidence_reference_id=retrieval_evidence_reference_id,
        presentation_order_index=presentation_order_index,
        created_at=utc_now(),
    )
    session.add(reference)
    session.flush()
    return reference


def get_ranking_result(
    session: Session,
    *,
    ranking_result_id: UUID,
) -> RankingResult | None:
    return session.get(RankingResult, ranking_result_id)


def list_results_for_request(
    session: Session,
    *,
    ranking_request_id: UUID,
) -> list[RankingResult]:
    return (
        session.execute(
            select(RankingResult)
            .where(RankingResult.ranking_request_id == ranking_request_id)
            .order_by(RankingResult.created_at.asc())
        )
        .scalars()
        .all()
    )


def list_ranked_evidence_references(
    session: Session,
    *,
    ranking_result_id: UUID,
) -> list[RankedEvidenceReference]:
    return (
        session.execute(
            select(RankedEvidenceReference)
            .where(RankedEvidenceReference.ranking_result_id == ranking_result_id)
            .order_by(RankedEvidenceReference.presentation_order_index.asc())
        )
        .scalars()
        .all()
    )
