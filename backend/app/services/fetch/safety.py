from pathlib import Path
from urllib.parse import urlparse

from app.services.fetch.contract import FetchRequest


class FetchSafetyError(Exception):
    def __init__(self, message: str, *, error_category: str):
        self.message = message
        self.error_category = error_category
        super().__init__(message)


def enforce_fetch_mode(fetch_request: FetchRequest) -> None:
    if not fetch_request.dry_run and not fetch_request.local_fixture_mode:
        raise FetchSafetyError(
            "dry_run=True is required unless local_fixture_mode=True",
            error_category="blocked",
        )


def reject_network_schemes(requested_url: str) -> None:
    parsed = urlparse(requested_url)
    if parsed.scheme in {"http", "https"}:
        raise FetchSafetyError(
            "external network fetching is prohibited in TASK-006H",
            error_category="blocked",
        )
    if parsed.scheme == "file":
        raise FetchSafetyError(
            "file scheme absolute access is prohibited; use fixture scheme",
            error_category="blocked",
        )
    if parsed.scheme and parsed.scheme not in {"fixture", "dry-run"}:
        raise FetchSafetyError(
            f"unsupported fetch URL scheme: {parsed.scheme}",
            error_category="blocked",
        )


def resolve_fixture_path(*, fixture_root: Path, requested_url: str) -> Path:
    parsed = urlparse(requested_url)
    if parsed.scheme not in {"fixture", ""}:
        raise FetchSafetyError(
            "fixture fetch requires fixture or relative scheme",
            error_category="blocked",
        )

    if parsed.scheme == "fixture":
        candidate = "/".join(part for part in [parsed.netloc, parsed.path.lstrip("/")] if part)
    else:
        candidate = parsed.path.lstrip("/")
    if not candidate:
        raise FetchSafetyError("empty fixture path is not allowed", error_category="blocked")

    full_path = (fixture_root / candidate).resolve()
    root = fixture_root.resolve()
    if root not in full_path.parents and full_path != root:
        raise FetchSafetyError(
            "path traversal or outside fixture root is prohibited",
            error_category="blocked",
        )
    return full_path


def enforce_max_content_size(content: bytes, *, max_bytes: int) -> None:
    if len(content) > max_bytes:
        raise FetchSafetyError(
            f"content exceeds max size of {max_bytes} bytes",
            error_category="content_too_large",
        )
