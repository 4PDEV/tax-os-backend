import hashlib

TEXT_HASH_ENCODING = "utf-8"


def sha256_text(text: str) -> str:
    """Return the SHA-256 hex digest of extracted raw text.

    The hash is computed over the UTF-8 encoded text exactly as extracted.
    It underpins integrity validation, reproducibility, and change detection.
    No normalization or transformation is applied before hashing.
    """
    return hashlib.sha256(text.encode(TEXT_HASH_ENCODING)).hexdigest()
