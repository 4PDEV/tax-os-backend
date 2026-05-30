"""Source traceability validation for legal object persistence."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.source_version import SourceVersion
from app.services.legal_object_extraction.models import LegalObjectCandidate
from app.services.legal_object_persistence.contract import LegalObjectPersistenceError


def validate_source_traceability(
    db: Session,
    *,
    candidate: LegalObjectCandidate,
    source_version: SourceVersion | None,
) -> None:
    """Require source_version_id and resolvable source document before persistence."""
    if not candidate.source_version_id:
        raise LegalObjectPersistenceError(
            "legal object cannot be persisted without source_version_id"
        )

    try:
        UUID(candidate.source_version_id)
    except ValueError as exc:
        raise LegalObjectPersistenceError("source_version_id must be a valid UUID") from exc

    if source_version is None:
        raise LegalObjectPersistenceError(
            f"source_version_id {candidate.source_version_id} not found"
        )

    if source_version.source_document is None:
        raise LegalObjectPersistenceError(
            "legal object requires resolvable source_document for source_version_id"
        )
