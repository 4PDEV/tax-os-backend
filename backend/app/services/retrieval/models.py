from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LegalObjectRetrievalRequest(BaseModel):
    """Deterministic retrieval criteria for persisted legal objects."""

    model_config = ConfigDict(extra="forbid")

    jurisdiction_code: str
    tax_type_code: str | None = None
    source_document_id: UUID | None = None
    source_version_id: UUID | None = None
    legal_object_type: str | None = None
    object_identifier: str | None = None
    effective_on: date | None = None
    include_superseded: bool = False
    include_archived: bool = False
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class LegalObjectRetrievalResult(BaseModel):
    """Single deterministic retrieval result — no summarization or AI fields."""

    model_config = ConfigDict(extra="forbid")

    legal_object_id: str
    source_document_id: UUID
    source_version_id: UUID
    object_type: str
    object_identifier: str
    status: str
    effective_from: date | None
    effective_to: date | None
    canonical_text: str
    integrity_hash: str
    text_hash: str
    retrieval_timestamp: datetime
