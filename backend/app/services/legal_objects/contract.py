"""Legal Object Extraction Contract.

This module defines the governance boundary for the legal object extraction
layer.

Extraction is strictly: STRUCTURED TEXT SEGMENTS -> CANONICAL LEGAL OBJECT
CANDIDATES.

The layer must remain deterministic, reproducible, traceable, non-interpretive,
source-faithful, and segment-backed. It must NEVER infer legal meaning,
summarize provisions, classify tax topics, determine legal effect, resolve
conflicts, rank authority, or generate advice.

Concrete contract objects live alongside this module:

- :class:`app.services.legal_objects.enums.LegalObjectType`
- :class:`app.services.legal_objects.enums.ExtractionStatus`
- :class:`app.services.legal_objects.models.LegalObjectCandidate`
- :class:`app.services.legal_objects.models.LegalObjectExtractionResult`
- :class:`app.services.legal_objects.extractors.base.BaseLegalObjectExtractor`
"""

from app.services.legal_objects.enums import ExtractionStatus, LegalObjectType
from app.services.legal_objects.models import (
    LegalObjectCandidate,
    LegalObjectExtractionMetadata,
    LegalObjectExtractionResult,
    LegalObjectMetadata,
)

__all__ = [
    "ExtractionStatus",
    "LegalObjectCandidate",
    "LegalObjectExtractionError",
    "LegalObjectExtractionMetadata",
    "LegalObjectExtractionResult",
    "LegalObjectMetadata",
    "LegalObjectType",
]


class LegalObjectExtractionError(Exception):
    """Raised when legal object extraction cannot be completed deterministically."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
