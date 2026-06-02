from pathlib import Path

from app.core.datetime_utils import utc_now
from app.services.fetch.checksum import sha256_bytes
from app.services.fetch.content_type import detect_content_type
from app.services.fetch.contract import ControlledFetcher, FetchRequest
from app.services.fetch.result import FetchResult
from app.services.fetch.safety import (
    FetchSafetyError,
    enforce_fetch_mode,
    enforce_max_content_size,
    reject_network_schemes,
    resolve_fixture_path,
)


class LocalFixtureFetcher(ControlledFetcher):
    name = "local-fixture-fetcher"
    version = "0.1.0"

    def __init__(self, *, fixture_root: Path, max_content_size_bytes: int = 1024 * 1024):
        self._fixture_root = fixture_root
        self._max_content_size_bytes = max_content_size_bytes

    def fetch(self, fetch_request: FetchRequest) -> FetchResult:
        try:
            enforce_fetch_mode(fetch_request)
            if not fetch_request.local_fixture_mode:
                raise FetchSafetyError(
                    "LocalFixtureFetcher requires local_fixture_mode=True",
                    error_category="blocked",
                )
            reject_network_schemes(fetch_request.requested_url)
            fixture_path = resolve_fixture_path(
                fixture_root=self._fixture_root,
                requested_url=fetch_request.requested_url,
            )
            if not fixture_path.exists() or not fixture_path.is_file():
                return self._failure(
                    fetch_request=fetch_request,
                    error_category="unexpected_content",
                    error_message="fixture file not found",
                )

            content_type = detect_content_type(fixture_path.name)
            if content_type is None:
                return self._failure(
                    fetch_request=fetch_request,
                    error_category="unsupported_content_type",
                    error_message="unsupported fixture content type",
                )

            content = fixture_path.read_bytes()
            enforce_max_content_size(content, max_bytes=self._max_content_size_bytes)

            return FetchResult(
                fetched_url=fetch_request.requested_url,
                final_url=str(fixture_path),
                fetch_status="success",
                fetched_at=utc_now(),
                http_status_code=None,
                content_type=content_type,
                content_length=len(content),
                checksum_sha256=sha256_bytes(content),
                storage_backend="local_test",
                storage_path=str(fixture_path),
                error_category=None,
                error_message=None,
                fetcher_name=self.name,
                fetcher_version=self.version,
            )
        except FetchSafetyError as exc:
            return self._failure(
                fetch_request=fetch_request,
                error_category=exc.error_category,
                error_message=exc.message,
                fetch_status="blocked" if exc.error_category == "blocked" else "failed",
            )

    def _failure(
        self,
        *,
        fetch_request: FetchRequest,
        error_category: str,
        error_message: str,
        fetch_status: str = "failed",
    ) -> FetchResult:
        return FetchResult(
            fetched_url=fetch_request.requested_url,
            final_url=None,
            fetch_status=fetch_status,
            fetched_at=None,
            http_status_code=None,
            content_type=None,
            content_length=None,
            checksum_sha256=None,
            storage_backend=None,
            storage_path=None,
            error_category=error_category,
            error_message=error_message,
            fetcher_name=self.name,
            fetcher_version=self.version,
        )
