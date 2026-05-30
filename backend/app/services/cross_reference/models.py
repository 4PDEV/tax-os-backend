from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.services.cross_reference.enums import ReferenceConfidence, ReferenceType


class CrossReferenceResult(BaseModel):
    """A single detected cross-reference in source text.

    Records what was matched and where — never legal meaning, authority
    hierarchy, or interpretive consequences. ``target_candidate`` is the
    literal surface target string when deterministically extractable (e.g.
    instrument name from an ``of the X Act`` phrase).
    """

    model_config = ConfigDict(extra="forbid")

    source_version_id: UUID
    source_location: str
    reference_text: str
    reference_type: ReferenceType
    target_candidate: str | None = None
    confidence: ReferenceConfidence
    detected_at: datetime
    detector_version: str


class CrossReferenceDetectionBatch(BaseModel):
    """Optional wrapper when callers need batch metadata alongside results."""

    model_config = ConfigDict(extra="forbid")

    source_version_id: UUID
    detector_name: str
    detector_version: str
    detected_at: datetime
    reference_count: int = Field(ge=0)
    references: list[CrossReferenceResult] = Field(default_factory=list)
