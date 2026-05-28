from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.source_processing_job import SourceProcessingJob
from app.models.source_version import SourceVersion
from app.schemas.source_processing_job import (
    SourceProcessingJobCreate,
    SourceProcessingJobRead,
    SourceProcessingJobStatusUpdate,
)
from app.services.processing_queue import (
    JOB_STATUS_FAILED,
    ProcessingQueueError,
    has_active_job,
    transition_job_status,
    validate_enqueue,
)

router = APIRouter()


@router.post("", response_model=SourceProcessingJobRead)
def enqueue_source_processing_job(payload: SourceProcessingJobCreate, db: Session = Depends(get_db)):
    version = db.query(SourceVersion).filter(SourceVersion.id == payload.source_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Source version not found")

    try:
        validate_enqueue(version, payload.job_type)
    except ProcessingQueueError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc

    existing_jobs = (
        db.query(SourceProcessingJob)
        .filter(SourceProcessingJob.source_version_id == payload.source_version_id)
        .all()
    )
    if has_active_job(existing_jobs, payload.job_type):
        raise HTTPException(
            status_code=409,
            detail="active processing job already exists for this source version",
        )

    record = SourceProcessingJob(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[SourceProcessingJobRead])
def list_source_processing_jobs(
    job_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(SourceProcessingJob).order_by(
        SourceProcessingJob.priority.desc(),
        SourceProcessingJob.queued_at.asc(),
    )
    if job_status is not None:
        query = query.filter(SourceProcessingJob.job_status == job_status)
    return query.all()


@router.get("/{job_id}", response_model=SourceProcessingJobRead)
def get_source_processing_job(job_id: UUID, db: Session = Depends(get_db)):
    record = db.query(SourceProcessingJob).filter(SourceProcessingJob.id == job_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Source processing job not found")
    return record


@router.post("/{job_id}/status", response_model=SourceProcessingJobRead)
def update_source_processing_job_status(
    job_id: UUID,
    payload: SourceProcessingJobStatusUpdate,
    db: Session = Depends(get_db),
):
    record = db.query(SourceProcessingJob).filter(SourceProcessingJob.id == job_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Source processing job not found")

    if payload.job_status == JOB_STATUS_FAILED and not payload.last_error:
        raise HTTPException(status_code=422, detail="last_error is required when job fails")

    try:
        transition_job_status(
            record,
            payload.job_status,
            last_error=payload.last_error,
        )
    except ProcessingQueueError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc

    db.commit()
    db.refresh(record)
    return record
