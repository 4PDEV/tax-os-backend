import hashlib

TEXT_HASH_ENCODING = "utf-8"
LEGAL_OBJECT_ID_PREFIX = "lo_"
LEGAL_OBJECT_ID_HEX_LENGTH = 32


def sha256_text(text: str) -> str:
    """Return SHA-256 hex digest of raw text (no normalization)."""
    return hashlib.sha256(text.encode(TEXT_HASH_ENCODING)).hexdigest()


def generate_legal_object_id(
    *,
    source_version_id: str,
    canonical_path: str,
    object_type: str,
    object_label: str,
    start_offset: int,
    text_hash: str,
) -> str:
    """Deterministic legal object identity from stable structural inputs.

    Never uses random UUIDs. The same inputs always produce the same id;
    different text or location produces a different id.
    """
    raw = (
        f"{source_version_id}|{canonical_path}|{object_type}|"
        f"{object_label}|{start_offset}|{text_hash}"
    )
    digest = hashlib.sha256(raw.encode(TEXT_HASH_ENCODING)).hexdigest()
    return f"{LEGAL_OBJECT_ID_PREFIX}{digest[:LEGAL_OBJECT_ID_HEX_LENGTH]}"


def build_canonical_path(unit, by_id: dict) -> str:
    """Build deterministic path from structural lineage using unit labels only.

    Uses structural lineage only — no interpreted titles, no inferred parents.
    """
    chain: list[str] = []
    seen: set[str] = set()
    current = unit

    while current is not None:
        if current.unit_id in seen:
            break
        seen.add(current.unit_id)
        chain.append(current.unit_label)
        parent_id = current.parent_unit_id
        if parent_id and parent_id in by_id:
            current = by_id[parent_id]
        else:
            break

    chain.reverse()
    if not chain:
        return unit.unit_label
    return " > ".join(chain)
