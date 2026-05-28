import hashlib
from pathlib import Path


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: str | Path, chunk_size: int = 8192) -> str:
    hasher = hashlib.sha256()
    file_path = Path(path)
    with file_path.open("rb") as file_obj:
        while True:
            chunk = file_obj.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()
