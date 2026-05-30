"""Deterministic content hashing for legal object integrity enforcement."""

from datetime import date

from app.services.legal_object_extraction.identity import sha256_text

INTEGRITY_HASH_SEPARATOR = "|"


def build_object_identifier(*, structural_unit_id: str, object_label: str) -> str:
    """Stable structural identifier for hash inputs (excludes volatile DB fields)."""
    return f"{structural_unit_id}:{object_label}"


def compute_content_integrity_hash(
    *,
    source_version_id: str,
    object_type: str,
    object_identifier: str,
    canonical_text: str,
    effective_from: date | None = None,
    effective_to: date | None = None,
) -> str:
    """SHA-256 over stable legal-memory fields only.

    Excludes volatile fields such as created_at, updated_at, and database ids.
    """
    effective_from_part = effective_from.isoformat() if effective_from else ""
    effective_to_part = effective_to.isoformat() if effective_to else ""
    payload = INTEGRITY_HASH_SEPARATOR.join(
        (
            source_version_id,
            object_type,
            object_identifier,
            canonical_text,
            effective_from_part,
            effective_to_part,
        )
    )
    return sha256_text(payload)


def verify_text_hash(*, raw_text: str, text_hash: str) -> bool:
    """Return True when text_hash matches SHA-256 of raw_text."""
    return text_hash == sha256_text(raw_text)
