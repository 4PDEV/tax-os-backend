"""Map registry source metadata to AuthorityType — descriptive only, no weighting."""

from app.services.citation.models import AuthorityType

_SOURCE_TYPE_AUTHORITY: dict[str, AuthorityType] = {
    "law": AuthorityType.STATUTE,
    "act": AuthorityType.STATUTE,
    "statute": AuthorityType.STATUTE,
    "regulation": AuthorityType.REGULATION,
    "guidance": AuthorityType.GUIDANCE,
    "public_ruling": AuthorityType.PUBLIC_RULING,
    "private_ruling": AuthorityType.PRIVATE_RULING,
    "case": AuthorityType.CASE,
    "judgment": AuthorityType.CASE,
    "tribunal": AuthorityType.TRIBUNAL,
    "treaty": AuthorityType.TREATY,
    "accounting_standard": AuthorityType.ACCOUNTING_STANDARD,
}


def resolve_authority_type(*, source_type: str, authority_level: str) -> AuthorityType:
    normalized = source_type.strip().lower()
    if normalized in _SOURCE_TYPE_AUTHORITY:
        return _SOURCE_TYPE_AUTHORITY[normalized]

    level = authority_level.strip().lower()
    if level in {"national", "primary"}:
        return AuthorityType.STATUTE
    if level == "regulation":
        return AuthorityType.REGULATION
    if level in {"guidance", "administrative"}:
        return AuthorityType.GUIDANCE

    return AuthorityType.OTHER
