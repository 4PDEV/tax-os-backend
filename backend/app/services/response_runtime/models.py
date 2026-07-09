"""Response runtime envelope models (TASK-010A)."""

from dataclasses import dataclass
from uuid import UUID

CURRENT_CONTRACT_VERSION = "010A-v1"

SUPPORTED_CONTRACT_VERSIONS = frozenset({CURRENT_CONTRACT_VERSION})

RESPONSE_STATUS_COMPLETED = "completed"
RESPONSE_STATUS_FAILED = "failed"

RENDERING_MODE_DETERMINISTIC = "deterministic"

RUNTIME_ERROR_CATEGORIES = frozenset(
    {
        "invalid_response_request",
        "contract_version_unsupported",
        "answer_request_not_found",
        "answer_result_not_found",
        "answer_not_completed",
        "answer_not_deliverable",
        "accepted_result_missing",
        "evidence_count_mismatch",
        "provenance_resolution_failed",
        "citation_format_failed",
        "response_pipeline_unavailable",
    }
)


class ResponseRuntimeError(Exception):
    def __init__(self, message: str, *, error_category: str | None = None):
        self.message = message
        self.error_category = error_category or _category_from_message(message)
        super().__init__(message)


def _category_from_message(message: str) -> str:
    prefix = message.split(":", 1)[0].strip()
    if prefix in RUNTIME_ERROR_CATEGORIES:
        return prefix
    return "response_pipeline_unavailable"


@dataclass(frozen=True)
class ResponseRequest:
    answer_request_id: UUID
    contract_version: str
    include_rendered_citation_text: bool = False
    answer_result_id: UUID | None = None


@dataclass(frozen=True)
class ResponseCitationReference:
    citation_id: str | None
    citation_hash: str | None
    rendered_citation_text: str | None = None


@dataclass(frozen=True)
class ResponseEvidenceEntry:
    presentation_order_index: int
    retrieval_evidence_reference_id: UUID
    ranked_evidence_reference_id: UUID
    legal_object_id: str | None
    source_version_id: UUID | None
    object_identifier: str | None
    location_reference: str | None
    citation_reference: ResponseCitationReference | None
    entry_metadata: dict | None = None


@dataclass(frozen=True)
class ResponseUncertaintyFlag:
    flag_type: str
    severity: str
    message: str
    related_evidence_ids: list[UUID]


@dataclass(frozen=True)
class ResponseMetadata:
    rendering_mode: str
    include_rendered_citation_text: bool
    notes: str | None = None


@dataclass(frozen=True)
class ResponsePackage:
    contract_version: str
    answer_request_id: UUID
    answer_result_id: UUID
    rank_count: int
    evidence_entries: list[ResponseEvidenceEntry]
    uncertainty_flags: list[ResponseUncertaintyFlag]
    response_metadata: ResponseMetadata | None = None


@dataclass(frozen=True)
class ResponseOutcome:
    response_status: str
    response_package: ResponsePackage | None
    error_category: str | None = None
    error_message: str | None = None
