from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.monitoring_attempt import MonitoringAttempt
from app.models.source_allowlist_entry import SourceAllowlistEntry
from app.services.monitoring.enums import AttemptStatus, ErrorCategory
from app.services.monitoring.errors import MonitoringPersistenceError

ATTEMPT_STATUSES = frozenset(status.value for status in AttemptStatus)
ERROR_CATEGORIES = frozenset(category.value for category in ErrorCategory)


def create_monitoring_attempt(
    session: Session,
    *,
    source_allowlist_entry_id: UUID,
    agent_name: str,
    agent_version: str,
    started_at: datetime,
    attempt_status: str = AttemptStatus.STARTED.value,
) -> MonitoringAttempt:
    if attempt_status not in ATTEMPT_STATUSES:
        raise MonitoringPersistenceError(f"invalid attempt_status: {attempt_status}")

    allowlist = session.get(SourceAllowlistEntry, source_allowlist_entry_id)
    if allowlist is None:
        raise MonitoringPersistenceError(
            f"source_allowlist_entry not found: {source_allowlist_entry_id}"
        )

    attempt = MonitoringAttempt(
        source_allowlist_entry_id=source_allowlist_entry_id,
        agent_name=agent_name,
        agent_version=agent_version,
        started_at=started_at,
        attempt_status=attempt_status,
        created_at=utc_now(),
    )
    session.add(attempt)
    session.flush()
    return attempt


def complete_monitoring_attempt(
    session: Session,
    *,
    monitoring_attempt_id: UUID,
    completed_at: datetime,
    attempt_status: str = AttemptStatus.COMPLETED.value,
) -> MonitoringAttempt:
    if attempt_status not in {AttemptStatus.COMPLETED.value, AttemptStatus.PARTIAL.value}:
        raise MonitoringPersistenceError(
            f"invalid completion status for monitoring attempt: {attempt_status}"
        )
    attempt = session.get(MonitoringAttempt, monitoring_attempt_id)
    if attempt is None:
        raise MonitoringPersistenceError(f"monitoring_attempt not found: {monitoring_attempt_id}")
    attempt.completed_at = completed_at
    attempt.attempt_status = attempt_status
    session.flush()
    return attempt


def fail_monitoring_attempt(
    session: Session,
    *,
    monitoring_attempt_id: UUID,
    completed_at: datetime,
    error_category: str,
    error_message: str | None = None,
) -> MonitoringAttempt:
    if error_category not in ERROR_CATEGORIES:
        raise MonitoringPersistenceError(f"invalid error_category: {error_category}")
    attempt = session.get(MonitoringAttempt, monitoring_attempt_id)
    if attempt is None:
        raise MonitoringPersistenceError(f"monitoring_attempt not found: {monitoring_attempt_id}")
    attempt.completed_at = completed_at
    attempt.attempt_status = AttemptStatus.FAILED.value
    attempt.error_category = error_category
    attempt.error_message = error_message
    session.flush()
    return attempt
