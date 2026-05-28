from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.country import Country
from app.schemas.country import CountryCreate, CountryRead, CountryUpdate

router = APIRouter()


@router.post("", response_model=CountryRead)
def create_country(payload: CountryCreate, db: Session = Depends(get_db)):
    existing = db.query(Country).filter(Country.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=409, detail="Country code already exists")

    record = Country(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[CountryRead])
def list_countries(db: Session = Depends(get_db)):
    return db.query(Country).order_by(Country.name).all()


@router.get("/{country_id}", response_model=CountryRead)
def get_country(country_id: UUID, db: Session = Depends(get_db)):
    record = db.query(Country).filter(Country.id == country_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Country not found")
    return record


@router.put("/{country_id}", response_model=CountryRead)
def update_country(country_id: UUID, payload: CountryUpdate, db: Session = Depends(get_db)):
    record = db.query(Country).filter(Country.id == country_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Country not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{country_id}", response_model=CountryRead)
def soft_delete_country(country_id: UUID, db: Session = Depends(get_db)):
    record = db.query(Country).filter(Country.id == country_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Country not found")

    record.status = "inactive"
    db.commit()
    db.refresh(record)
    return record
