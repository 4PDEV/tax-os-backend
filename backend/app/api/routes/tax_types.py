from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.country import Country
from app.models.tax_type import TaxType
from app.schemas.tax_type import TaxTypeCreate, TaxTypeRead, TaxTypeUpdate

router = APIRouter()


@router.post("", response_model=TaxTypeRead)
def create_tax_type(payload: TaxTypeCreate, db: Session = Depends(get_db)):
    country = db.query(Country).filter(Country.id == payload.country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    record = TaxType(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[TaxTypeRead])
def list_tax_types(db: Session = Depends(get_db)):
    return db.query(TaxType).order_by(TaxType.name).all()


@router.get("/{tax_type_id}", response_model=TaxTypeRead)
def get_tax_type(tax_type_id: UUID, db: Session = Depends(get_db)):
    record = db.query(TaxType).filter(TaxType.id == tax_type_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Tax type not found")
    return record


@router.put("/{tax_type_id}", response_model=TaxTypeRead)
def update_tax_type(tax_type_id: UUID, payload: TaxTypeUpdate, db: Session = Depends(get_db)):
    record = db.query(TaxType).filter(TaxType.id == tax_type_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Tax type not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{tax_type_id}", response_model=TaxTypeRead)
def soft_delete_tax_type(tax_type_id: UUID, db: Session = Depends(get_db)):
    record = db.query(TaxType).filter(TaxType.id == tax_type_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Tax type not found")

    record.status = "inactive"
    db.commit()
    db.refresh(record)
    return record
