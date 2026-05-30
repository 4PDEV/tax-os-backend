from enum import Enum


class SegmentType(str, Enum):
    """Structural (not semantic) segment labels.

    These describe the structural role of a block of text only. They carry no
    legal meaning, classification, or interpretation. No additional types may
    be introduced without an explicit contract revision.
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
    UNKNOWN = "unknown"


class SegmentationStatus(str, Enum):
    """Permitted segmentation states.

    Only these statuses are allowed. No additional statuses may be added
    without an explicit contract revision.
    """

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
