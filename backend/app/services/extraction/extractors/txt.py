import time
from uuid import UUID

from app.core.datetime_utils import utc_now
from app.services.extraction.enums import ExtractionStatus
from app.services.extraction.extractors.base import BaseExtractor
from app.services.extraction.hashing import sha256_text
from app.services.extraction.models import ExtractionMetadata, ExtractionResult

TXT_MIME_TYPES = frozenset({"text/plain"})
TXT_EXTENSIONS = (".txt",)
DEFAULT_ENCODING = "utf-8"


class TxtExtractor(BaseExtractor):
    """Faithful plain-text extractor.

    Returns the file's text exactly as decoded. No normalization, trimming,
    or transformation is applied. UTF-8 is used as the canonical encoding; if
    the bytes are not valid UTF-8 the extractor degrades deterministically to a
    PARTIAL result using lossy replacement rather than failing silently.
    """

    name = "txt"
    version = "1.0.0"

    def can_handle(self, *, mime_type: str | None, filename: str | None) -> bool:
        if mime_type is not None and mime_type.split(";")[0].strip().lower() in TXT_MIME_TYPES:
            return True
        if filename is not None and filename.lower().endswith(TXT_EXTENSIONS):
            return True
        return False

    def extract(self, *, source_version_id: UUID, content: bytes) -> ExtractionResult:
        started = time.perf_counter()
        warnings: list[str] = []
        partial = False
        status = ExtractionStatus.SUCCESS

        try:
            raw_text = content.decode(DEFAULT_ENCODING)
        except UnicodeDecodeError:
            raw_text = content.decode(DEFAULT_ENCODING, errors="replace")
            partial = True
            status = ExtractionStatus.PARTIAL
            warnings.append("invalid utf-8 bytes were replaced during decoding")

        duration_ms = (time.perf_counter() - started) * 1000.0

        metadata = ExtractionMetadata(
            encoding=DEFAULT_ENCODING,
            duration_ms=duration_ms,
            char_count=len(raw_text),
            line_count=raw_text.count("\n") + 1 if raw_text else 0,
            byte_count=len(content),
            partial=partial,
            warnings=warnings,
        )

        return ExtractionResult(
            source_version_id=source_version_id,
            extraction_status=status,
            extractor_name=self.name,
            extractor_version=self.version,
            extracted_at=utc_now(),
            content_hash=sha256_text(raw_text),
            raw_text=raw_text,
            metadata=metadata,
        )
