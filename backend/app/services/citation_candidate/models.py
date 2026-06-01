from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CandidateStatus(str, Enum):
    """Deterministic citation candidate readiness status."""

    READY = "ready"
    SOURCE_TRACEABILITY_FAILED = "source_traceability_failed"
    INTEGRITY_FAILED = "integrity_failed"
    DATE_AMBIGUOUS = "date_ambiguous"
    DATE_NOT_APPLICABLE = "date_not_applicable"
    MISSING_EFFECTIVE_DATE = "missing_effective_date"


class CitationCandidateRequest(BaseModel):
    """Request to build citation candidates from retrieval/resolution inputs."""

    model_config = ConfigDict(extra="forbid")

    jurisdiction_code: str
    tax_type_code: str | None = None
    legal_object_id: str | None = None
    source_document_id: UUID | None = None
    source_version_id: UUID | None = None
    effective_on: date | None = None
    include_superseded: bool = False
    include_archived: bool = False
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class CitationCandidate(BaseModel):
    """Citation-ready candidate DTO — not a final formatted citation."""

    model_config = ConfigDict(extra="forbid")

    legal_object_id: str
    legal_object_version_id: UUID
    source_document_id: UUID
    source_version_id: UUID
    jurisdiction_code: str
    tax_type_code: str | None = None
    source_type: str
    authority_level: str
    source_title: str
    source_short_title: str | None = None
    issuing_authority: str | None = None
    official_reference: str | None = None
    source_url: str | None = None
    language: str | None = None
    object_type: str
    object_identifier: str
    object_label: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    publication_date: date | None = None
    retrieved_at: datetime | None = None
    canonical_text: str
    text_hash: str
    integrity_hash: str
    candidate_created_at: datetime
    candidate_status: CandidateStatus
