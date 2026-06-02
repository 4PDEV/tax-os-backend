from pathlib import Path


SUPPORTED_CONTENT_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".html": "text/html",
    ".htm": "text/html",
    ".txt": "text/plain",
    ".xml": "application/xml",
    ".json": "application/json",
}


def detect_content_type(path: str) -> str | None:
    suffix = Path(path).suffix.lower()
    return SUPPORTED_CONTENT_TYPES.get(suffix)
