from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.monitoring_attempt import MonitoringAttempt
from app.models.monitoring_event import MonitoringEvent
from app.models.source_document import SourceDocument
from app.services.monitoring.enums import ChangeType, MonitoringConfidence
from app.services.monitoring.errors import MonitoringPersistenceError

CHANGE_TYPES = frozenset(change_type.value for change_type in ChangeType)
CONFIDENCE_LEVELS = frozenset(level.value for level in MonitoringConfidence)


def create_monitoring_event(
    session: Session,
    *,
    monitoring_attempt_id: UUID,
    source_registry_id: UUID | None,
    source_url: str,
    source_name: str,
    source_type: str,
    detected_title: str,
    detected_url: str,
    detected_at: datetime,
    detection_method: str,
    checksum_sha256: str | None,
    previous_checksum_sha256: str | None,
    change_type: str,
    confidence: str,
    notes: str | None = None,
) -> MonitoringEvent:
    if change_type not in CHANGE_TYPES:
        raise MonitoringPersistenceError(f"invalid change_type: {change_type}")
    if confidence not in CONFIDENCE_LEVELS:
        raise MonitoringPersistenceError(f"invalid confidence: {confidence}")

    attempt = session.get(MonitoringAttempt, monitoring_attempt_id)
    if attempt is None:
        raise MonitoringPersistenceError(f"monitoring_attempt not found: {monitoring_attempt_id}")

    if source_registry_id is not None:
        source_registry = session.get(SourceDocument, source_registry_id)
        if source_registry is None:
            raise MonitoringPersistenceError(f"source_registry not found: {source_registry_id}")

    event = MonitoringEvent(
        monitoring_attempt_id=monitoring_attempt_id,
        source_registry_id=source_registry_id,
        source_url=source_url,
        source_name=source_name,
        source_type=source_type,
        detected_title=detected_title,
        detected_url=detected_url,
        detected_at=detected_at,
        detection_method=detection_method,
        checksum_sha256=checksum_sha256,
        previous_checksum_sha256=previous_checksum_sha256,
        change_type=change_type,
        confidence=confidence,
        notes=notes,
        created_at=utc_now(),
    )
    session.add(event)
    session.flush()
    return event
