from enum import Enum


class LegalObjectType(str, Enum):
    """Canonical structural legal object labels for extraction candidates.

    These identify the structural type of a legal object candidate only. They
    carry no interpretive, tax-topic, or legal-effect meaning.
    """

    ACT = "act"
    LAW = "law"
    TITLE = "title"
    PART = "part"
    CHAPTER = "chapter"
    SECTION = "section"
    ARTICLE = "article"
    REGULATION = "regulation"
    SCHEDULE = "schedule"
    PARAGRAPH = "paragraph"
    SUBPARAGRAPH = "subparagraph"
    DEFINITION = "definition"
    UNKNOWN = "unknown"


class LegalObjectExtractionStatus(str, Enum):
    """Permitted extraction states for a legal object candidate."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    UNKNOWN = "unknown"
