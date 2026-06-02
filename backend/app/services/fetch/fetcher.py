from app.services.fetch.contract import ControlledFetcher, FetchRequest
from app.services.fetch.result import FetchResult


def execute_fetch(fetcher: ControlledFetcher, fetch_request: FetchRequest) -> FetchResult:
    return fetcher.fetch(fetch_request)
