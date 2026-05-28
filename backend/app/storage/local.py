from pathlib import Path

from app.storage.base import StorageService, StoredObject
from app.storage.checksum import sha256_bytes
from app.storage.paths import normalize_storage_path, resolve_storage_path


class LocalFileStorage(StorageService):
    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, storage_path: str, content: bytes, *, overwrite: bool = False) -> StoredObject:
        normalized = normalize_storage_path(storage_path)
        absolute_path = resolve_storage_path(self.root_dir, normalized)
        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        if absolute_path.exists() and not overwrite:
            raise FileExistsError(f"storage path already exists: {normalized}")

        with absolute_path.open("wb") as file_obj:
            file_obj.write(content)

        return StoredObject(
            storage_path=normalized,
            absolute_path=absolute_path,
            file_size=len(content),
            checksum_sha256=sha256_bytes(content),
        )

    def read_bytes(self, storage_path: str) -> bytes:
        absolute_path = resolve_storage_path(self.root_dir, storage_path)
        with absolute_path.open("rb") as file_obj:
            return file_obj.read()
