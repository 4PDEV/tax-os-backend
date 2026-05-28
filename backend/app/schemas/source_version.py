from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SourceVersionBase(BaseModel):
    source_document_id: UUID
    version_label: str
    publication_date: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    enforcement_date: date | None = None
    retrieved_at: datetime | None = None
    checksum_sha256: str
    storage_path: str
    mime_type: str | None = None
    file_size: int | None = None
    version_status: str = "active"
    supersedes_version_id: UUID | None = None
    notes: str | None = None


class SourceVersionCreate(SourceVersionBase):
    pass


class SourceVersionRead(SourceVersionBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
