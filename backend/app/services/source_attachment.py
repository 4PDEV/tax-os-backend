from dataclasses import dataclass

from app.models.source_version import SourceVersion
from app.storage.local import LocalFileStorage
from app.storage.paths import normalize_storage_path, resolve_storage_path


class AttachmentStateError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class AttachmentStatus:
    status: str
    file_attached: bool


def _storage_file_exists(storage: LocalFileStorage, storage_path: str) -> bool:
    normalized = normalize_storage_path(storage_path)
    return resolve_storage_path(storage.root_dir, normalized).exists()


def _metadata_complete(version: SourceVersion) -> bool:
    return bool(
        version.storage_path
        and version.checksum_sha256
        and version.file_size is not None
        and version.mime_type
    )


def has_attached_file(version: SourceVersion, storage: LocalFileStorage | None = None) -> bool:
    if not _metadata_complete(version):
        return False
    if storage is None:
        return True
    return _storage_file_exists(storage, version.storage_path)


def validate_attachment_state(
    version: SourceVersion,
    storage: LocalFileStorage | None = None,
) -> None:
    size_set = version.file_size is not None
    mime_set = bool(version.mime_type)

    if size_set != mime_set:
        raise AttachmentStateError(
            "inconsistent attachment metadata: file_size and mime_type must both be set or both unset"
        )

    if storage is None:
        return

    file_on_disk = _storage_file_exists(storage, version.storage_path)
    metadata_complete = _metadata_complete(version)

    if file_on_disk and not metadata_complete:
        raise AttachmentStateError(
            "storage file exists but attachment metadata is incomplete"
        )


def get_attachment_status(
    version: SourceVersion,
    storage: LocalFileStorage | None = None,
) -> AttachmentStatus:
    try:
        validate_attachment_state(version, storage)
    except AttachmentStateError:
        return AttachmentStatus(status="inconsistent", file_attached=False)

    if has_attached_file(version, storage):
        return AttachmentStatus(status="attached", file_attached=True)

    return AttachmentStatus(status="pending", file_attached=False)


def build_source_version_read(version: SourceVersion, storage: LocalFileStorage | None) -> dict:
    attachment = get_attachment_status(version, storage)
    payload = {
        column.name: getattr(version, column.name)
        for column in version.__table__.columns
    }
    payload["file_attached"] = attachment.file_attached
    payload["attachment_status"] = attachment.status
    return payload
