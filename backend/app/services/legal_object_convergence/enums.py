from enum import Enum


class ConvergenceSource(str, Enum):
    """Upstream pipeline that produced a legal object candidate."""

    STRUCTURAL_UNIT = "structural_unit"
    SEGMENT = "segment"
    LEGACY = "legacy"
    UNKNOWN = "unknown"


class ConvergenceStatus(str, Enum):
    """Result of converging a candidate to the canonical shape."""

    CANONICAL = "canonical"
    MAPPED = "mapped"
    PARTIAL = "partial"
    REJECTED = "rejected"
