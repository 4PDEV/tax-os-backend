"""Deterministic location reference construction — identification only."""

from app.services.citation.models import LocationReferenceKind

_OBJECT_TYPE_TO_KIND: dict[str, LocationReferenceKind] = {
    "section": LocationReferenceKind.SECTION,
    "article": LocationReferenceKind.ARTICLE,
    "regulation": LocationReferenceKind.REGULATION,
    "part": LocationReferenceKind.PART,
    "chapter": LocationReferenceKind.CHAPTER,
    "schedule": LocationReferenceKind.SCHEDULE,
    "paragraph": LocationReferenceKind.PARAGRAPH,
    "clause": LocationReferenceKind.CLAUSE,
    "subclause": LocationReferenceKind.SUBSECTION,
    "subparagraph": LocationReferenceKind.SUBSECTION,
    "subsection": LocationReferenceKind.SUBSECTION,
}

_KIND_DISPLAY: dict[LocationReferenceKind, str] = {
    LocationReferenceKind.SECTION: "Section",
    LocationReferenceKind.ARTICLE: "Article",
    LocationReferenceKind.REGULATION: "Regulation",
    LocationReferenceKind.PART: "Part",
    LocationReferenceKind.CHAPTER: "Chapter",
    LocationReferenceKind.SCHEDULE: "Schedule",
    LocationReferenceKind.PARAGRAPH: "Paragraph",
    LocationReferenceKind.CLAUSE: "Clause",
    LocationReferenceKind.SUBSECTION: "Subsection",
}


def build_location_reference(*, object_type: str, object_label: str) -> str:
    """Build a deterministic location string such as 'Section 15'."""
    label = object_label.strip()
    if not label:
        raise ValueError("object_label is required for location_reference")

    normalized_type = object_type.strip().lower()
    kind = _OBJECT_TYPE_TO_KIND.get(normalized_type)
    if kind is None:
        return label

    prefix = _KIND_DISPLAY[kind]
    lowered_label = label.lower()
    if lowered_label.startswith(prefix.lower()):
        return label
    return f"{prefix} {label}"
