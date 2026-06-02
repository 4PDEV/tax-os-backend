from enum import Enum


class SourceAllowlistStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class AttemptStatus(str, Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ChangeType(str, Enum):
    NEW_DOCUMENT = "new_document"
    MODIFIED_DOCUMENT = "modified_document"
    REMOVED_OR_UNAVAILABLE = "removed_or_unavailable"
    METADATA_CHANGED = "metadata_changed"
    CHECKSUM_CHANGED = "checksum_changed"
    UNKNOWN = "unknown"


class CandidateState(str, Enum):
    DETECTED = "detected"
    QUEUED_FOR_REVIEW = "queued_for_review"
    REJECTED = "rejected"
    APPROVED_FOR_INGESTION = "approved_for_ingestion"
    SUPERSEDED = "superseded"
    FAILED = "failed"


class MonitoringConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ErrorCategory(str, Enum):
    SOURCE_UNREACHABLE = "source_unreachable"
    ACCESS_DENIED = "access_denied"
    ROBOTS_OR_TERMS_RESTRICTED = "robots_or_terms_restricted"
    PARSE_FAILED = "parse_failed"
    CHECKSUM_FAILED = "checksum_failed"
    UNEXPECTED_CONTENT = "unexpected_content"
    TIMEOUT = "timeout"
    UNKNOWN_FAILURE = "unknown_failure"
