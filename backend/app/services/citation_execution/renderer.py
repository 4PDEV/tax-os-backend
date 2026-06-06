"""Deterministic citation rendering via TASK-004D assembler."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.legal_object import LegalObject
from app.services.citation.assembler import CitationAssembler
from app.services.citation.exceptions import CitationAssemblyError
from app.services.citation.models import CitationResult


class CitationRenderError(Exception):
    def __init__(self, message: str, *, category: str = "citation_pipeline_unavailable"):
        self.message = message
        self.category = category
        super().__init__(message)


def render_citation(
    db: Session,
    *,
    legal_object: LegalObject,
    legal_object_version_id: UUID,
) -> CitationResult:
    """Render citation deterministically — no retrieval, ranking, answers, or inference."""
    try:
        return CitationAssembler().assemble(
            db,
            legal_object,
            legal_object_version_id=legal_object_version_id,
        )
    except CitationAssemblyError as exc:
        raise CitationRenderError(str(exc), category="citation_pipeline_unavailable") from exc
