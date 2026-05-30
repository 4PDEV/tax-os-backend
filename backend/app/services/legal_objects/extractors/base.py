from abc import ABC, abstractmethod

from app.services.legal_objects.models import LegalObjectExtractionResult
from app.services.segmentation.models import SegmentationResult


class BaseLegalObjectExtractor(ABC):
    """Contract every legal object extractor must implement.

    Subclasses map a deterministic :class:`SegmentationResult` into a
    deterministic :class:`LegalObjectExtractionResult`. Implementations must be
    source-faithful and non-interpretive: no summarization, inference, topic
    classification, authority ranking, or legal-effect determination.

    ``name`` and ``version`` are mandatory so every extraction is traceable and
    reproducible. Bumping ``version`` signals that extraction output for the
    same input may change.
    """

    name: str = "base"
    version: str = "0.0.0"

    @abstractmethod
    def can_handle(self, *, segmentation_result: SegmentationResult, hint: str | None = None) -> bool:
        """Return whether this extractor can process the given segmentation result."""
        raise NotImplementedError

    @abstractmethod
    def extract(self, *, segmentation_result: SegmentationResult) -> LegalObjectExtractionResult:
        """Map structured segments into deterministic legal object candidates."""
        raise NotImplementedError
