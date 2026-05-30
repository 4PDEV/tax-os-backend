from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.legal_object_extraction.enums import LegalObjectExtractionStatus, LegalObjectType


class LegalObjectCandidate(BaseModel):
    """A source-backed legal object candidate derived from a structural unit.

    Candidates are not final legal truth — they are structured, traceable inputs
    for later validation, persistence, citation anchoring, and topic mapping.
    No legal interpretation is encoded in this model.
    """

    model_config = ConfigDict(extra="forbid")

    source_version_id: str
    legal_object_id: str
    object_type: LegalObjectType
    object_label: str
    object_title: str | None = None
    canonical_path: str
    parent_legal_object_id: str | None = None
    structural_unit_id: str
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    raw_text: str
    text_hash: str
    extraction_status: LegalObjectExtractionStatus
    extracted_at: datetime
    extractor_version: str
    metadata: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def offsets_must_be_ordered(self) -> "LegalObjectCandidate":
        if self.end_offset < self.start_offset:
            raise ValueError("end_offset must be >= start_offset")
        return self
