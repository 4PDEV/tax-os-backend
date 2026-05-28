from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.source_version import SourceVersion
from app.services.source_attachment import (
    AttachmentStateError,
    has_attached_file,
    validate_attachment_state,
)
from app.storage.base import StorageService
from app.storage.checksum import sha256_bytes
from app.storage.local import LocalFileStorage
from app.storage.paths import normalize_storage_path, validate_filename


DEFAULT_UPLOAD_MIME_TYPE = "application/octet-stream"


class SourceUploadError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def resolve_upload_mime_type(content_type: str | None) -> str:
    if content_type and content_type.strip():
        return content_type.strip()
    return DEFAULT_UPLOAD_MIME_TYPE


def upload_source_version_file(
    db: Session,
    storage: StorageService,
    *,
    source_version_id,
    filename: str,
    content: bytes,
    content_type: str | None,
) -> SourceVersion:
    if not content:
        raise SourceUploadError("upload file must not be empty")

    mime_type = resolve_upload_mime_type(content_type)

    validate_filename(filename)

    record = (
        db.query(SourceVersion)
        .filter(SourceVersion.id == source_version_id)
        .first()
    )
    if not record:
        raise SourceUploadError("Source version not found")

    if not isinstance(storage, LocalFileStorage):
        raise SourceUploadError("upload requires local filesystem storage")

    try:
        validate_attachment_state(record, storage)
    except AttachmentStateError as exc:
        raise SourceUploadError(exc.message) from exc

    if has_attached_file(record, storage):
        raise SourceUploadError("source version file is already attached")

    computed_checksum = sha256_bytes(content)
    expected_checksum = record.checksum_sha256.lower()
    if computed_checksum != expected_checksum:
        raise SourceUploadError("upload checksum does not match source version checksum")

    normalized_path = normalize_storage_path(record.storage_path)
    stored = storage.save_bytes(normalized_path, content, overwrite=False)

    record.storage_path = stored.storage_path
    record.file_size = stored.file_size
    record.mime_type = mime_type
    record.retrieved_at = utc_now()

    db.commit()
    db.refresh(record)
    return record
