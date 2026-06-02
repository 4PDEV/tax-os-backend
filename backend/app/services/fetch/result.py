from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FetchResult:
    fetched_url: str
    final_url: str | None
    fetch_status: str
    fetched_at: datetime | None
    http_status_code: int | None
    content_type: str | None
    content_length: int | None
    checksum_sha256: str | None
    storage_backend: str | None
    storage_path: str | None
    error_category: str | None
    error_message: str | None
    fetcher_name: str
    fetcher_version: str
