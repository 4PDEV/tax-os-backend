"""Canonical Citation Anchor Contract.

This module defines the governance boundary for the citation anchor layer.

Generation is strictly: LEGAL OBJECT CANDIDATES -> CANONICAL CITATION ANCHORS.

Citation anchors must be deterministic, stable, reproducible, traceable,
hierarchy-aware, and source-faithful. They must NEVER depend on AI, semantic
interpretation, mutable display formatting, generated summaries, or transient
database IDs. The same legal object candidate must always generate the same
canonical anchor under identical source conditions.

Concrete contract objects live alongside this module:

- :class:`app.services.citation_anchors.enums.CitationAnchorType`
- :class:`app.services.citation_anchors.enums.GenerationStatus`
- :class:`app.services.citation_anchors.models.CanonicalCitationAnchor`
- :class:`app.services.citation_anchors.models.CitationAnchorGenerationResult`
- :class:`app.services.citation_anchors.generators.base.BaseCitationAnchorGenerator`
"""

from app.services.citation_anchors.enums import CitationAnchorType, GenerationStatus
from app.services.citation_anchors.models import (
    CanonicalCitationAnchor,
    CitationAnchorGenerationMetadata,
    CitationAnchorGenerationResult,
    CitationAnchorMetadata,
)

__all__ = [
    "CanonicalCitationAnchor",
    "CitationAnchorGenerationError",
    "CitationAnchorGenerationMetadata",
    "CitationAnchorGenerationResult",
    "CitationAnchorMetadata",
    "CitationAnchorType",
    "GenerationStatus",
]


class CitationAnchorGenerationError(Exception):
    """Raised when citation anchor generation cannot complete deterministically."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
