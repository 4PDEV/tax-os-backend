from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.source_document import SourceDocument
from app.models.source_version import SourceVersion
from app.schemas.source_version import SourceVersionCreate, SourceVersionRead
from app.services.source_upload import SourceUploadError, upload_source_version_file
from app.storage.deps import get_storage
from app.storage.base import StorageService

router = APIRouter()


@router.post("", response_model=SourceVersionRead)
def create_source_version(payload: SourceVersionCreate, db: Session = Depends(get_db)):
    source_document = (
        db.query(SourceDocument)
        .filter(SourceDocument.id == payload.source_document_id)
        .first()
    )
    if not source_document:
        raise HTTPException(status_code=404, detail="Source document not found")

    if payload.supersedes_version_id:
        superseded = (
            db.query(SourceVersion)
            .filter(SourceVersion.id == payload.supersedes_version_id)
            .first()
        )
        if not superseded:
            raise HTTPException(status_code=404, detail="Superseded source version not found")

    record = SourceVersion(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[SourceVersionRead])
def list_source_versions(db: Session = Depends(get_db)):
    return db.query(SourceVersion).order_by(SourceVersion.created_at.desc()).all()


@router.get("/{source_version_id}", response_model=SourceVersionRead)
def get_source_version(source_version_id: UUID, db: Session = Depends(get_db)):
    record = db.query(SourceVersion).filter(SourceVersion.id == source_version_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Source version not found")
    return record


@router.post("/{source_version_id}/upload", response_model=SourceVersionRead)
def upload_source_version(
    source_version_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage),
):
    if not file.filename:
        raise HTTPException(status_code=422, detail="filename is required")

    content = file.file.read()
    try:
        record = upload_source_version_file(
            db,
            storage,
            source_version_id=source_version_id,
            filename=file.filename,
            content=content,
            content_type=file.content_type,
        )
    except SourceUploadError as exc:
        message = exc.message
        if message == "Source version not found":
            raise HTTPException(status_code=404, detail=message) from exc
        if message == "source file already uploaded for this version":
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=422, detail=message) from exc
    except FileExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail="source file already uploaded for this version",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return record
