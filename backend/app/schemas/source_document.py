from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SourceDocumentBase(BaseModel):
    country_id: UUID
    tax_type_id: UUID | None = None
    source_type: str
    authority_level: str
    title: str
    short_title: str | None = None
    issuing_authority: str | None = None
    official_reference: str | None = None
    source_url: str | None = None
    language: str = "en"
    status: str = "active"


class SourceDocumentCreate(SourceDocumentBase):
    pass


class SourceDocumentUpdate(BaseModel):
    tax_type_id: UUID | None = None
    source_type: str | None = None
    authority_level: str | None = None
    title: str | None = None
    short_title: str | None = None
    issuing_authority: str | None = None
    official_reference: str | None = None
    source_url: str | None = None
    language: str | None = None
    status: str | None = None


class SourceDocumentRead(SourceDocumentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
