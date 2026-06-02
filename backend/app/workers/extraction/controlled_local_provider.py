from pathlib import Path

from app.models.extraction_trigger_request import ExtractionTriggerRequest
from app.models.source_version import SourceVersion
from app.services.fetch.content_type import detect_content_type
from app.workers.extraction.content import content_fingerprint, extract_text_from_bytes
from app.workers.extraction.result import ExtractionProviderResult
from app.workers.extraction.safety import (
    ExtractionSafetyError,
    enforce_max_content_size,
    resolve_artifact_path,
    validate_supported_content_type,
)

CONTROLLED_LOCAL_EXTRACTOR_NAME = "controlled_local_extraction_provider"
CONTROLLED_LOCAL_EXTRACTOR_VERSION = "0.1.0"


class ControlledLocalExtractionProvider:
    """Reads approved local artifacts only; never uses network, OCR, or PDF parsing."""

    def __init__(self, *, artifact_root: Path, max_content_size_bytes: int = 1024 * 1024):
        self._artifact_root = artifact_root
        self._max_content_size_bytes = max_content_size_bytes

    def run_extraction(
        self,
        source_version: SourceVersion,
        trigger_request: ExtractionTriggerRequest,
    ) -> ExtractionProviderResult:
        _ = trigger_request
        try:
            artifact_path = resolve_artifact_path(
                artifact_root=self._artifact_root,
                storage_path=source_version.storage_path,
            )
            if not artifact_path.exists() or not artifact_path.is_file():
                return ExtractionProviderResult(
                    success=False,
                    error_category="provenance_missing",
                    error_message="artifact file not found",
                    extractor_name=CONTROLLED_LOCAL_EXTRACTOR_NAME,
                    extractor_version=CONTROLLED_LOCAL_EXTRACTOR_VERSION,
                )

            content_type = source_version.mime_type or detect_content_type(artifact_path.name)
            normalized_type = validate_supported_content_type(content_type)

            content = artifact_path.read_bytes()
            enforce_max_content_size(content, max_bytes=self._max_content_size_bytes)

            raw_text, extraction_status = extract_text_from_bytes(
                content=content,
                content_type=normalized_type,
            )
            content_hash, raw_text_length = content_fingerprint(raw_text)

            return ExtractionProviderResult(
                success=True,
                raw_text=raw_text,
                extraction_status=extraction_status,
                content_hash=content_hash,
                raw_text_length=raw_text_length,
                notes=f"controlled local extraction from {artifact_path.name}",
                extractor_name=CONTROLLED_LOCAL_EXTRACTOR_NAME,
                extractor_version=CONTROLLED_LOCAL_EXTRACTOR_VERSION,
            )
        except ExtractionSafetyError as exc:
            return ExtractionProviderResult(
                success=False,
                error_category=exc.error_category,
                error_message=exc.message,
                extractor_name=CONTROLLED_LOCAL_EXTRACTOR_NAME,
                extractor_version=CONTROLLED_LOCAL_EXTRACTOR_VERSION,
            )
