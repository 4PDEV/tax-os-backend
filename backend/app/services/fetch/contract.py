from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.services.fetch.result import FetchResult


@dataclass(frozen=True)
class FetchRequest:
    requested_url: str
    requested_by_actor_type: str
    requested_by_actor_identifier: str | None
    request_reason: str
    dry_run: bool
    local_fixture_mode: bool = False
    monitoring_candidate_id: UUID | None = None
    source_allowlist_entry_id: UUID | None = None
    notes: str | None = None


class ControlledFetcher(Protocol):
    def fetch(self, fetch_request: FetchRequest) -> FetchResult:
        """Execute a bounded controlled fetch operation."""
