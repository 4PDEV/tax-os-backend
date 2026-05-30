from uuid import UUID

from app.services.extraction.extractors.base import BaseExtractor
from app.services.extraction.models import ExtractionResult

PDF_MIME_TYPES = frozenset({"application/pdf"})
PDF_EXTENSIONS = (".pdf",)


class PdfExtractor(BaseExtractor):
    """Skeleton PDF extractor.

    Intentionally unimplemented. A future, dedicated task will provide a
    deterministic, non-interpretive PDF text extraction strategy. That work is
    explicitly out of scope here and must NOT introduce:

    - OCR
    - AI / model-based extraction
    - heuristic layout reconstruction or content inference

    When implemented, ``extract`` must remain faithful (PDF text only, no
    interpretation) and reproducible, and must bump ``version`` accordingly.
    """

    name = "pdf"
    version = "0.0.0"

    def can_handle(self, *, mime_type: str | None, filename: str | None) -> bool:
        if mime_type is not None and mime_type.split(";")[0].strip().lower() in PDF_MIME_TYPES:
            return True
        if filename is not None and filename.lower().endswith(PDF_EXTENSIONS):
            return True
        return False

    def extract(self, *, source_version_id: UUID, content: bytes) -> ExtractionResult:
        raise NotImplementedError("PDF extraction is not implemented in TASK-002A")
