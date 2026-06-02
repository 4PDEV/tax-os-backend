from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.source_allowlist_entry import SourceAllowlistEntry
from app.services.monitoring.enums import SourceAllowlistStatus
from app.services.monitoring.errors import MonitoringPersistenceError

ALLOWLIST_STATUSES = frozenset(status.value for status in SourceAllowlistStatus)


def create_allowlist_entry(
    session: Session,
    *,
    jurisdiction: str,
    authority_name: str,
    source_type: str,
    base_url: str,
    allowed_patterns_json: list[str],
    blocked_patterns_json: list[str],
    monitoring_frequency: str,
    status: str = SourceAllowlistStatus.ACTIVE.value,
    notes: str | None = None,
) -> SourceAllowlistEntry:
    if status not in ALLOWLIST_STATUSES:
        raise MonitoringPersistenceError(f"invalid allowlist status: {status}")

    entry = SourceAllowlistEntry(
        jurisdiction=jurisdiction,
        authority_name=authority_name,
        source_type=source_type,
        base_url=base_url,
        allowed_patterns_json=allowed_patterns_json,
        blocked_patterns_json=blocked_patterns_json,
        monitoring_frequency=monitoring_frequency,
        status=status,
        notes=notes,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    session.add(entry)
    session.flush()
    return entry
