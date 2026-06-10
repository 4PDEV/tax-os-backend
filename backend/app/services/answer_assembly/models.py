"""In-memory answer assembly DTOs (TASK-009A) — not ORM."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.models.ranked_evidence_reference import RankedEvidenceReference
from app.models.ranking_request import RankingRequest
from app.models.ranking_result import RankingResult

CURRENT_CONTRACT_VERSION = "009A-v1"

ANSWER_ERROR_CATEGORIES = frozenset(
    {
        "ranking_result_not_completed",
        "accepted_ranking_result_missing",
        "ranked_evidence_missing",
        "evidence_count_mismatch",
        "provenance_chain_incomplete",
        "citation_reference_incomplete",
        "retrieval_result_mismatch",
        "assembly_validation_failed",
        "answer_pipeline_unavailable",
        "unknown_failure",
    }
)


@dataclass(frozen=True)
class CitationReference:
    citation_id: str | None
    citation_hash: str | None
    rendered_citation_text: str | None = None


@dataclass(frozen=True)
class UncertaintyFlag:
    flag_type: str
    severity: str
    message: str
    related_evidence_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True)
class AnswerAssemblyMetadata:
    requested_by_actor_type: str | None = None
    assembly_mode: str = "deterministic"
    display_flags: dict | None = None
    notes: str | None = None


@dataclass(frozen=True)
class AnswerEvidenceEntry:
    presentation_order_index: int
    ranked_evidence_reference_id: UUID
    retrieval_evidence_reference_id: UUID
    retrieval_result_id: UUID
    legal_object_id: str
    legal_object_version_id: UUID
    source_version_id: UUID
    citation_reference: CitationReference | None
    object_identifier: str | None
    location_reference: str | None
    citation_reference_status: str
    entry_metadata: dict | None = None


@dataclass(frozen=True)
class AnswerPackage:
    answer_package_id: UUID
    contract_version: str
    ranking_request_id: UUID
    retrieval_result_id: UUID
    terminal_ranking_result_id: UUID
    accepted_ranking_result_id: UUID
    ranking_profile: str
    rank_count: int
    answer_status: str
    assembled_at: datetime
    evidence_entries: tuple[AnswerEvidenceEntry, ...]
    uncertainty_flags: tuple[UncertaintyFlag, ...]
    assembly_metadata: AnswerAssemblyMetadata
    error_category: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class AnswerAssemblyOutcome:
    answer_status: str
    answer_package: AnswerPackage | None = None
    error_category: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class RankingAssemblyInputs:
    ranking_request: RankingRequest
    terminal_ranking_result: RankingResult
    accepted_ranking_result: RankingResult
    ranked_rows: tuple[RankedEvidenceReference, ...]


class AnswerAssemblyError(Exception):
    def __init__(self, category: str, message: str):
        if category not in ANSWER_ERROR_CATEGORIES:
            raise ValueError(f"invalid error_category: {category}")
        self.category = category
        self.message = message
        super().__init__(message)
