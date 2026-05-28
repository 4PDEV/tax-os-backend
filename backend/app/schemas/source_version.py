from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.services.ingestion_status import INGESTION_STATUS_NOT_STARTED, INGESTION_STATUSES


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
    ingestion_status: str = INGESTION_STATUS_NOT_STARTED
    supersedes_version_id: UUID | None = None
    notes: str | None = None


class SourceVersionCreate(SourceVersionBase):
    @field_validator("ingestion_status")
    @classmethod
    def ingestion_status_must_be_not_started(cls, value: str) -> str:
        if value != INGESTION_STATUS_NOT_STARTED:
            raise ValueError("ingestion_status must be not_started on create")
        return value


class SourceVersionIngestionStatusUpdate(BaseModel):
    ingestion_status: str

    @field_validator("ingestion_status")
    @classmethod
    def ingestion_status_must_be_valid(cls, value: str) -> str:
        if value not in INGESTION_STATUSES:
            raise ValueError(f"invalid ingestion status: {value}")
        return value


class SourceVersionRead(SourceVersionBase):
    id: UUID
    created_at: datetime
    file_attached: bool = False
    attachment_status: str = "pending"

    model_config = ConfigDict(from_attributes=True)
