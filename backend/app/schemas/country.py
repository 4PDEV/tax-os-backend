from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CountryBase(BaseModel):
    code: str
    name: str
    status: str = "active"


class CountryCreate(CountryBase):
    pass


class CountryUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    status: str | None = None


class CountryRead(CountryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
