"""Source Text Extraction Contract.

This module defines the governance boundary for the extraction layer.

Extraction is strictly: SOURCE FILE -> RAW EXTRACTED TEXT.

The extraction layer must remain faithful, deterministic, reproducible,
traceable, version-aware, and non-interpretive. It must NEVER summarize,
infer, rewrite, simplify, or interpret legal meaning.

The concrete contract objects live alongside this module:

- :class:`app.services.extraction.enums.ExtractionStatus`
- :class:`app.services.extraction.models.ExtractionMetadata`
- :class:`app.services.extraction.models.ExtractionResult`
- :class:`app.services.extraction.extractors.base.BaseExtractor`
"""

from app.services.extraction.enums import ExtractionStatus
from app.services.extraction.models import ExtractionMetadata, ExtractionResult

__all__ = [
    "ExtractionError",
    "ExtractionMetadata",
    "ExtractionResult",
    "ExtractionStatus",
]


class ExtractionError(Exception):
    """Raised when extraction cannot be completed in a deterministic way."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
