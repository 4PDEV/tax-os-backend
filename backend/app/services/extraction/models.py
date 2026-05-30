from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.services.extraction.enums import ExtractionStatus


class ExtractionMetadata(BaseModel):
    """Non-interpretive metadata describing how extraction was performed.

    Fields are intentionally minimal and observational. They describe the
    mechanics of extraction (encoding, sizing, timing, warnings) and never
    carry interpreted, summarized, or inferred content.
    """

    model_config = ConfigDict(extra="forbid")

    encoding: str | None = None
    duration_ms: float | None = Field(default=None, ge=0)
    char_count: int | None = Field(default=None, ge=0)
    line_count: int | None = Field(default=None, ge=0)
    byte_count: int | None = Field(default=None, ge=0)
    partial: bool = False
    warnings: list[str] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """Deterministic result of converting a source file to raw extracted text.

    This contract is faithful and non-interpretive: ``raw_text`` is the text
    exactly as extracted, and ``content_hash`` is the SHA-256 of that text.
    """

    model_config = ConfigDict(extra="forbid")

    source_version_id: UUID
    extraction_status: ExtractionStatus
    extractor_name: str
    extractor_version: str
    extracted_at: datetime
    content_hash: str | None = None
    raw_text: str | None = None
    metadata: ExtractionMetadata = Field(default_factory=ExtractionMetadata)
