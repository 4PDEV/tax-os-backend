"""Cross-Reference Detection Contract.

This module defines the governance boundary for cross-reference detection.

Detection is strictly: identify, record, link — NOT interpret, prioritize,
or reason. Cross-reference detection must be deterministic, reproducible,
traceable, and source-backed.

The system must never infer legal meaning, authority hierarchy, legal
consequences, or legal interpretation. This layer only identifies references.

Concrete contract objects:

- :class:`app.services.cross_reference.enums.ReferenceType`
- :class:`app.services.cross_reference.enums.ReferenceConfidence`
- :class:`app.services.cross_reference.models.CrossReferenceResult`
- :class:`app.services.cross_reference.detector.CrossReferenceDetector`
"""

from app.services.cross_reference.enums import ReferenceConfidence, ReferenceType
from app.services.cross_reference.models import CrossReferenceResult

__all__ = [
    "CrossReferenceDetectionError",
    "CrossReferenceResult",
    "ReferenceConfidence",
    "ReferenceType",
]


class CrossReferenceDetectionError(Exception):
    """Raised when cross-reference detection cannot complete deterministically."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
