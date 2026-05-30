from enum import Enum


class CitationAnchorType(str, Enum):
    """Structural citation anchor labels.

    These describe the structural identity of a citation anchor only. They carry
    NO interpretive, authority, or semantic meaning. No additional types may be
    introduced without a contract revision.
    """

    DOCUMENT = "document"
    PART = "part"
    CHAPTER = "chapter"
    SECTION = "section"
    ARTICLE = "article"
    CLAUSE = "clause"
    SUBCLAUSE = "subclause"
    PARAGRAPH = "paragraph"
    SCHEDULE = "schedule"
    DEFINITION = "definition"
    UNKNOWN = "unknown"


class GenerationStatus(str, Enum):
    """Permitted citation anchor generation states.

    Only these statuses are allowed. No additional statuses may be added
    without an explicit contract revision.
    """

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
