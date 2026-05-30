from pydantic import BaseModel, ConfigDict, Field

from app.services.legal_object_convergence.enums import ConvergenceSource, ConvergenceStatus
from app.services.legal_object_extraction.models import LegalObjectCandidate


class ConvergedLegalObjectCandidate(BaseModel):
    """A legal object candidate normalized to the canonical extraction contract."""

    model_config = ConfigDict(extra="forbid")

    candidate: LegalObjectCandidate
    source_pipeline: ConvergenceSource
    convergence_status: ConvergenceStatus
    warnings: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
