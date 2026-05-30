from enum import Enum


class PersistenceStatus(str, Enum):
    """Result status for a legal object persistence operation."""

    CREATED = "created"
    VERSION_CREATED = "version_created"
    DUPLICATE_DETECTED = "duplicate_detected"
    REJECTED = "rejected"
    FAILED = "failed"


class IntegrityOperationStatus(str, Enum):
    """Result status for integrity lifecycle operations."""

    SUCCESS = "success"
    REJECTED = "rejected"
    FAILED = "failed"
