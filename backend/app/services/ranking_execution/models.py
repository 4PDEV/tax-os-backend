from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class RankingEvidenceRow:
    """In-memory sort input — sort-time reads only; not persisted on ranked rows."""

    retrieval_evidence_reference_id: UUID
    retrieval_result_id: UUID
    deterministic_order_index: int
    legal_object_id: str
    legal_object_version_id: UUID
    source_version_id: UUID
    source_document_id: UUID | None
    citation_hash: str | None
    object_identifier: str | None
    effective_from: date | None


@dataclass(frozen=True)
class RankingExecutionOutcome:
    ranking_request_id: UUID
    ranking_result_id: UUID
    ranking_status: str
    rank_count: int
    error_category: str | None = None
    error_message: str | None = None


class RankingExecutionError(Exception):
    def __init__(self, category: str, message: str):
        self.category = category
        self.message = message
        super().__init__(message)
