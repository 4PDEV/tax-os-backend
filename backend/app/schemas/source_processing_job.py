from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.processing_queue import JOB_TYPE_SOURCE_INGESTION, JOB_STATUSES, JOB_TYPES


class SourceProcessingJobCreate(BaseModel):
    source_version_id: UUID
    job_type: str = JOB_TYPE_SOURCE_INGESTION
    priority: int = 0
    max_attempts: int = Field(default=3, ge=1)

    @field_validator("job_type")
    @classmethod
    def job_type_must_be_valid(cls, value: str) -> str:
        if value not in JOB_TYPES:
            raise ValueError(f"invalid job type: {value}")
        return value


class SourceProcessingJobStatusUpdate(BaseModel):
    job_status: str
    last_error: str | None = None

    @field_validator("job_status")
    @classmethod
    def job_status_must_be_valid(cls, value: str) -> str:
        if value not in JOB_STATUSES:
            raise ValueError(f"invalid job status: {value}")
        return value


class SourceProcessingJobRead(BaseModel):
    id: UUID
    source_version_id: UUID
    job_type: str
    job_status: str
    priority: int
    attempt_count: int
    max_attempts: int
    last_error: str | None = None
    queued_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
