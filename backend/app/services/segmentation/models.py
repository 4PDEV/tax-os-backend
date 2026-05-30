from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.segmentation.enums import SegmentationStatus, SegmentType


class SegmentMetadata(BaseModel):
    """Non-interpretive metadata describing a single segment.

    Observational only — character/line counts and the structural marker that
    triggered typing. Never carries inferred or summarized content.
    """

    model_config = ConfigDict(extra="forbid")

    char_count: int = Field(default=0, ge=0)
    line_count: int = Field(default=0, ge=0)
    matched_marker: str | None = None
    warnings: list[str] = Field(default_factory=list)


class Segment(BaseModel):
    """A single structural text segment.

    ``raw_text`` is the exact substring of the source extracted text spanning
    ``[start_offset, end_offset)``. Hierarchy is expressed structurally via
    ``hierarchy_level`` and ``parent_segment_id`` without any semantic meaning.
    """

    model_config = ConfigDict(extra="forbid")

    segment_id: str
    segment_type: SegmentType
    hierarchy_level: int = Field(ge=0)
    parent_segment_id: str | None = None
    sequence_number: int = Field(ge=0)
    heading: str | None = None
    raw_text: str
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    metadata: SegmentMetadata = Field(default_factory=SegmentMetadata)

    @model_validator(mode="after")
    def offsets_must_be_ordered(self) -> "Segment":
        if self.end_offset < self.start_offset:
            raise ValueError("end_offset must be >= start_offset")
        return self


class SegmentationMetadata(BaseModel):
    """Non-interpretive metadata describing how segmentation was performed."""

    model_config = ConfigDict(extra="forbid")

    source_char_count: int = Field(default=0, ge=0)
    block_count: int = Field(default=0, ge=0)
    duration_ms: float | None = Field(default=None, ge=0)
    partial: bool = False
    warnings: list[str] = Field(default_factory=list)


class SegmentationResult(BaseModel):
    """Deterministic result of segmenting extracted text into ordered segments."""

    model_config = ConfigDict(extra="forbid")

    source_version_id: UUID
    segmentation_status: SegmentationStatus
    segmenter_name: str
    segmenter_version: str
    segmented_at: datetime
    segment_count: int = Field(ge=0)
    segments: list[Segment] = Field(default_factory=list)
    metadata: SegmentationMetadata = Field(default_factory=SegmentationMetadata)

    @model_validator(mode="after")
    def segment_count_must_match(self) -> "SegmentationResult":
        if self.segment_count != len(self.segments):
            raise ValueError("segment_count must equal len(segments)")
        return self
