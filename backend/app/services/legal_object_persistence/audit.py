"""Optional audit logging for legal object persistence operations."""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record_legal_object_audit_event(
    db: Session,
    *,
    entity_type: str,
    entity_id: str | UUID | None,
    action_type: str,
    actor_type: str = "system",
    actor_identifier: str | None = "legal_object_persistence",
    previous_state: dict[str, Any] | None = None,
    new_state: dict[str, Any] | None = None,
) -> AuditLog:
    """Append an audit_log row for a legal object lifecycle event."""
    parsed_entity_id: UUID | None
    if entity_id is None:
        parsed_entity_id = None
    elif isinstance(entity_id, UUID):
        parsed_entity_id = entity_id
    else:
        parsed_entity_id = None

    record = AuditLog(
        entity_type=entity_type,
        entity_id=parsed_entity_id,
        action_type=action_type,
        actor_type=actor_type,
        actor_identifier=actor_identifier,
        previous_state_json=previous_state,
        new_state_json=new_state,
    )
    db.add(record)
    db.flush()
    return record
