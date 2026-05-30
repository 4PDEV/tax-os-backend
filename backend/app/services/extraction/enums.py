from enum import Enum


class ExtractionStatus(str, Enum):
    """Terminal and intermediate states for a source text extraction.

    Only these statuses are permitted. No additional statuses may be added
    without an explicit contract revision.
    """

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
