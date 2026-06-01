from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.ingestion_state_transition import IngestionStateTransition
from app.services.ingestion.enums import PipelineArtifactState
from app.services.ingestion.errors import IngestionPipelineStateError

PIPELINE_STATES = frozenset(state.value for state in PipelineArtifactState)

ALLOWED_PIPELINE_TRANSITIONS: dict[str, frozenset[str]] = {
    PipelineArtifactState.SOURCE_REGISTERED.value: frozenset(
        {
            PipelineArtifactState.EXTRACTED.value,
            PipelineArtifactState.FAILED.value,
            PipelineArtifactState.PARTIAL.value,
        }
    ),
    PipelineArtifactState.EXTRACTED.value: frozenset(
        {
            PipelineArtifactState.PARSED.value,
            PipelineArtifactState.FAILED.value,
            PipelineArtifactState.PARTIAL.value,
        }
    ),
    PipelineArtifactState.PARSED.value: frozenset(
        {
            PipelineArtifactState.LEGAL_OBJECTS_CREATED.value,
            PipelineArtifactState.FAILED.value,
            PipelineArtifactState.PARTIAL.value,
        }
    ),
    PipelineArtifactState.PARTIAL.value: frozenset(
        {
            PipelineArtifactState.EXTRACTED.value,
            PipelineArtifactState.PARSED.value,
            PipelineArtifactState.LEGAL_OBJECTS_CREATED.value,
            PipelineArtifactState.FAILED.value,
        }
    ),
    PipelineArtifactState.FAILED.value: frozenset(
        {
            PipelineArtifactState.SOURCE_REGISTERED.value,
            PipelineArtifactState.EXTRACTED.value,
            PipelineArtifactState.PARSED.value,
            PipelineArtifactState.PARTIAL.value,
        }
    ),
    PipelineArtifactState.LEGAL_OBJECTS_CREATED.value: frozenset(),
}


def validate_pipeline_state(state: str) -> None:
    if state not in PIPELINE_STATES:
        raise IngestionPipelineStateError(f"invalid pipeline artifact state: {state}")


def get_current_pipeline_state(session: Session, *, source_version_id: UUID) -> str | None:
    stmt = (
        select(IngestionStateTransition)
        .where(IngestionStateTransition.source_version_id == source_version_id)
        .order_by(IngestionStateTransition.created_at.desc())
        .limit(1)
    )
    row = session.execute(stmt).scalar_one_or_none()
    return row.pipeline_state if row else None


def initialize_pipeline_state(
    session: Session,
    *,
    source_version_id: UUID,
) -> IngestionStateTransition:
    current = get_current_pipeline_state(session, source_version_id=source_version_id)
    if current is not None:
        raise IngestionPipelineStateError("pipeline state already initialized")

    transition = IngestionStateTransition(
        source_version_id=source_version_id,
        pipeline_state=PipelineArtifactState.SOURCE_REGISTERED.value,
        previous_pipeline_state=None,
        created_at=utc_now(),
    )
    session.add(transition)
    session.flush()
    return transition


def update_ingestion_state(
    session: Session,
    *,
    source_version_id: UUID,
    pipeline_state: str,
    extraction_run_id: UUID | None = None,
    parser_run_id: UUID | None = None,
) -> IngestionStateTransition:
    validate_pipeline_state(pipeline_state)

    current = get_current_pipeline_state(session, source_version_id=source_version_id)
    if current is None:
        if pipeline_state == PipelineArtifactState.SOURCE_REGISTERED.value:
            return initialize_pipeline_state(session, source_version_id=source_version_id)
        initialize_pipeline_state(session, source_version_id=source_version_id)
        current = PipelineArtifactState.SOURCE_REGISTERED.value

    if current == pipeline_state:
        raise IngestionPipelineStateError(f"pipeline state is already {current}")

    allowed = ALLOWED_PIPELINE_TRANSITIONS.get(current, frozenset())
    if pipeline_state not in allowed:
        raise IngestionPipelineStateError(
            f"transition from {current} to {pipeline_state} is not allowed"
        )

    transition = IngestionStateTransition(
        source_version_id=source_version_id,
        pipeline_state=pipeline_state,
        previous_pipeline_state=current,
        extraction_run_id=extraction_run_id,
        parser_run_id=parser_run_id,
        created_at=utc_now(),
    )
    session.add(transition)
    session.flush()
    return transition
