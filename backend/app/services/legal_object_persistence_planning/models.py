from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.core.datetime_utils import utc_now
from app.services.legal_object_convergence.models import ConvergedLegalObjectCandidate


class PlannedPersistenceStatus(str, Enum):
    """Proposed lifecycle states for a planned persisted legal object."""

    PLANNED = "planned"
    BLOCKED = "blocked"
    APPROVED_FOR_IMPLEMENTATION = "approved_for_implementation"
    SUPERSEDED = "superseded"
    ROLLED_BACK = "rolled_back"


class PlannedVersionStatus(str, Enum):
    """Proposed version-state labels for persisted legal objects."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class PlannedDuplicateStrategy(str, Enum):
    """Proposed duplicate-handling strategies (planning labels only)."""

    REJECT = "reject"
    VERSION_AS_NEW = "version_as_new"
    LINK_LINEAGE = "link_lineage"
    FLAG_FOR_REVIEW = "flag_for_review"
    DEFER = "defer"


class PlannedLegalObjectPersistenceModel(BaseModel):
    """Proposed persistence shape for a converged legal object candidate.

    Planning model only — no database bindings, SQLAlchemy mappings, or
    migration artifacts. Fields describe governance concepts for future
    implementation tasks.
    """

    model_config = ConfigDict(extra="forbid")

    legal_object_id: str
    source_version_id: str
    canonical_path: str
    parent_legal_object_id: str | None = None
    text_hash: str
    effective_from: date | None = None
    effective_to: date | None = None
    version_status: PlannedVersionStatus = PlannedVersionStatus.DRAFT
    lineage_chain: list[str] = Field(default_factory=list)
    duplicate_strategy: PlannedDuplicateStrategy = PlannedDuplicateStrategy.DEFER
    persistence_status: PlannedPersistenceStatus = PlannedPersistenceStatus.PLANNED
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    structural_unit_id: str
    planned_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)


def build_planned_persistence_model(
    converged: ConvergedLegalObjectCandidate,
) -> PlannedLegalObjectPersistenceModel:
    """Build a planning-only persistence model from a converged candidate."""
    from app.services.legal_object_persistence_planning.contract import (
        assert_canonical_persistence_input,
    )

    assert_canonical_persistence_input(converged)
    candidate = converged.candidate

    if candidate.parent_legal_object_id:
        lineage_chain = [candidate.parent_legal_object_id, candidate.legal_object_id]
    else:
        lineage_chain = [candidate.legal_object_id]

    persistence_status = PlannedPersistenceStatus.PLANNED
    if converged.convergence_status.value == "partial":
        persistence_status = PlannedPersistenceStatus.BLOCKED

    return PlannedLegalObjectPersistenceModel(
        legal_object_id=candidate.legal_object_id,
        source_version_id=candidate.source_version_id,
        canonical_path=candidate.canonical_path,
        parent_legal_object_id=candidate.parent_legal_object_id,
        text_hash=candidate.text_hash,
        effective_from=None,
        effective_to=None,
        version_status=PlannedVersionStatus.DRAFT,
        lineage_chain=lineage_chain,
        duplicate_strategy=PlannedDuplicateStrategy.DEFER,
        persistence_status=persistence_status,
        start_offset=candidate.start_offset,
        end_offset=candidate.end_offset,
        structural_unit_id=candidate.structural_unit_id,
        planned_at=utc_now(),
        metadata={
            "convergence_status": converged.convergence_status.value,
            "source_pipeline": converged.source_pipeline.value,
            "warnings": list(converged.warnings),
        },
    )
