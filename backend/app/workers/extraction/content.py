import json
import re
from html.parser import HTMLParser

from app.services.extraction.enums import ExtractionStatus
from app.services.extraction.hashing import sha256_text
from app.workers.extraction.safety import ExtractionSafetyError


class _HTMLTextCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if stripped:
            self._parts.append(stripped)

    def text(self) -> str:
        return "\n".join(self._parts)


def extract_text_from_bytes(*, content: bytes, content_type: str) -> tuple[str, str]:
    """Return (raw_text, extraction_status) for supported controlled formats."""
    if content_type == "text/plain":
        try:
            return content.decode("utf-8"), ExtractionStatus.SUCCESS.value
        except UnicodeDecodeError:
            return content.decode("utf-8", errors="replace"), ExtractionStatus.PARTIAL.value

    if content_type == "text/html":
        html = content.decode("utf-8", errors="replace")
        collector = _HTMLTextCollector()
        collector.feed(html)
        text = collector.text()
        if not text:
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()
        return text, ExtractionStatus.SUCCESS.value

    if content_type == "application/json":
        decoded = content.decode("utf-8")
        try:
            payload = json.loads(decoded)
            return (
                json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False),
                ExtractionStatus.SUCCESS.value,
            )
        except json.JSONDecodeError as exc:
            raise ExtractionSafetyError(
                f"invalid json content: {exc}",
                error_category="invalid_request",
            ) from exc

    if content_type == "application/xml":
        return content.decode("utf-8"), ExtractionStatus.SUCCESS.value

    raise ExtractionSafetyError(
        f"unsupported content type: {content_type}",
        error_category="unsupported_source_type",
    )


def content_fingerprint(raw_text: str) -> tuple[str, int]:
    return sha256_text(raw_text), len(raw_text)
