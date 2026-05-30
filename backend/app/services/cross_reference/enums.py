from enum import Enum


class ReferenceType(str, Enum):
    """Structural reference labels detected in source text.

    These identify the surface form of a cross-reference only. They carry no
    legal meaning, authority hierarchy, or interpretive classification.
    """

    SECTION = "section"
    ARTICLE = "article"
    REGULATION = "regulation"
    SCHEDULE = "schedule"
    PART = "part"
    CHAPTER = "chapter"
    ACT = "act"
    LAW = "law"
    GUIDANCE = "guidance"
    CASE = "case"
    TREATY = "treaty"
    UNKNOWN = "unknown"


class ReferenceConfidence(str, Enum):
    """Deterministic confidence assigned by pattern match quality.

    Not probabilistic inference — each level maps to a fixed pattern class.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
