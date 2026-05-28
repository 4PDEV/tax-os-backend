import pytest

from app.models.source_version import SourceVersion
from app.services.source_upload import resolve_upload_mime_type
from app.services.source_attachment import (
    AttachmentStateError,
    get_attachment_status,
    has_attached_file,
    validate_attachment_state,
)
from app.storage.local import LocalFileStorage


def _version(**kwargs) -> SourceVersion:
    record = SourceVersion(
        source_document_id=kwargs.get("source_document_id"),
        version_label=kwargs.get("version_label", "v1"),
        checksum_sha256=kwargs.get("checksum_sha256", "a" * 64),
        storage_path=kwargs.get("storage_path", "rw/vat/v1.pdf"),
        file_size=kwargs.get("file_size"),
        mime_type=kwargs.get("mime_type"),
    )
    return record


def test_resolve_upload_mime_type_defaults_when_missing():
    assert resolve_upload_mime_type(None) == "application/octet-stream"
    assert resolve_upload_mime_type("") == "application/octet-stream"
    assert resolve_upload_mime_type("  ") == "application/octet-stream"
    assert resolve_upload_mime_type("application/pdf") == "application/pdf"


def test_has_attached_file_requires_complete_metadata(tmp_path):
    storage = LocalFileStorage(tmp_path)
    content = b"attached"
    storage.save_bytes("rw/vat/v1.pdf", content)

    pending = _version()
    assert has_attached_file(pending, storage) is False

    complete = _version(file_size=len(content), mime_type="application/pdf")
    assert has_attached_file(complete, storage) is True


def test_validate_attachment_state_rejects_partial_metadata():
    with pytest.raises(AttachmentStateError):
        validate_attachment_state(_version(file_size=10))

    with pytest.raises(AttachmentStateError):
        validate_attachment_state(_version(mime_type="application/pdf"))


def test_get_attachment_status_pending(tmp_path):
    storage = LocalFileStorage(tmp_path)
    status = get_attachment_status(_version(), storage)
    assert status.status == "pending"
    assert status.file_attached is False


def test_get_attachment_status_inconsistent_when_metadata_partial():
    status = get_attachment_status(_version(file_size=10))
    assert status.status == "inconsistent"
    assert status.file_attached is False


def test_get_attachment_status_pending_when_metadata_complete_but_file_missing(tmp_path):
    storage = LocalFileStorage(tmp_path)
    status = get_attachment_status(
        _version(file_size=10, mime_type="application/pdf"),
        storage,
    )
    assert status.status == "pending"
    assert status.file_attached is False
