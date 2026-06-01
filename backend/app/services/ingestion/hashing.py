import hashlib
import json
from typing import Any

from app.services.extraction.hashing import sha256_text

STRUCTURE_HASH_UNIT_FIELDS: tuple[str, ...] = (
    "unit_type",
    "unit_label",
    "unit_title",
    "full_heading",
    "parent_unit_id",
    "hierarchy_level",
    "start_offset",
    "end_offset",
    "raw_text",
)


def canonical_structure_units_for_hash(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a deterministic, hash-stable representation of structural units.

    Excludes volatile fields (timestamps, UUIDs, parser version, source_version_id).
    """
    canonical: list[dict[str, Any]] = []
    for unit in units:
        canonical.append({field: unit[field] for field in STRUCTURE_HASH_UNIT_FIELDS if field in unit})
    canonical.sort(key=lambda u: (u.get("start_offset", 0), u.get("unit_label", "")))
    return canonical


def sha256_structure(structure_units: list[dict[str, Any]]) -> str:
    """SHA-256 over canonical JSON of structural unit content (no volatile metadata)."""
    payload = canonical_structure_units_for_hash(structure_units)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


__all__ = [
    "STRUCTURE_HASH_UNIT_FIELDS",
    "canonical_structure_units_for_hash",
    "sha256_structure",
    "sha256_text",
]
