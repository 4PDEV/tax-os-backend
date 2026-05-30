"""Structural Source Segmentation Contract.

This module defines the governance boundary for the segmentation layer.

Segmentation is strictly: RAW EXTRACTED TEXT -> STRUCTURED TEXT SEGMENTS.

The segmentation layer must remain deterministic, reproducible, traceable,
non-interpretive, hierarchy-aware, and source-faithful. It must NEVER infer
legal meaning, rewrite text, summarize, classify legal intent, or invent
structure not present in the source.

Concrete contract objects live alongside this module:

- :class:`app.services.segmentation.enums.SegmentType`
- :class:`app.services.segmentation.enums.SegmentationStatus`
- :class:`app.services.segmentation.models.Segment`
- :class:`app.services.segmentation.models.SegmentationResult`
- :class:`app.services.segmentation.segmenters.base.BaseSegmenter`
"""

from app.services.segmentation.enums import SegmentationStatus, SegmentType
from app.services.segmentation.models import (
    Segment,
    SegmentationMetadata,
    SegmentationResult,
    SegmentMetadata,
)

__all__ = [
    "Segment",
    "SegmentMetadata",
    "SegmentationError",
    "SegmentationMetadata",
    "SegmentationResult",
    "SegmentationStatus",
    "SegmentType",
]


class SegmentationError(Exception):
    """Raised when segmentation cannot be completed deterministically."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
