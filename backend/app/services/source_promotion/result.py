from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class SourceVersionPromotionResult:
    source_version_id: UUID | None
    promotion_status: str
    review_required: bool
    validation_errors: list[str]
    promoted_at: datetime | None
    source_document_id: UUID
    fetch_result_id: UUID
    checksum_sha256: str | None
    notes: str | None
