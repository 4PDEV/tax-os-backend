from enum import Enum


class LegalObjectType(str, Enum):
    """Canonical structural legal object labels.

    These describe the structural identity of a legal object candidate only.
    They carry NO interpretive, tax-topic, or legal-effect meaning. Semantic
    types (obligation, exemption, penalty, rate, right, prohibition, etc.) are
    explicitly out of scope. No additional types may be introduced without a
    contract revision.
    """

    ACT = "act"
    REGULATION = "regulation"
    ORDER = "order"
    NOTICE = "notice"
    JUDGMENT = "judgment"
    TREATY = "treaty"
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


class ExtractionStatus(str, Enum):
    """Permitted legal object extraction states.

    Only these statuses are allowed. No additional statuses may be added
    without an explicit contract revision.
    """

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
