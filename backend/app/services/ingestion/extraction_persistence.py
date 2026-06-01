from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.extracted_text import ExtractedText
from app.models.extraction_run import ExtractionRun
from app.models.source_version import SourceVersion
from app.services.extraction.enums import ExtractionStatus
from app.services.ingestion.enums import (
    STORAGE_BACKEND_DATABASE,
    PipelineArtifactState,
)
from app.services.ingestion.errors import IngestionPersistenceError
from app.services.ingestion.hashing import sha256_text
from app.services.ingestion.immutability import assert_extracted_text_immutable
from app.services.ingestion.ingestion_state import get_current_pipeline_state, update_ingestion_state

EXTRACTION_RUN_STATUSES = frozenset(status.value for status in ExtractionStatus)


def create_extraction_run(
    session: Session,
    *,
    source_version_id: UUID,
    extractor_name: str,
    extractor_version: str,
    extraction_status: str,
    started_at: datetime,
    completed_at: datetime | None = None,
    content_hash: str | None = None,
    raw_text_length: int | None = None,
    error_message: str | None = None,
) -> ExtractionRun:
    if extraction_status not in EXTRACTION_RUN_STATUSES:
        raise IngestionPersistenceError(f"invalid extraction_status: {extraction_status}")

    version = session.get(SourceVersion, source_version_id)
    if version is None:
        raise IngestionPersistenceError(f"source_version not found: {source_version_id}")

    run = ExtractionRun(
        source_version_id=source_version_id,
        extractor_name=extractor_name,
        extractor_version=extractor_version,
        extraction_status=extraction_status,
        started_at=started_at,
        completed_at=completed_at,
        content_hash=content_hash,
        raw_text_length=raw_text_length,
        error_message=error_message,
        created_at=utc_now(),
    )
    session.add(run)
    session.flush()

    if extraction_status == ExtractionStatus.FAILED.value:
        update_ingestion_state(
            session,
            source_version_id=source_version_id,
            pipeline_state=PipelineArtifactState.FAILED.value,
            extraction_run_id=run.id,
        )
    elif extraction_status == ExtractionStatus.PARTIAL.value:
        update_ingestion_state(
            session,
            source_version_id=source_version_id,
            pipeline_state=PipelineArtifactState.PARTIAL.value,
            extraction_run_id=run.id,
        )

    return run


def persist_extracted_text(
    session: Session,
    *,
    extraction_run_id: UUID,
    raw_text: str,
    normalized_text: str | None = None,
    storage_backend: str = STORAGE_BACKEND_DATABASE,
) -> ExtractedText:
    run = session.get(ExtractionRun, extraction_run_id)
    if run is None:
        raise IngestionPersistenceError(f"extraction_run not found: {extraction_run_id}")

    if run.extraction_status not in {
        ExtractionStatus.SUCCESS.value,
        ExtractionStatus.PARTIAL.value,
    }:
        raise IngestionPersistenceError(
            "extracted text may only be persisted for successful or partial extraction runs"
        )

    existing = session.execute(
        select(ExtractedText).where(ExtractedText.extraction_run_id == extraction_run_id)
    ).scalar_one_or_none()
    if existing is not None:
        raise IngestionPersistenceError(
            "extracted text already exists for this extraction run; append a new run instead"
        )

    content_hash = sha256_text(raw_text)
    if run.content_hash is not None and run.content_hash != content_hash:
        raise IngestionPersistenceError("content_hash does not match extraction run record")

    if run.content_hash is None:
        run.content_hash = content_hash
        run.raw_text_length = len(raw_text)

    record = ExtractedText(
        extraction_run_id=extraction_run_id,
        source_version_id=run.source_version_id,
        content_hash=content_hash,
        raw_text=raw_text,
        normalized_text=normalized_text,
        storage_backend=storage_backend,
        created_at=utc_now(),
    )
    session.add(record)
    session.flush()

    pipeline_state = (
        PipelineArtifactState.PARTIAL.value
        if run.extraction_status == ExtractionStatus.PARTIAL.value
        else PipelineArtifactState.EXTRACTED.value
    )
    current = get_current_pipeline_state(session, source_version_id=run.source_version_id)
    if current != pipeline_state:
        update_ingestion_state(
            session,
            source_version_id=run.source_version_id,
            pipeline_state=pipeline_state,
            extraction_run_id=run.id,
        )
    return record


def assert_extracted_text_not_mutated(record: ExtractedText, *, field_name: str) -> None:
    assert_extracted_text_immutable(field_name=field_name)
    _ = record
