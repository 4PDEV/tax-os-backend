"""Deterministic citation hash for reproducibility and audit."""

from uuid import UUID

from app.services.legal_object_extraction.identity import sha256_text

CITATION_ID_PREFIX = "cit_"
CITATION_ID_HEX_LENGTH = 32


def compute_citation_hash(
    *,
    source_version_id: UUID,
    legal_object_id: str,
    legal_object_version_id: UUID,
    location_reference: str,
) -> str:
    payload = (
        f"{source_version_id}|{legal_object_id}|{legal_object_version_id}|{location_reference}"
    )
    return sha256_text(payload)


def citation_id_from_hash(citation_hash: str) -> str:
    return f"{CITATION_ID_PREFIX}{citation_hash[:CITATION_ID_HEX_LENGTH]}"
