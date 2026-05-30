from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResolutionStatus(str, Enum):
    """Deterministic resolution outcome for a legal object on a given date."""

    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    AMBIGUOUS_OVERLAP = "ambiguous_overlap"
    MISSING_EFFECTIVE_DATE = "missing_effective_date"
    INTEGRITY_FAILED = "integrity_failed"


RESOLUTION_STATUS_VALUES: frozenset[str] = frozenset(s.value for s in ResolutionStatus)


class EffectiveDateResolutionRequest(BaseModel):
    """Deterministic effective-date resolution criteria."""

    model_config = ConfigDict(extra="forbid")

    jurisdiction_code: str
    tax_type_code: str | None = None
    legal_object_id: str | None = None
    source_document_id: UUID | None = None
    source_version_id: UUID | None = None
    effective_on: date
    include_superseded: bool = False
    include_archived: bool = False
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class EffectiveDateResolutionResult(BaseModel):
    """Resolution outcome for one legal object on a given date."""

    model_config = ConfigDict(extra="forbid")

    legal_object_id: str
    legal_object_version_id: UUID | None
    source_document_id: UUID
    source_version_id: UUID
    object_type: str
    object_identifier: str
    status: str
    effective_from: date | None
    effective_to: date | None
    canonical_text: str
    text_hash: str
    integrity_hash: str
    resolution_date: date
    resolution_status: ResolutionStatus
