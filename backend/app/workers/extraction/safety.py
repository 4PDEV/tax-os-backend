from pathlib import Path


class ExtractionSafetyError(Exception):
    def __init__(self, message: str, *, error_category: str):
        self.message = message
        self.error_category = error_category
        super().__init__(message)


SUPPORTED_EXTRACTION_CONTENT_TYPES = frozenset(
    {
        "text/plain",
        "text/html",
        "application/json",
        "application/xml",
    }
)


def reject_network_storage_path(storage_path: str) -> None:
    lowered = storage_path.strip().lower()
    if lowered.startswith(("http://", "https://", "ftp://")):
        raise ExtractionSafetyError(
            "external network storage paths are prohibited",
            error_category="blocked",
        )


def resolve_artifact_path(*, artifact_root: Path, storage_path: str) -> Path:
    if not storage_path or not storage_path.strip():
        raise ExtractionSafetyError("storage_path is required", error_category="provenance_missing")

    reject_network_storage_path(storage_path)

    normalized = storage_path.strip().replace("\\", "/").lstrip("/")
    for prefix in ("fixtures/fetch/", "fixtures/", "fetch/"):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
            break

    if not normalized:
        raise ExtractionSafetyError("empty artifact path is not allowed", error_category="provenance_missing")

    relative = Path(normalized)
    if relative.is_absolute() or ".." in relative.parts:
        raise ExtractionSafetyError(
            "path traversal is prohibited",
            error_category="blocked",
        )

    full_path = (artifact_root / relative).resolve()
    root = artifact_root.resolve()
    if root not in full_path.parents and full_path != root:
        raise ExtractionSafetyError(
            "artifact path outside approved root is prohibited",
            error_category="blocked",
        )
    return full_path


def enforce_max_content_size(content: bytes, *, max_bytes: int) -> None:
    if len(content) > max_bytes:
        raise ExtractionSafetyError(
            f"content exceeds max size of {max_bytes} bytes",
            error_category="invalid_request",
        )


def validate_supported_content_type(content_type: str | None) -> str:
    if content_type is None:
        raise ExtractionSafetyError(
            "unsupported or unknown content type",
            error_category="unsupported_source_type",
        )
    normalized = content_type.split(";")[0].strip().lower()
    if normalized not in SUPPORTED_EXTRACTION_CONTENT_TYPES:
        raise ExtractionSafetyError(
            f"unsupported content type for controlled extraction: {normalized}",
            error_category="unsupported_source_type",
        )
    return normalized
