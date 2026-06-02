from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.monitoring_candidate import MonitoringCandidate
from app.models.monitoring_candidate_state_transition import MonitoringCandidateStateTransition
from app.models.monitoring_event import MonitoringEvent
from app.services.monitoring.enums import CandidateState
from app.services.monitoring.errors import MonitoringPersistenceError


def create_monitoring_candidate(
    session: Session,
    *,
    monitoring_event_id: UUID,
    candidate_state: str = CandidateState.DETECTED.value,
    actor_type: str = "system",
    actor_identifier: str | None = None,
    transition_reason: str | None = "candidate detected from monitoring event",
) -> MonitoringCandidate:
    if candidate_state != CandidateState.DETECTED.value:
        raise MonitoringPersistenceError(
            "monitoring candidate must be created in detected state"
        )

    event = session.get(MonitoringEvent, monitoring_event_id)
    if event is None:
        raise MonitoringPersistenceError(f"monitoring_event not found: {monitoring_event_id}")

    existing = session.execute(
        select(MonitoringCandidate).where(MonitoringCandidate.monitoring_event_id == monitoring_event_id)
    ).scalar_one_or_none()
    if existing is not None:
        raise MonitoringPersistenceError("monitoring candidate already exists for this event")

    candidate = MonitoringCandidate(
        monitoring_event_id=monitoring_event_id,
        candidate_state=candidate_state,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    session.add(candidate)
    session.flush()

    transition = MonitoringCandidateStateTransition(
        monitoring_candidate_id=candidate.id,
        from_state=None,
        to_state=candidate_state,
        transition_reason=transition_reason,
        actor_type=actor_type,
        actor_identifier=actor_identifier,
        transitioned_at=utc_now(),
    )
    session.add(transition)
    session.flush()
    return candidate
