from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CitationAssemblyGovernanceProviderResult:
    success: bool
    error_category: str | None = None
    error_message: str | None = None
    notes: str | None = None
    provider_name: str | None = None
    provider_version: str | None = None
    citation_id: str | None = None
    assembled_at: datetime | None = None


@dataclass(frozen=True)
class CitationAssemblyGovernanceRunSummary:
    requests_seen: int = 0
    requests_processed: int = 0
    requests_skipped: int = 0
    results_created: int = 0
    failures: int = 0
    requests_replayed: int = 0

    @property
    def requests_failed(self) -> int:
        return self.failures


# TASK-006AB spec aliases (governance-prefixed types remain canonical).
CitationAssemblyWorkerResult = CitationAssemblyGovernanceProviderResult
CitationAssemblyWorkerSummary = CitationAssemblyGovernanceRunSummary
