from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalRuntimeProviderResult:
    success: bool
    error_category: str | None = None
    error_message: str | None = None
    notes: str | None = None
    provider_name: str | None = None
    provider_version: str | None = None
    result_count: int | None = None


@dataclass(frozen=True)
class RetrievalRuntimeRunSummary:
    requests_seen: int = 0
    requests_processed: int = 0
    requests_skipped: int = 0
    results_created: int = 0
    failures: int = 0
    requests_replayed: int = 0

    @property
    def requests_failed(self) -> int:
        return self.failures
