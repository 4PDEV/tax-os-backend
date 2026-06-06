"""Read-only citation lookup for retrieval execution — no assembly or creation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.citation import Citation


def lookup_citation_for_version(
    session: Session,
    *,
    legal_object_version_id: UUID,
) -> Citation | None:
    """Return deterministic citation for version — lowest citation_hash wins."""
    return session.execute(
        select(Citation)
        .where(Citation.legal_object_version_id == legal_object_version_id)
        .order_by(Citation.citation_hash.asc())
        .limit(1)
    ).scalar_one_or_none()
