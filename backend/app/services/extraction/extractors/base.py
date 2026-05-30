from abc import ABC, abstractmethod
from uuid import UUID

from app.services.extraction.models import ExtractionResult


class BaseExtractor(ABC):
    """Contract every source text extractor must implement.

    Subclasses convert a single source file's bytes into a deterministic
    :class:`ExtractionResult`. Implementations must be faithful and
    non-interpretive: no summarization, inference, rewriting, or legal parsing.

    ``name`` and ``version`` are mandatory so every extraction is traceable and
    reproducible. Bumping ``version`` signals that extraction output for the
    same input may change.
    """

    name: str = "base"
    version: str = "0.0.0"

    @abstractmethod
    def can_handle(self, *, mime_type: str | None, filename: str | None) -> bool:
        """Return whether this extractor can process the given file descriptor."""
        raise NotImplementedError

    @abstractmethod
    def extract(self, *, source_version_id: UUID, content: bytes) -> ExtractionResult:
        """Convert raw file bytes into a deterministic extraction result."""
        raise NotImplementedError
