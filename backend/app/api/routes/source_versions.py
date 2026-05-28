from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.source_document import SourceDocument
from app.models.source_version import SourceVersion
from app.schemas.source_version import SourceVersionCreate, SourceVersionRead

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
