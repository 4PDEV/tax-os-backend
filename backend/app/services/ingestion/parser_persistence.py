from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.extraction_run import ExtractionRun
from app.models.parsed_structure import ParsedStructure
from app.models.parser_run import ParserRun
from app.services.ingestion.enums import (
    STRUCTURE_TYPE_STRUCTURAL_UNITS,
    ParserRunStatus,
    PipelineArtifactState,
)
from app.services.ingestion.errors import IngestionPersistenceError
from app.services.ingestion.hashing import sha256_structure
from app.services.ingestion.immutability import assert_parsed_structure_immutable
from app.services.ingestion.ingestion_state import get_current_pipeline_state, update_ingestion_state

PARSER_RUN_STATUSES = frozenset(status.value for status in ParserRunStatus)


def create_parser_run(
    session: Session,
    *,
    extraction_run_id: UUID,
    parser_name: str,
    parser_version: str,
    parser_status: str,
    started_at: datetime,
    completed_at: datetime | None = None,
    error_message: str | None = None,
) -> ParserRun:
    if parser_status not in PARSER_RUN_STATUSES:
        raise IngestionPersistenceError(f"invalid parser_status: {parser_status}")

    extraction_run = session.get(ExtractionRun, extraction_run_id)
    if extraction_run is None:
        raise IngestionPersistenceError(f"extraction_run not found: {extraction_run_id}")

    run = ParserRun(
        extraction_run_id=extraction_run_id,
        parser_name=parser_name,
        parser_version=parser_version,
        parser_status=parser_status,
        started_at=started_at,
        completed_at=completed_at,
        error_message=error_message,
        created_at=utc_now(),
    )
    session.add(run)
    session.flush()

    if parser_status == ParserRunStatus.FAILED.value:
        update_ingestion_state(
            session,
            source_version_id=extraction_run.source_version_id,
            pipeline_state=PipelineArtifactState.FAILED.value,
            parser_run_id=run.id,
        )
    elif parser_status == ParserRunStatus.PARTIAL.value:
        update_ingestion_state(
            session,
            source_version_id=extraction_run.source_version_id,
            pipeline_state=PipelineArtifactState.PARTIAL.value,
            parser_run_id=run.id,
        )

    return run


def persist_parsed_structure(
    session: Session,
    *,
    parser_run_id: UUID,
    structure_units: list[dict[str, Any]],
    structure_type: str = STRUCTURE_TYPE_STRUCTURAL_UNITS,
) -> ParsedStructure:
    run = session.get(ParserRun, parser_run_id)
    if run is None:
        raise IngestionPersistenceError(f"parser_run not found: {parser_run_id}")

    if run.parser_status not in {
        ParserRunStatus.SUCCESS.value,
        ParserRunStatus.PARTIAL.value,
    }:
        raise IngestionPersistenceError(
            "parsed structure may only be persisted for successful or partial parser runs"
        )

    existing = session.execute(
        select(ParsedStructure).where(ParsedStructure.parser_run_id == parser_run_id)
    ).scalar_one_or_none()
    if existing is not None:
        raise IngestionPersistenceError(
            "parsed structure already exists for this parser run; append a new run instead"
        )

    extraction_run = session.get(ExtractionRun, run.extraction_run_id)
    if extraction_run is None:
        raise IngestionPersistenceError(f"extraction_run not found: {run.extraction_run_id}")

    structure_hash = sha256_structure(structure_units)
    structure_json = {
        "structure_type": structure_type,
        "units": structure_units,
    }

    record = ParsedStructure(
        parser_run_id=parser_run_id,
        source_version_id=extraction_run.source_version_id,
        structure_type=structure_type,
        structure_json=structure_json,
        structure_hash=structure_hash,
        created_at=utc_now(),
    )
    session.add(record)
    session.flush()

    pipeline_state = (
        PipelineArtifactState.PARTIAL.value
        if run.parser_status == ParserRunStatus.PARTIAL.value
        else PipelineArtifactState.PARSED.value
    )
    current = get_current_pipeline_state(session, source_version_id=extraction_run.source_version_id)
    if current != pipeline_state:
        update_ingestion_state(
            session,
            source_version_id=extraction_run.source_version_id,
            pipeline_state=pipeline_state,
            parser_run_id=run.id,
        )
    return record


def assert_parsed_structure_not_mutated(record: ParsedStructure, *, field_name: str) -> None:
    assert_parsed_structure_immutable(field_name=field_name)
    _ = record
