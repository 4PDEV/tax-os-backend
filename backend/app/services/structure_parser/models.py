from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.structure_parser.enums import StructuralUnitType


class StructuralUnit(BaseModel):
    """A single structural unit within extracted document text.

    Source-faithful and traceable: ``raw_text`` spans ``[start_offset, end_offset)``
    in the original extracted text. Hierarchy is expressed structurally via
    ``hierarchy_level`` and ``parent_unit_id`` with no semantic interpretation.
    """

    model_config = ConfigDict(extra="forbid")

    source_version_id: UUID
    unit_id: str
    unit_type: StructuralUnitType
    unit_label: str
    unit_title: str | None = None
    full_heading: str
    parent_unit_id: str | None = None
    hierarchy_level: int = Field(ge=0)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    raw_text: str
    detected_at: datetime
    parser_version: str

    @model_validator(mode="after")
    def offsets_must_be_ordered(self) -> "StructuralUnit":
        if self.end_offset < self.start_offset:
            raise ValueError("end_offset must be >= start_offset")
        return self
