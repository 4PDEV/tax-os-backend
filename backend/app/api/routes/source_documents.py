from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.country import Country
from app.models.source_document import SourceDocument
from app.models.tax_type import TaxType
from app.schemas.source_document import (
    SourceDocumentCreate,
    SourceDocumentRead,
    SourceDocumentUpdate,
)

router = APIRouter()


@router.post("", response_model=SourceDocumentRead)
def create_source_document(payload: SourceDocumentCreate, db: Session = Depends(get_db)):
    country = db.query(Country).filter(Country.id == payload.country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    if payload.tax_type_id:
        tax_type = db.query(TaxType).filter(TaxType.id == payload.tax_type_id).first()
        if not tax_type:
            raise HTTPException(status_code=404, detail="Tax type not found")

    record = SourceDocument(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[SourceDocumentRead])
def list_source_documents(db: Session = Depends(get_db)):
    return db.query(SourceDocument).order_by(SourceDocument.title).all()


@router.get("/{source_document_id}", response_model=SourceDocumentRead)
def get_source_document(source_document_id: UUID, db: Session = Depends(get_db)):
    record = db.query(SourceDocument).filter(SourceDocument.id == source_document_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Source document not found")
    return record


@router.put("/{source_document_id}", response_model=SourceDocumentRead)
def update_source_document(
    source_document_id: UUID,
    payload: SourceDocumentUpdate,
    db: Session = Depends(get_db),
):
    record = db.query(SourceDocument).filter(SourceDocument.id == source_document_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Source document not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{source_document_id}", response_model=SourceDocumentRead)
def soft_delete_source_document(source_document_id: UUID, db: Session = Depends(get_db)):
    record = db.query(SourceDocument).filter(SourceDocument.id == source_document_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Source document not found")

    record.status = "inactive"
    db.commit()
    db.refresh(record)
    return record
