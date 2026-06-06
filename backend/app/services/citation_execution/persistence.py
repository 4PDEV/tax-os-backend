"""Citation entity persistence — idempotent on citation_hash."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.citation import Citation
from app.services.citation_execution.validation import (
    CitationExecutionValidationError,
    validate_citation_hash,
    validate_citation_id,
    validate_location_reference,
    validate_provenance_pins,
)


class CitationExecutionPersistenceError(Exception):
    pass


def find_existing_citation(session: Session, *, citation_hash: str) -> Citation | None:
    validate_citation_hash(citation_hash)
    return session.execute(
        select(Citation).where(Citation.citation_hash == citation_hash).limit(1)
    ).scalar_one_or_none()


def get_citation_by_hash(session: Session, *, citation_hash: str) -> Citation | None:
    return find_existing_citation(session, citation_hash=citation_hash)


def create_citation(
    session: Session,
    *,
    citation_id: str,
    citation_hash: str,
    legal_object_id: str,
    legal_object_version_id,
    source_version_id,
    location_reference: str,
    rendered_citation_text: str,
    assembled_at: datetime | None = None,
) -> tuple[Citation, bool]:
    """Persist citation entity. Returns (citation, created). created=False when existing returned."""
    validate_citation_id(citation_id)
    validate_citation_hash(citation_hash)
    validate_location_reference(location_reference)
    validate_provenance_pins(
        legal_object_id=legal_object_id,
        legal_object_version_id=legal_object_version_id,
        source_version_id=source_version_id,
    )
    if not rendered_citation_text or not rendered_citation_text.strip():
        raise CitationExecutionValidationError("invalid_rendered_citation_text")

    existing = find_existing_citation(session, citation_hash=citation_hash)
    if existing is not None:
        return existing, False

    resolved_assembled_at = assembled_at or utc_now()
    citation = Citation(
        citation_id=citation_id,
        citation_hash=citation_hash,
        legal_object_id=legal_object_id,
        legal_object_version_id=legal_object_version_id,
        source_version_id=source_version_id,
        location_reference=location_reference,
        rendered_citation_text=rendered_citation_text,
        assembled_at=resolved_assembled_at,
        created_at=utc_now(),
    )
    session.add(citation)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raced = find_existing_citation(session, citation_hash=citation_hash)
        if raced is not None:
            return raced, False
        raise CitationExecutionPersistenceError("citation_create_failed") from exc
    return citation, True
