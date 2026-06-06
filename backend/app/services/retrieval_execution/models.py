from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class EvidenceCandidate:
    legal_object_id: str
    legal_object_version_id: UUID
    source_version_id: UUID
    source_document_id: UUID
    effective_from: date | None
    object_identifier: str
    object_type: str
    object_label: str
    citation_id: str | None = None
    citation_hash: str | None = None
    location_reference: str | None = None


@dataclass(frozen=True)
class RetrievalExecutionOutcome:
    evidence_count: int
    notes: str
