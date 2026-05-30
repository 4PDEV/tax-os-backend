from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.citation_anchors.enums import CitationAnchorType, GenerationStatus


class CitationAnchorMetadata(BaseModel):
    """Observational metadata for a single citation anchor.

    Records only how the anchor was generated. Never carries legal
    interpretation, authority ranking, semantic classification, risk
    assessment, or topic tagging.
    """

    model_config = ConfigDict(extra="forbid")

    generated_from_object_type: str | None = None
    normalization_notes: str | None = None
    generator_notes: str | None = None
    anchor_generation_warnings: list[str] = Field(default_factory=list)


class CanonicalCitationAnchor(BaseModel):
    """A single deterministic, structure-based citation anchor.

    Source-faithful and object-backed: ``raw_text`` and offsets are preserved
    exactly from the originating :class:`LegalObjectCandidate`. ``canonical_anchor``
    and ``citation_anchor_id`` are deterministic functions of stable structural
    inputs only (never database IDs, UUID randomness, timestamps, or AI).
    """

    model_config = ConfigDict(extra="forbid")

    citation_anchor_id: str
    source_version_id: UUID
    legal_object_id: str
    source_segment_id: str
    anchor_type: CitationAnchorType
    canonical_anchor: str
    display_label: str
    hierarchy_path: list[str] = Field(default_factory=list)
    sequence_number: int = Field(ge=0)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    raw_text: str
    metadata: CitationAnchorMetadata = Field(default_factory=CitationAnchorMetadata)

    @model_validator(mode="after")
    def offsets_must_be_ordered(self) -> "CanonicalCitationAnchor":
        if self.end_offset < self.start_offset:
            raise ValueError("end_offset must be >= start_offset")
        return self


class CitationAnchorGenerationMetadata(BaseModel):
    """Observational metadata describing how anchor generation was performed."""

    model_config = ConfigDict(extra="forbid")

    source_object_count: int = Field(default=0, ge=0)
    generated_count: int = Field(default=0, ge=0)
    duration_ms: float | None = Field(default=None, ge=0)
    partial: bool = False
    anchor_generation_warnings: list[str] = Field(default_factory=list)


class CitationAnchorGenerationResult(BaseModel):
    """Deterministic result of generating citation anchors for legal objects."""

    model_config = ConfigDict(extra="forbid")

    source_version_id: UUID
    generation_status: GenerationStatus
    generator_name: str
    generator_version: str
    generated_at: datetime
    citation_anchor_count: int = Field(ge=0)
    citation_anchors: list[CanonicalCitationAnchor] = Field(default_factory=list)
    metadata: CitationAnchorGenerationMetadata = Field(default_factory=CitationAnchorGenerationMetadata)

    @model_validator(mode="after")
    def count_must_match(self) -> "CitationAnchorGenerationResult":
        if self.citation_anchor_count != len(self.citation_anchors):
            raise ValueError("citation_anchor_count must equal len(citation_anchors)")
        return self
