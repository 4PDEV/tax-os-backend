from enum import Enum


class StructuralUnitType(str, Enum):
    """Structural document unit labels.

    These describe the structural role of a document block only. They carry no
    legal meaning, topic classification, or interpretive semantics.
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
    UNKNOWN = "unknown"
