"""API delivery envelope models (TASK-011A)."""

from dataclasses import dataclass
from uuid import UUID

CURRENT_API_CONTRACT_VERSION = "011A-v1"

SUPPORTED_API_CONTRACT_VERSIONS = frozenset({CURRENT_API_CONTRACT_VERSION})

API_TO_RUNTIME_CONTRACT_VERSION = {
    "011A-v1": "010A-v1",
}

DELIVERY_STATUS_COMPLETED = "completed"
DELIVERY_STATUS_FAILED = "failed"


@dataclass(frozen=True)
class ApiDeliveryRequest:
    answer_request_id: UUID
    api_contract_version: str = CURRENT_API_CONTRACT_VERSION
    include_rendered_citation_text: bool = False
    answer_result_id: UUID | None = None


@dataclass(frozen=True)
class ApiDeliveryMetadata:
    rendering_mode: str
    include_rendered_citation_text: bool
    notes: str | None = None


@dataclass(frozen=True)
class ApiDeliveryCitationReference:
    citation_id: str | None
    citation_hash: str | None
    rendered_citation_text: str | None = None


@dataclass(frozen=True)
class ApiDeliveryEvidenceEntry:
    presentation_order_index: int
    retrieval_evidence_reference_id: UUID
    ranked_evidence_reference_id: UUID
    legal_object_id: str | None
    source_version_id: UUID | None
    object_identifier: str | None
    location_reference: str | None
    citation_reference: ApiDeliveryCitationReference | None
    entry_metadata: dict | None = None


@dataclass(frozen=True)
class ApiDeliveryUncertaintyFlag:
    flag_type: str
    severity: str
    message: str
    related_evidence_ids: list[UUID]


@dataclass(frozen=True)
class ApiDeliveryError:
    error_code: str
    error_message: str | None = None


@dataclass(frozen=True)
class ApiDeliveryResponse:
    api_contract_version: str
    delivery_status: str
    answer_request_id: UUID
    answer_result_id: UUID | None = None
    rank_count: int | None = None
    evidence_entries: list[ApiDeliveryEvidenceEntry] | None = None
    uncertainty_flags: list[ApiDeliveryUncertaintyFlag] | None = None
    delivery_metadata: ApiDeliveryMetadata | None = None
    error: ApiDeliveryError | None = None


@dataclass(frozen=True)
class ApiDeliveryOutcome:
    http_status: int
    response: ApiDeliveryResponse
