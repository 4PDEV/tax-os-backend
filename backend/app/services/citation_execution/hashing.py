"""Canonical citation identity hashing (004D provenance tuple)."""

from uuid import UUID

from app.services.citation.hash import compute_citation_hash as _compute_citation_hash


def compute_citation_hash(
    *,
    source_version_id: UUID,
    legal_object_id: str,
    legal_object_version_id: UUID,
    location_reference: str,
) -> str:
    return _compute_citation_hash(
        source_version_id=source_version_id,
        legal_object_id=legal_object_id,
        legal_object_version_id=legal_object_version_id,
        location_reference=location_reference,
    )


__all__ = ["compute_citation_hash"]
