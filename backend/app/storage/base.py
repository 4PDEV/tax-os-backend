from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StoredObject:
    storage_path: str
    absolute_path: Path
    file_size: int
    checksum_sha256: str


class StorageService(ABC):
    @abstractmethod
    def save_bytes(self, storage_path: str, content: bytes, *, overwrite: bool = False) -> StoredObject:
        """
        Persist bytes at a relative storage path.

        Implementations must prevent unsafe path traversal and return immutable
        metadata for persistence in database records.
        """

    @abstractmethod
    def read_bytes(self, storage_path: str) -> bytes:
        """Read raw bytes from a relative storage path."""
