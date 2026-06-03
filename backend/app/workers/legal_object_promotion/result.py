from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class LegalObjectPromotionProviderResult:
    success: bool
    error_category: str | None = None
    error_message: str | None = None
    notes: str | None = None
    provider_name: str | None = None
    provider_version: str | None = None
    legal_object_id: str | None = None
    legal_object_version_id: UUID | None = None
    created_legal_object: bool = False
    created_version: bool = False


@dataclass(frozen=True)
class LegalObjectPromotionRunSummary:
    requests_seen: int = 0
    requests_processed: int = 0
    requests_skipped: int = 0
    results_created: int = 0
    failures: int = 0
