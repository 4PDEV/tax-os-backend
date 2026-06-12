"""Append-only answer persistence (TASK-009B).

Persistence records answer assembly intent, lifecycle, and pure-pointer evidence membership only —
no answer worker, no APIs, no ranking/retrieval execution, no AI.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.answer_evidence_entry import AnswerEvidenceEntry
from app.models.answer_request import AnswerRequest
from app.models.answer_result import AnswerResult
from app.models.answer_uncertainty_flag import AnswerUncertaintyFlag
from app.models.ranked_evidence_reference import RankedEvidenceReference
from app.models.ranking_request import RankingRequest
from app.models.retrieval_evidence_reference import RetrievalEvidenceReference
from app.services.answer_assembly import assemble_answer_package
from app.services.answer_assembly.models import CURRENT_CONTRACT_VERSION as ASSEMBLY_CONTRACT_VERSION
from app.services.answer_assembly.validation import resolve_ranking_assembly_inputs
from app.services.answer_persistence.hashing import (
    CURRENT_CONTRACT_VERSION,
    compute_answer_request_hash,
)
from app.services.answer_persistence.validation import (
    TERMINAL_ANSWER_STATUSES,
    validate_actor_type,
    validate_answer_error_category,
    validate_answer_status,
    validate_uncertainty_flag_type,
    validate_uncertainty_severity,
)


class AnswerPersistenceError(Exception):
    pass


@dataclass(frozen=True)
class AnswerPersistenceOutcome:
    answer_request_id: UUID
    answer_result_id: UUID
    answer_status: str
    rank_count: int | None = None
    error_category: str | None = None
    error_message: str | None = None


def find_existing_default_request(
    session: Session,
    *,
    answer_request_hash: str,
) -> AnswerRequest | None:
    return session.execute(
        select(AnswerRequest)
        .where(
            AnswerRequest.answer_request_hash == answer_request_hash,
            AnswerRequest.force_replay.is_(False),
        )
        .order_by(AnswerRequest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def _validate_ranked_membership_v_b_02(
    session: Session,
    *,
    ranked_evidence_reference_id: UUID,
    accepted_ranking_result_id: UUID,
    retrieval_result_id: UUID,
    retrieval_evidence_reference_id: UUID,
) -> RankedEvidenceReference:
    ranked = session.get(RankedEvidenceReference, ranked_evidence_reference_id)
    if ranked is None:
        raise AnswerPersistenceError(
            f"ranked_evidence_reference not found: {ranked_evidence_reference_id}"
        )
    if ranked.ranking_result_id != accepted_ranking_result_id:
        raise AnswerPersistenceError("ranked_evidence_parent_mismatch")
    if ranked.retrieval_result_id != retrieval_result_id:
        raise AnswerPersistenceError("ranked_retrieval_result_mismatch")
    if ranked.retrieval_evidence_reference_id != retrieval_evidence_reference_id:
        raise AnswerPersistenceError("ranked_retrieval_evidence_mismatch")
    return ranked


def create_answer_request(
    session: Session,
    *,
    ranking_request_id: UUID,
    requested_by_actor_type: str,
    contract_version: str = CURRENT_CONTRACT_VERSION,
    assembly_contract_version: str = ASSEMBLY_CONTRACT_VERSION,
    include_rendered_citation_text: bool = False,
    requested_by_actor_identifier: str | None = None,
    requested_at: datetime | None = None,
    force_replay: bool = False,
    notes: str | None = None,
    replay_nonce: str | None = None,
) -> AnswerRequest:
    try:
        validate_actor_type(requested_by_actor_type)
    except ValueError as exc:
        raise AnswerPersistenceError(str(exc)) from exc

    ranking_request = session.get(RankingRequest, ranking_request_id)
    if ranking_request is None:
        raise AnswerPersistenceError(f"ranking_request not found: {ranking_request_id}")

    answer_request_hash = compute_answer_request_hash(
        ranking_request_id=ranking_request_id,
        contract_version=contract_version,
        assembly_contract_version=assembly_contract_version,
        include_rendered_citation_text=include_rendered_citation_text,
        force_replay=force_replay,
        replay_nonce=replay_nonce,
    )

    if not force_replay:
        existing = find_existing_default_request(session, answer_request_hash=answer_request_hash)
        if existing is not None:
            raise AnswerPersistenceError("duplicate_default_request_for_hash")

    request = AnswerRequest(
        answer_request_hash=answer_request_hash,
        ranking_request_id=ranking_request_id,
        contract_version=contract_version,
        assembly_contract_version=assembly_contract_version,
        include_rendered_citation_text=include_rendered_citation_text,
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


def create_answer_result(
    session: Session,
    *,
    answer_request_id: UUID,
    ranking_request_id: UUID,
    retrieval_result_id: UUID,
    answer_status: str,
    rank_count: int | None = None,
    completed_at: datetime | None = None,
    error_category: str | None = None,
    error_message: str | None = None,
    notes: str | None = None,
    accepted_ranking_result_id: UUID | None = None,
    terminal_ranking_result_id: UUID | None = None,
) -> AnswerResult:
    try:
        validate_answer_status(answer_status)
        validate_answer_error_category(error_category)
    except ValueError as exc:
        raise AnswerPersistenceError(str(exc)) from exc

    request = session.get(AnswerRequest, answer_request_id)
    if request is None:
        raise AnswerPersistenceError(f"answer_request not found: {answer_request_id}")

    ranking_request = session.get(RankingRequest, ranking_request_id)
    if ranking_request is None:
        raise AnswerPersistenceError(f"ranking_request not found: {ranking_request_id}")

    if request.ranking_request_id != ranking_request_id:
        raise AnswerPersistenceError("answer_request_ranking_request_mismatch")

    if ranking_request.retrieval_result_id != retrieval_result_id:
        raise AnswerPersistenceError("ranking_request_retrieval_result_mismatch")

    result = AnswerResult(
        answer_request_id=answer_request_id,
        ranking_request_id=ranking_request_id,
        retrieval_result_id=retrieval_result_id,
        accepted_ranking_result_id=accepted_ranking_result_id,
        terminal_ranking_result_id=terminal_ranking_result_id,
        answer_status=answer_status,
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


def create_answer_evidence_entry(
    session: Session,
    *,
    answer_result_id: UUID,
    answer_request_id: UUID,
    ranking_request_id: UUID,
    ranked_evidence_reference_id: UUID,
    retrieval_result_id: UUID,
    retrieval_evidence_reference_id: UUID,
    presentation_order_index: int,
    accepted_ranking_result_id: UUID,
) -> AnswerEvidenceEntry:
    if presentation_order_index < 1:
        raise AnswerPersistenceError("invalid_presentation_order_index")

    answer_result = session.get(AnswerResult, answer_result_id)
    if answer_result is None:
        raise AnswerPersistenceError(f"answer_result not found: {answer_result_id}")

    if answer_result.answer_status != "accepted":
        raise AnswerPersistenceError("evidence_must_attach_to_accepted_result")

    _validate_ranked_membership_v_b_02(
        session,
        ranked_evidence_reference_id=ranked_evidence_reference_id,
        accepted_ranking_result_id=accepted_ranking_result_id,
        retrieval_result_id=retrieval_result_id,
        retrieval_evidence_reference_id=retrieval_evidence_reference_id,
    )

    evidence = session.get(RetrievalEvidenceReference, retrieval_evidence_reference_id)
    if evidence is None:
        raise AnswerPersistenceError(
            f"retrieval_evidence_reference not found: {retrieval_evidence_reference_id}"
        )
    if evidence.retrieval_result_id != retrieval_result_id:
        raise AnswerPersistenceError("evidence_reference_retrieval_result_mismatch")

    entry = AnswerEvidenceEntry(
        answer_result_id=answer_result_id,
        answer_request_id=answer_request_id,
        ranking_request_id=ranking_request_id,
        ranked_evidence_reference_id=ranked_evidence_reference_id,
        retrieval_result_id=retrieval_result_id,
        retrieval_evidence_reference_id=retrieval_evidence_reference_id,
        presentation_order_index=presentation_order_index,
        created_at=utc_now(),
    )
    session.add(entry)
    session.flush()
    return entry


def create_answer_uncertainty_flag(
    session: Session,
    *,
    answer_result_id: UUID,
    flag_type: str,
    severity: str,
    message: str,
    related_retrieval_evidence_reference_id: UUID | None = None,
) -> AnswerUncertaintyFlag:
    try:
        validate_uncertainty_flag_type(flag_type)
        validate_uncertainty_severity(severity)
    except ValueError as exc:
        raise AnswerPersistenceError(str(exc)) from exc

    answer_result = session.get(AnswerResult, answer_result_id)
    if answer_result is None:
        raise AnswerPersistenceError(f"answer_result not found: {answer_result_id}")

    if answer_result.answer_status != "accepted":
        raise AnswerPersistenceError("uncertainty_must_attach_to_accepted_result")

    if related_retrieval_evidence_reference_id is not None:
        evidence = session.get(
            RetrievalEvidenceReference,
            related_retrieval_evidence_reference_id,
        )
        if evidence is None:
            raise AnswerPersistenceError(
                "related_retrieval_evidence_reference not found: "
                f"{related_retrieval_evidence_reference_id}"
            )

    flag = AnswerUncertaintyFlag(
        answer_result_id=answer_result_id,
        flag_type=flag_type,
        severity=severity,
        message=message,
        related_retrieval_evidence_reference_id=related_retrieval_evidence_reference_id,
        created_at=utc_now(),
    )
    session.add(flag)
    session.flush()
    return flag


def get_answer_request(
    session: Session,
    *,
    answer_request_id: UUID,
) -> AnswerRequest | None:
    return session.get(AnswerRequest, answer_request_id)


def get_answer_result(
    session: Session,
    *,
    answer_result_id: UUID,
) -> AnswerResult | None:
    return session.get(AnswerResult, answer_result_id)


def list_results_for_request(
    session: Session,
    *,
    answer_request_id: UUID,
) -> list[AnswerResult]:
    return (
        session.execute(
            select(AnswerResult)
            .where(AnswerResult.answer_request_id == answer_request_id)
            .order_by(AnswerResult.created_at.asc())
        )
        .scalars()
        .all()
    )


def list_evidence_entries_for_result(
    session: Session,
    *,
    answer_result_id: UUID,
) -> list[AnswerEvidenceEntry]:
    return (
        session.execute(
            select(AnswerEvidenceEntry)
            .where(AnswerEvidenceEntry.answer_result_id == answer_result_id)
            .order_by(AnswerEvidenceEntry.presentation_order_index.asc())
        )
        .scalars()
        .all()
    )


def list_uncertainty_flags_for_result(
    session: Session,
    *,
    answer_result_id: UUID,
) -> list[AnswerUncertaintyFlag]:
    return (
        session.execute(
            select(AnswerUncertaintyFlag)
            .where(AnswerUncertaintyFlag.answer_result_id == answer_result_id)
            .order_by(AnswerUncertaintyFlag.created_at.asc())
        )
        .scalars()
        .all()
    )


def _check_duplicate_before_request(
    session: Session,
    *,
    ranking_request_id: UUID,
    contract_version: str,
    assembly_contract_version: str,
    include_rendered_citation_text: bool,
) -> AnswerRequest | None:
    answer_request_hash = compute_answer_request_hash(
        ranking_request_id=ranking_request_id,
        contract_version=contract_version,
        assembly_contract_version=assembly_contract_version,
        include_rendered_citation_text=include_rendered_citation_text,
        force_replay=False,
    )
    existing = find_existing_default_request(session, answer_request_hash=answer_request_hash)
    if existing is None:
        return None

    results = list_results_for_request(session, answer_request_id=existing.id)
    if results:
        latest = results[-1]
        if latest.answer_status == "accepted":
            raise AnswerPersistenceError("in_flight_accepted_answer_result")
        if latest.answer_status in TERMINAL_ANSWER_STATUSES:
            return existing
    return existing


def persist_answer_for_ranking_request(
    session: Session,
    *,
    ranking_request_id: UUID,
    contract_version: str = CURRENT_CONTRACT_VERSION,
    assembly_contract_version: str = ASSEMBLY_CONTRACT_VERSION,
    include_rendered_citation_text: bool = False,
    force_replay: bool = False,
    replay_nonce: str | None = None,
    requested_by_actor_type: str = "worker",
    requested_by_actor_identifier: str | None = None,
    notes: str | None = None,
) -> AnswerPersistenceOutcome:
    """Option A orchestration: request → accepted → assemble → children → terminal."""
    try:
        inputs = resolve_ranking_assembly_inputs(session, ranking_request_id=ranking_request_id)
    except Exception as exc:
        raise AnswerPersistenceError(f"ranking_request_missing: {exc}") from exc

    ranking_request = inputs.ranking_request
    retrieval_result_id = ranking_request.retrieval_result_id
    accepted_ranking_result_id = inputs.accepted_ranking_result.id
    terminal_ranking_result_id = inputs.terminal_ranking_result.id

    if not force_replay:
        existing = _check_duplicate_before_request(
            session,
            ranking_request_id=ranking_request_id,
            contract_version=contract_version,
            assembly_contract_version=assembly_contract_version,
            include_rendered_citation_text=include_rendered_citation_text,
        )
        if existing is not None:
            rejected = create_answer_result(
                session,
                answer_request_id=existing.id,
                ranking_request_id=ranking_request_id,
                retrieval_result_id=retrieval_result_id,
                answer_status="duplicate_rejected",
                error_category="duplicate_answer",
                error_message="duplicate_default_request_for_hash",
                completed_at=utc_now(),
                accepted_ranking_result_id=accepted_ranking_result_id,
                terminal_ranking_result_id=terminal_ranking_result_id,
            )
            session.commit()
            return AnswerPersistenceOutcome(
                answer_request_id=existing.id,
                answer_result_id=rejected.id,
                answer_status="duplicate_rejected",
                error_category="duplicate_answer",
                error_message="duplicate_default_request_for_hash",
            )

    try:
        answer_request = create_answer_request(
            session,
            ranking_request_id=ranking_request_id,
            contract_version=contract_version,
            assembly_contract_version=assembly_contract_version,
            include_rendered_citation_text=include_rendered_citation_text,
            requested_by_actor_type=requested_by_actor_type,
            requested_by_actor_identifier=requested_by_actor_identifier,
            force_replay=force_replay,
            notes=notes,
            replay_nonce=replay_nonce,
        )
    except AnswerPersistenceError as exc:
        if "duplicate_default_request_for_hash" in str(exc):
            raise AnswerPersistenceError("duplicate_answer") from exc
        raise

    accepted = create_answer_result(
        session,
        answer_request_id=answer_request.id,
        ranking_request_id=ranking_request_id,
        retrieval_result_id=retrieval_result_id,
        answer_status="accepted",
    )

    assembly_outcome = assemble_answer_package(
        session,
        ranking_request_id=ranking_request_id,
        contract_version=assembly_contract_version,
        include_rendered_citation_text=include_rendered_citation_text,
    )

    if assembly_outcome.answer_status == "failed":
        failed = create_answer_result(
            session,
            answer_request_id=answer_request.id,
            ranking_request_id=ranking_request_id,
            retrieval_result_id=retrieval_result_id,
            answer_status="failed",
            error_category=assembly_outcome.error_category,
            error_message=assembly_outcome.error_message,
            completed_at=utc_now(),
            accepted_ranking_result_id=accepted_ranking_result_id,
            terminal_ranking_result_id=terminal_ranking_result_id,
        )
        session.commit()
        return AnswerPersistenceOutcome(
            answer_request_id=answer_request.id,
            answer_result_id=failed.id,
            answer_status="failed",
            rank_count=0,
            error_category=assembly_outcome.error_category,
            error_message=assembly_outcome.error_message,
        )

    package = assembly_outcome.answer_package
    assert package is not None

    for entry in package.evidence_entries:
        create_answer_evidence_entry(
            session,
            answer_result_id=accepted.id,
            answer_request_id=answer_request.id,
            ranking_request_id=ranking_request_id,
            ranked_evidence_reference_id=entry.ranked_evidence_reference_id,
            retrieval_result_id=entry.retrieval_result_id,
            retrieval_evidence_reference_id=entry.retrieval_evidence_reference_id,
            presentation_order_index=entry.presentation_order_index,
            accepted_ranking_result_id=accepted_ranking_result_id,
        )

    for flag in package.uncertainty_flags:
        related_id = flag.related_evidence_ids[0] if flag.related_evidence_ids else None
        create_answer_uncertainty_flag(
            session,
            answer_result_id=accepted.id,
            flag_type=flag.flag_type,
            severity=flag.severity,
            message=flag.message,
            related_retrieval_evidence_reference_id=related_id,
        )

    completed = create_answer_result(
        session,
        answer_request_id=answer_request.id,
        ranking_request_id=ranking_request_id,
        retrieval_result_id=retrieval_result_id,
        answer_status="completed",
        rank_count=package.rank_count,
        completed_at=utc_now(),
        accepted_ranking_result_id=accepted_ranking_result_id,
        terminal_ranking_result_id=terminal_ranking_result_id,
    )
    session.commit()
    return AnswerPersistenceOutcome(
        answer_request_id=answer_request.id,
        answer_result_id=completed.id,
        answer_status="completed",
        rank_count=package.rank_count,
    )
