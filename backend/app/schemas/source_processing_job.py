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


class SourceProcessingJobClaimRequest(BaseModel):
    locked_by: str
    job_type: str | None = None

    @field_validator("locked_by")
    @classmethod
    def locked_by_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("locked_by must not be empty")
        return value.strip()

    @field_validator("job_type")
    @classmethod
    def job_type_must_be_valid_when_provided(cls, value: str | None) -> str | None:
        if value is not None and value not in JOB_TYPES:
            raise ValueError(f"invalid job type: {value}")
        return value


class SourceProcessingJobCompleteRequest(BaseModel):
    completed_by: str
    result_json: dict | None = None

    @field_validator("completed_by")
    @classmethod
    def completed_by_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("completed_by must not be empty")
        return value.strip()


class SourceProcessingJobFailRequest(BaseModel):
    failed_by: str
    last_error: str
    result_json: dict | None = None

    @field_validator("failed_by")
    @classmethod
    def failed_by_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("failed_by must not be empty")
        return value.strip()

    @field_validator("last_error")
    @classmethod
    def last_error_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("last_error must not be empty")
        return value.strip()


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
    locked_at: datetime | None = None
    locked_by: str | None = None
    result_json: dict | None = None
    completed_by: str | None = None
    failed_by: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
