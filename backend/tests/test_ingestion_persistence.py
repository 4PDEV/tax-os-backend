import pytest
from sqlalchemy import select

from app.core.datetime_utils import utc_now
from app.models.extracted_text import ExtractedText
from app.models.extraction_run import ExtractionRun
from app.models.parsed_structure import ParsedStructure
from app.models.parser_run import ParserRun
from app.services.extraction.enums import ExtractionStatus
from app.services.ingestion import (
    PipelineArtifactState,
    ParserRunStatus,
    create_extraction_run,
    create_parser_run,
    get_current_pipeline_state,
    initialize_pipeline_state,
    persist_extracted_text,
    persist_parsed_structure,
    sha256_structure,
    sha256_text,
    update_ingestion_state,
)
from app.services.ingestion.errors import (
    IngestionImmutabilityError,
    IngestionPersistenceError,
    IngestionPipelineStateError,
)
from app.services.ingestion.immutability import (
    assert_extracted_text_immutable,
    assert_parsed_structure_immutable,
)
from tests.ingestion_test_helpers import seed_source_version


@pytest.mark.integration
def test_extraction_run_append_only_and_failed_preserved(db_session):
    version = seed_source_version(db_session)
    started = utc_now()

    failed_run = create_extraction_run(
        db_session,
        source_version_id=version.id,
        extractor_name="TxtExtractor",
        extractor_version="1.0.0",
        extraction_status=ExtractionStatus.FAILED.value,
        started_at=started,
        completed_at=utc_now(),
        error_message="decode error",
    )
    success_run = create_extraction_run(
        db_session,
        source_version_id=version.id,
        extractor_name="TxtExtractor",
        extractor_version="1.0.0",
        extraction_status=ExtractionStatus.SUCCESS.value,
        started_at=started,
        completed_at=utc_now(),
    )

    runs = db_session.execute(
        select(ExtractionRun).where(ExtractionRun.source_version_id == version.id)
    ).scalars().all()
    assert len(runs) == 2
    assert failed_run.error_message == "decode error"
    assert success_run.id != failed_run.id


@pytest.mark.integration
def test_persist_extracted_text_immutable_and_hash_consistent(db_session):
    version = seed_source_version(db_session)
    initialize_pipeline_state(db_session, source_version_id=version.id)
    started = utc_now()
    raw = "Section 15 — tax is due on supply."

    run = create_extraction_run(
        db_session,
        source_version_id=version.id,
        extractor_name="TxtExtractor",
        extractor_version="1.0.0",
        extraction_status=ExtractionStatus.SUCCESS.value,
        started_at=started,
        completed_at=utc_now(),
        content_hash=sha256_text(raw),
        raw_text_length=len(raw),
    )
    record = persist_extracted_text(db_session, extraction_run_id=run.id, raw_text=raw)

    assert record.content_hash == sha256_text(raw)
    with pytest.raises(IngestionPersistenceError):
        persist_extracted_text(db_session, extraction_run_id=run.id, raw_text=raw)

    with pytest.raises(IngestionImmutabilityError):
        assert_extracted_text_immutable(field_name="raw_text")

    assert get_current_pipeline_state(db_session, source_version_id=version.id) == (
        PipelineArtifactState.EXTRACTED.value
    )


@pytest.mark.integration
def test_parser_persistence_and_structure_hash(db_session):
    version = seed_source_version(db_session)
    initialize_pipeline_state(db_session, source_version_id=version.id)
    started = utc_now()
    raw = "PART I\nSection 15\nTax is due."

    extraction_run = create_extraction_run(
        db_session,
        source_version_id=version.id,
        extractor_name="TxtExtractor",
        extractor_version="1.0.0",
        extraction_status=ExtractionStatus.SUCCESS.value,
        started_at=started,
        completed_at=utc_now(),
    )
    persist_extracted_text(db_session, extraction_run_id=extraction_run.id, raw_text=raw)

    failed_parser = create_parser_run(
        db_session,
        extraction_run_id=extraction_run.id,
        parser_name="StructuralParser",
        parser_version="1.0.0",
        parser_status=ParserRunStatus.FAILED.value,
        started_at=started,
        error_message="parse failed",
    )
    success_parser = create_parser_run(
        db_session,
        extraction_run_id=extraction_run.id,
        parser_name="StructuralParser",
        parser_version="1.0.0",
        parser_status=ParserRunStatus.SUCCESS.value,
        started_at=started,
        completed_at=utc_now(),
    )

    units = [
        {
            "unit_type": "section",
            "unit_label": "15",
            "unit_title": None,
            "full_heading": "Section 15",
            "parent_unit_id": None,
            "hierarchy_level": 1,
            "start_offset": 6,
            "end_offset": 16,
            "raw_text": "Section 15",
        }
    ]
    structure = persist_parsed_structure(
        db_session,
        parser_run_id=success_parser.id,
        structure_units=units,
    )
    assert structure.structure_hash == sha256_structure(units)

    parser_runs = db_session.execute(
        select(ParserRun).where(ParserRun.extraction_run_id == extraction_run.id)
    ).scalars().all()
    assert len(parser_runs) == 2
    assert failed_parser.error_message == "parse failed"

    with pytest.raises(IngestionPersistenceError):
        persist_parsed_structure(db_session, parser_run_id=success_parser.id, structure_units=units)

    with pytest.raises(IngestionImmutabilityError):
        assert_parsed_structure_immutable(field_name="structure_json")

    assert get_current_pipeline_state(db_session, source_version_id=version.id) == (
        PipelineArtifactState.PARSED.value
    )


@pytest.mark.integration
def test_ingestion_state_transitions_are_governed(db_session):
    version = seed_source_version(db_session)
    initialize_pipeline_state(db_session, source_version_id=version.id)

    with pytest.raises(IngestionPipelineStateError):
        update_ingestion_state(
            db_session,
            source_version_id=version.id,
            pipeline_state=PipelineArtifactState.PARSED.value,
        )

    update_ingestion_state(
        db_session,
        source_version_id=version.id,
        pipeline_state=PipelineArtifactState.EXTRACTED.value,
    )
    update_ingestion_state(
        db_session,
        source_version_id=version.id,
        pipeline_state=PipelineArtifactState.PARSED.value,
    )
    update_ingestion_state(
        db_session,
        source_version_id=version.id,
        pipeline_state=PipelineArtifactState.LEGAL_OBJECTS_CREATED.value,
    )

    assert get_current_pipeline_state(db_session, source_version_id=version.id) == (
        PipelineArtifactState.LEGAL_OBJECTS_CREATED.value
    )


@pytest.mark.integration
def test_multiple_extracted_text_snapshots_via_new_runs(db_session):
    version = seed_source_version(db_session)
    initialize_pipeline_state(db_session, source_version_id=version.id)
    started = utc_now()

    for idx, text in enumerate(["version A text", "version B text"]):
        run = create_extraction_run(
            db_session,
            source_version_id=version.id,
            extractor_name="TxtExtractor",
            extractor_version="1.0.0",
            extraction_status=ExtractionStatus.SUCCESS.value,
            started_at=started,
            completed_at=utc_now(),
        )
        persist_extracted_text(db_session, extraction_run_id=run.id, raw_text=text)

    texts = db_session.execute(
        select(ExtractedText).where(ExtractedText.source_version_id == version.id)
    ).scalars().all()
    assert len(texts) == 2
    hashes = {t.content_hash for t in texts}
    assert len(hashes) == 2
