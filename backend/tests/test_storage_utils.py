from pathlib import Path

import pytest

from app.storage.checksum import sha256_bytes, sha256_file
from app.storage.local import LocalFileStorage
from app.storage.paths import normalize_storage_path, validate_filename


def test_sha256_bytes_and_file_match(tmp_path: Path):
    content = b"deterministic-content"
    file_path = tmp_path / "sample.bin"
    file_path.write_bytes(content)

    assert sha256_bytes(content) == sha256_file(file_path)


def test_normalize_storage_path_rejects_unsafe_values():
    with pytest.raises(ValueError):
        normalize_storage_path("../escape.txt")
    with pytest.raises(ValueError):
        normalize_storage_path("")
    with pytest.raises(ValueError):
        normalize_storage_path("/")


def test_validate_filename_rejects_path_values():
    with pytest.raises(ValueError):
        validate_filename("a/b.txt")
    with pytest.raises(ValueError):
        validate_filename("..")


def test_local_storage_save_and_read(tmp_path: Path):
    storage = LocalFileStorage(tmp_path)
    content = b"raw-source-file"

    stored = storage.save_bytes("rw/vat/law.pdf", content)
    assert stored.storage_path == "rw/vat/law.pdf"
    assert stored.file_size == len(content)
    assert stored.absolute_path.exists()
    assert stored.checksum_sha256 == sha256_bytes(content)
    assert storage.read_bytes("rw/vat/law.pdf") == content


def test_local_storage_rejects_overwrite_without_flag(tmp_path: Path):
    storage = LocalFileStorage(tmp_path)
    storage.save_bytes("rw/vat/law.pdf", b"first")

    with pytest.raises(FileExistsError):
        storage.save_bytes("rw/vat/law.pdf", b"second")


def test_local_storage_allows_overwrite_with_flag(tmp_path: Path):
    storage = LocalFileStorage(tmp_path)
    storage.save_bytes("rw/vat/law.pdf", b"first")

    stored = storage.save_bytes("rw/vat/law.pdf", b"second", overwrite=True)
    assert stored.file_size == len(b"second")
    assert storage.read_bytes("rw/vat/law.pdf") == b"second"
