from uuid import UUID

from app.services.extraction.extractors.base import BaseExtractor
from app.services.extraction.models import ExtractionResult

HTML_MIME_TYPES = frozenset({"text/html", "application/xhtml+xml"})
HTML_EXTENSIONS = (".html", ".htm")


class HtmlExtractor(BaseExtractor):
    """Skeleton HTML extractor.

    Intentionally unimplemented. A future task will define deterministic,
    non-interpretive HTML-to-text extraction (e.g. faithful text content
    without summarization or semantic restructuring). HTML parsing is out of
    scope for TASK-002A.
    """

    name = "html"
    version = "0.0.0"

    def can_handle(self, *, mime_type: str | None, filename: str | None) -> bool:
        if mime_type is not None and mime_type.split(";")[0].strip().lower() in HTML_MIME_TYPES:
            return True
        if filename is not None and filename.lower().endswith(HTML_EXTENSIONS):
            return True
        return False

    def extract(self, *, source_version_id: UUID, content: bytes) -> ExtractionResult:
        raise NotImplementedError("HTML extraction is not implemented in TASK-002A")
