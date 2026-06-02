from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.monitoring_candidate import MonitoringCandidate
from app.models.monitoring_candidate_state_transition import MonitoringCandidateStateTransition
from app.services.monitoring.enums import CandidateState
from app.services.monitoring.errors import MonitoringPersistenceError

CANDIDATE_STATES = frozenset(state.value for state in CandidateState)

ALLOWED_CANDIDATE_TRANSITIONS: dict[str, frozenset[str]] = {
    CandidateState.DETECTED.value: frozenset(
        {CandidateState.QUEUED_FOR_REVIEW.value, CandidateState.REJECTED.value, CandidateState.FAILED.value}
    ),
    CandidateState.QUEUED_FOR_REVIEW.value: frozenset(
        {
            CandidateState.REJECTED.value,
            CandidateState.APPROVED_FOR_INGESTION.value,
            CandidateState.SUPERSEDED.value,
            CandidateState.FAILED.value,
        }
    ),
    CandidateState.REJECTED.value: frozenset({CandidateState.SUPERSEDED.value}),
    CandidateState.APPROVED_FOR_INGESTION.value: frozenset({CandidateState.SUPERSEDED.value}),
    CandidateState.FAILED.value: frozenset(
        {CandidateState.QUEUED_FOR_REVIEW.value, CandidateState.REJECTED.value}
    ),
    CandidateState.SUPERSEDED.value: frozenset(),
}


def get_candidate_current_state(session: Session, *, monitoring_candidate_id: UUID) -> str:
    candidate = session.get(MonitoringCandidate, monitoring_candidate_id)
    if candidate is None:
        raise MonitoringPersistenceError(f"monitoring_candidate not found: {monitoring_candidate_id}")
    return candidate.candidate_state


def transition_candidate_state(
    session: Session,
    *,
    monitoring_candidate_id: UUID,
    to_state: str,
    actor_type: str,
    actor_identifier: str | None = None,
    transition_reason: str | None = None,
) -> MonitoringCandidateStateTransition:
    if to_state not in CANDIDATE_STATES:
        raise MonitoringPersistenceError(f"invalid candidate state: {to_state}")

    candidate = session.get(MonitoringCandidate, monitoring_candidate_id)
    if candidate is None:
        raise MonitoringPersistenceError(f"monitoring_candidate not found: {monitoring_candidate_id}")

    from_state = candidate.candidate_state
    if from_state == to_state:
        raise MonitoringPersistenceError(f"candidate state is already {from_state}")

    allowed = ALLOWED_CANDIDATE_TRANSITIONS.get(from_state, frozenset())
    if to_state not in allowed:
        raise MonitoringPersistenceError(f"transition from {from_state} to {to_state} is not allowed")

    transition = MonitoringCandidateStateTransition(
        monitoring_candidate_id=monitoring_candidate_id,
        from_state=from_state,
        to_state=to_state,
        transition_reason=transition_reason,
        actor_type=actor_type,
        actor_identifier=actor_identifier,
        transitioned_at=utc_now(),
    )
    session.add(transition)

    candidate.candidate_state = to_state
    if to_state in {CandidateState.REJECTED.value, CandidateState.APPROVED_FOR_INGESTION.value}:
        candidate.reviewed_at = utc_now()
        candidate.reviewed_by = actor_identifier
    if to_state == CandidateState.APPROVED_FOR_INGESTION.value:
        candidate.approved_for_ingestion_at = utc_now()
    candidate.updated_at = utc_now()
    session.flush()
    return transition


def get_candidate_transitions(
    session: Session,
    *,
    monitoring_candidate_id: UUID,
) -> list[MonitoringCandidateStateTransition]:
    stmt = (
        select(MonitoringCandidateStateTransition)
        .where(MonitoringCandidateStateTransition.monitoring_candidate_id == monitoring_candidate_id)
        .order_by(MonitoringCandidateStateTransition.transitioned_at.asc())
    )
    return list(session.execute(stmt).scalars().all())
