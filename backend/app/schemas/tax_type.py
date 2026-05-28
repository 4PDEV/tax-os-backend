from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TaxTypeBase(BaseModel):
    country_id: UUID
    code: str
    name: str
    description: str | None = None
    status: str = "active"


class TaxTypeCreate(TaxTypeBase):
    pass


class TaxTypeUpdate(BaseModel):
    country_id: UUID | None = None
    code: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None


class TaxTypeRead(TaxTypeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
