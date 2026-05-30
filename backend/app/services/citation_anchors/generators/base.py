from abc import ABC, abstractmethod

from app.services.citation_anchors.models import CitationAnchorGenerationResult
from app.services.legal_objects.models import LegalObjectExtractionResult


class BaseCitationAnchorGenerator(ABC):
    """Contract every citation anchor generator must implement.

    Subclasses map a deterministic :class:`LegalObjectExtractionResult` into a
    deterministic :class:`CitationAnchorGenerationResult`. Implementations must
    be source-faithful and non-interpretive: anchors derive only from stable
    structural inputs, never from AI, semantic interpretation, mutable display
    formatting, or transient database IDs.

    ``name`` and ``version`` are mandatory so every generation is traceable and
    reproducible. Bumping ``version`` signals that anchor output for the same
    input may change.
    """

    name: str = "base"
    version: str = "0.0.0"

    @abstractmethod
    def can_handle(self, *, extraction_result: LegalObjectExtractionResult, hint: str | None = None) -> bool:
        """Return whether this generator can process the given legal object result."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, *, extraction_result: LegalObjectExtractionResult) -> CitationAnchorGenerationResult:
        """Generate deterministic canonical citation anchors for legal objects."""
        raise NotImplementedError
