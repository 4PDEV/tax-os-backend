from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class SourceVersionPromotionRequest:
    fetch_result_id: UUID
    source_document_id: UUID
    requested_by_actor_type: str
    promotion_reason: str
    monitoring_candidate_id: UUID | None = None
    change_detection_result_id: UUID | None = None
    proposed_version_label: str | None = None
    publication_date: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    requested_by_actor_identifier: str | None = None
    notes: str | None = None
