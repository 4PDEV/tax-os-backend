"""Legal Object Extraction Contract.

This module defines the governance boundary for proto-legal object extraction.

Extraction is strictly: Structural Units → Legal Object Candidates.

This layer introduces canonical identity, lineage, deterministic object paths, and
object-level text hashing — but performs NO legal interpretation, topic
classification, authority ranking, conflict resolution, citation generation,
answer generation, or persistence.

Legal object candidates are source-backed structured inputs for later validation
and persistence. They are not approved legal knowledge.
"""

from app.services.legal_object_extraction.enums import LegalObjectExtractionStatus, LegalObjectType
from app.services.legal_object_extraction.models import LegalObjectCandidate

__all__ = [
    "LegalObjectCandidate",
    "LegalObjectExtractionError",
    "LegalObjectExtractionStatus",
    "LegalObjectType",
]


class LegalObjectExtractionError(Exception):
    """Raised when legal object extraction cannot complete deterministically."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
