from app.core.datetime_utils import utc_now
from app.services.fetch.checksum import sha256_bytes
from app.services.fetch.contract import ControlledFetcher, FetchRequest
from app.services.fetch.result import FetchResult
from app.services.fetch.safety import enforce_fetch_mode, reject_network_schemes


class DryRunFetcher(ControlledFetcher):
    name = "dry-run-fetcher"
    version = "0.1.0"

    def fetch(self, fetch_request: FetchRequest) -> FetchResult:
        enforce_fetch_mode(fetch_request)
        reject_network_schemes(fetch_request.requested_url)

        synthetic = b"Dry run controlled fetch content."
        return FetchResult(
            fetched_url=fetch_request.requested_url,
            final_url=fetch_request.requested_url,
            fetch_status="success",
            fetched_at=utc_now(),
            http_status_code=None,
            content_type="text/plain",
            content_length=len(synthetic),
            checksum_sha256=sha256_bytes(synthetic),
            storage_backend="local_test",
            storage_path=None,
            error_category=None,
            error_message=None,
            fetcher_name=self.name,
            fetcher_version=self.version,
        )
