from abc import ABC, abstractmethod
from uuid import UUID

from app.services.segmentation.models import SegmentationResult


class BaseSegmenter(ABC):
    """Contract every structural segmenter must implement.

    Subclasses convert raw extracted text into a deterministic, ordered
    :class:`SegmentationResult`. Implementations must be source-faithful and
    non-interpretive: no summarization, inference, rewriting, or legal
    classification.

    ``name`` and ``version`` are mandatory so every segmentation is traceable
    and reproducible. Bumping ``version`` signals that segmentation output for
    the same input may change.
    """

    name: str = "base"
    version: str = "0.0.0"

    @abstractmethod
    def can_handle(self, *, raw_text: str, hint: str | None = None) -> bool:
        """Return whether this segmenter can process the given text."""
        raise NotImplementedError

    @abstractmethod
    def segment(self, *, source_version_id: UUID, raw_text: str) -> SegmentationResult:
        """Convert raw extracted text into a deterministic segmentation result."""
        raise NotImplementedError
