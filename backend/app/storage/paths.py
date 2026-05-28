from pathlib import Path


def normalize_storage_path(storage_path: str) -> str:
    raw = storage_path.strip()
    if not raw:
        raise ValueError("storage_path must not be empty")

    normalized = raw.replace("\\", "/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    normalized = normalized.strip("/")
    if not normalized:
        raise ValueError("storage_path must not be root-only")

    if any(part in {"", ".", ".."} for part in normalized.split("/")):
        raise ValueError("storage_path contains invalid path segments")

    return normalized


def validate_filename(filename: str) -> str:
    safe = filename.strip()
    if not safe:
        raise ValueError("filename must not be empty")
    if "/" in safe or "\\" in safe:
        raise ValueError("filename must not include path separators")
    if safe in {".", ".."}:
        raise ValueError("filename must not be dot path")
    return safe


def resolve_storage_path(base_dir: str | Path, storage_path: str) -> Path:
    base = Path(base_dir).resolve()
    normalized = normalize_storage_path(storage_path)
    resolved = (base / normalized).resolve()
    if base not in resolved.parents and resolved != base:
        raise ValueError("storage_path resolves outside storage root")
    return resolved
