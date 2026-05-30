from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.legal_objects.enums import ExtractionStatus, LegalObjectType


class LegalObjectMetadata(BaseModel):
    """Observational metadata for a single legal object candidate.

    Records only how the structural mapping was produced. Never carries legal
    interpretation, tax-topic classification, risk assessment, authority
    ranking, or effective-date inference.
    """

    model_config = ConfigDict(extra="forbid")

    mapped_from_segment_type: str | None = None
    confidence_of_structural_mapping: float | None = Field(default=None, ge=0.0, le=1.0)
    extractor_notes: str | None = None
    extraction_warnings: list[str] = Field(default_factory=list)


class LegalObjectCandidate(BaseModel):
    """A single canonical legal object candidate derived from one text segment.

    Source-faithful and segment-backed: ``raw_text`` and offsets are preserved
    exactly from the originating segment. Hierarchy is expressed structurally
    via ``hierarchy_level`` and ``parent_legal_object_id`` with no semantic
    interpretation.
    """

    model_config = ConfigDict(extra="forbid")

    legal_object_id: str
    source_version_id: UUID
    source_segment_id: str
    object_type: LegalObjectType
    object_label: str | None = None
    heading: str | None = None
    raw_text: str
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    sequence_number: int = Field(ge=0)
    parent_legal_object_id: str | None = None
    hierarchy_level: int = Field(ge=0)
    metadata: LegalObjectMetadata = Field(default_factory=LegalObjectMetadata)

    @model_validator(mode="after")
    def offsets_must_be_ordered(self) -> "LegalObjectCandidate":
        if self.end_offset < self.start_offset:
            raise ValueError("end_offset must be >= start_offset")
        return self


class LegalObjectExtractionMetadata(BaseModel):
    """Observational metadata describing how legal object extraction was performed."""

    model_config = ConfigDict(extra="forbid")

    source_segment_count: int = Field(default=0, ge=0)
    mapped_count: int = Field(default=0, ge=0)
    duration_ms: float | None = Field(default=None, ge=0)
    partial: bool = False
    extraction_warnings: list[str] = Field(default_factory=list)


class LegalObjectExtractionResult(BaseModel):
    """Deterministic result of mapping text segments to legal object candidates."""

    model_config = ConfigDict(extra="forbid")

    source_version_id: UUID
    extraction_status: ExtractionStatus
    extractor_name: str
    extractor_version: str
    extracted_at: datetime
    legal_object_count: int = Field(ge=0)
    legal_objects: list[LegalObjectCandidate] = Field(default_factory=list)
    metadata: LegalObjectExtractionMetadata = Field(default_factory=LegalObjectExtractionMetadata)

    @model_validator(mode="after")
    def count_must_match(self) -> "LegalObjectExtractionResult":
        if self.legal_object_count != len(self.legal_objects):
            raise ValueError("legal_object_count must equal len(legal_objects)")
        return self
