from enum import Enum


class PersistenceStatus(str, Enum):
    """Result status for a legal object persistence operation."""

    CREATED = "created"
    VERSION_CREATED = "version_created"
    DUPLICATE_DETECTED = "duplicate_detected"
    REJECTED = "rejected"
    FAILED = "failed"
