from app.services.fetch.checksum import sha256_bytes
from app.services.fetch.content_type import SUPPORTED_CONTENT_TYPES, detect_content_type
from app.services.fetch.contract import ControlledFetcher, FetchRequest
from app.services.fetch.dry_run_fetcher import DryRunFetcher
from app.services.fetch.fetcher import execute_fetch
from app.services.fetch.local_fixture_fetcher import LocalFixtureFetcher
from app.services.fetch.persistence import (
    FetchPersistenceError,
    create_fetch_request,
    create_persisted_fetch_request_from_contract,
    get_fetch_request,
    get_latest_fetch_result_for_request,
    list_fetch_results_for_request,
    persist_fetch_result,
    persist_result_from_contract,
)
from app.services.fetch.result import FetchResult
from app.services.fetch.safety import FetchSafetyError

__all__ = [
    "ControlledFetcher",
    "FetchRequest",
    "FetchResult",
    "FetchSafetyError",
    "DryRunFetcher",
    "LocalFixtureFetcher",
    "FetchPersistenceError",
    "create_fetch_request",
    "persist_fetch_result",
    "get_fetch_request",
    "list_fetch_results_for_request",
    "get_latest_fetch_result_for_request",
    "create_persisted_fetch_request_from_contract",
    "persist_result_from_contract",
    "SUPPORTED_CONTENT_TYPES",
    "detect_content_type",
    "sha256_bytes",
    "execute_fetch",
]
