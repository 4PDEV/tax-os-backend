"""Controlled citation execution orchestration."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.citation import Citation
from app.models.citation_assembly_governance_request import CitationAssemblyGovernanceRequest
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.services.citation_execution.persistence import create_citation
from app.services.citation_execution.renderer import CitationRenderError, render_citation


@dataclass(frozen=True)
class ControlledCitationExecutionOutcome:
    citation: Citation
    created: bool
    assembled_at: datetime


def execute_controlled_citation(
    db: Session,
    *,
    request: CitationAssemblyGovernanceRequest,
    legal_object_version: LegalObjectVersion,
) -> ControlledCitationExecutionOutcome:
    legal_object = db.get(LegalObject, request.legal_object_id)
    if legal_object is None:
        raise CitationRenderError("legal_object_missing", category="legal_object_missing")

    rendered = render_citation(
        db,
        legal_object=legal_object,
        legal_object_version_id=legal_object_version.legal_object_version_id,
    )

    citation, created = create_citation(
        db,
        citation_id=rendered.citation_id,
        citation_hash=rendered.citation_hash,
        legal_object_id=rendered.legal_object_id,
        legal_object_version_id=rendered.legal_object_version_id,
        source_version_id=rendered.source_version_id,
        location_reference=rendered.location_reference,
        rendered_citation_text=rendered.citation_text,
        assembled_at=rendered.assembled_at,
    )
    return ControlledCitationExecutionOutcome(
        citation=citation,
        created=created,
        assembled_at=citation.assembled_at,
    )
