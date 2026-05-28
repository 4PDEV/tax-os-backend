from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.source_version import SourceVersion
from app.storage.base import StorageService
from app.storage.checksum import sha256_bytes
from app.storage.local import LocalFileStorage
from app.storage.paths import normalize_storage_path, resolve_storage_path, validate_filename


class SourceUploadError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def _storage_file_exists(storage: LocalFileStorage, storage_path: str) -> bool:
    normalized = normalize_storage_path(storage_path)
    return resolve_storage_path(storage.root_dir, normalized).exists()


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

    normalized_path = normalize_storage_path(record.storage_path)
    if _storage_file_exists(storage, normalized_path):
        raise SourceUploadError("source file already uploaded for this version")

    computed_checksum = sha256_bytes(content)
    expected_checksum = record.checksum_sha256.lower()
    if computed_checksum != expected_checksum:
        raise SourceUploadError("upload checksum does not match source version checksum")

    stored = storage.save_bytes(normalized_path, content, overwrite=False)

    record.storage_path = stored.storage_path
    record.file_size = stored.file_size
    record.mime_type = content_type or record.mime_type
    record.retrieved_at = utc_now()

    db.commit()
    db.refresh(record)
    return record
