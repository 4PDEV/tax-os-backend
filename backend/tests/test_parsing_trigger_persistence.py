import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.datetime_utils import utc_now
from app.models.extracted_text import ExtractedText
from app.models.extraction_run import ExtractionRun
from app.models.legal_object import LegalObject
from app.models.parsed_structure import ParsedStructure
from app.models.parser_run import ParserRun
from app.models.parsing_trigger_request import ParsingTriggerRequest
from app.models.parsing_trigger_result import ParsingTriggerResult
from app.models.source_version import SourceVersion
from app.services.parsing_trigger import (
    ParsingTriggerPersistenceError,
    compute_trigger_hash,
    create_parsing_trigger_request,
    find_existing_default_trigger_for_extracted_text,
    get_latest_trigger_result_for_request,
    get_parsing_trigger_request,
    list_trigger_results_for_request,
    persist_parsing_trigger_result,
)
from tests.monitoring_test_helpers import seed_source_document

pytestmark = pytest.mark.integration


def _seed_source_version(db_session, *, status: str = "active") -> SourceVersion:
    source_doc = seed_source_document(db_session)
    version = SourceVersion(
        source_document_id=source_doc.id,
        version_label="v1",
        publication_date=None,
        effective_from=None,
        effective_to=None,
        enforcement_date=None,
        retrieved_at=utc_now(),
        checksum_sha256="a" * 64,
        storage_path="/fixtures/source-v1.json",
        mime_type="application/json",
        file_size=120,
        version_status=status,
        notes="seed source version for parsing trigger tests",
        supersedes_version_id=None,
    )
    db_session.add(version)
    db_session.flush()
    return version


def _seed_extracted_text(
    db_session,
    *,
    extraction_status: str = "success",
    raw_text: str = "Article 1\nTax applies.",
) -> ExtractedText:
    source_version = _seed_source_version(db_session)
    run = ExtractionRun(
        source_version_id=source_version.id,
        extractor_name="test_extractor",
        extractor_version="1.0.0",
        extraction_status=extraction_status,
        started_at=utc_now(),
        completed_at=utc_now(),
        content_hash="b" * 64,
        raw_text_length=len(raw_text),
    )
    db_session.add(run)
    db_session.flush()
    extracted = ExtractedText(
        extraction_run_id=run.id,
        source_version_id=source_version.id,
        content_hash="c" * 64,
        raw_text=raw_text,
        storage_backend="database",
    )
    db_session.add(extracted)
    db_session.flush()
    return extracted


def test_parsing_trigger_request_creation(db_session):
    extracted = _seed_extracted_text(db_session)
    request = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="admin",
        requested_by_actor_identifier="qa-reviewer",
        trigger_reason="manual parsing request",
        rerun_allowed=True,
        force_reparse=False,
        notes="review-gated trigger",
    )
    assert request.id is not None
    assert request.extracted_text_id == extracted.id
    assert request.rerun_allowed is True
    assert request.force_reparse is False


def test_trigger_hash_deterministic_for_extracted_text_only():
    from uuid import uuid4

    extracted_text_id = uuid4()
    hash_one = compute_trigger_hash(extracted_text_id=extracted_text_id, force_reparse=False)
    hash_two = compute_trigger_hash(extracted_text_id=extracted_text_id, force_reparse=False)
    assert hash_one == hash_two


def test_trigger_hash_ignores_request_metadata(db_session):
    extracted = _seed_extracted_text(db_session)
    request = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="worker",
        trigger_reason="reason A",
        rerun_allowed=False,
        force_reparse=False,
    )
    expected = compute_trigger_hash(extracted_text_id=extracted.id, force_reparse=False)
    assert request.trigger_hash == expected


def test_duplicate_default_trigger_rejected_when_force_reparse_false(db_session):
    extracted = _seed_extracted_text(db_session)
    create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="worker",
        trigger_reason="duplicate test",
        force_reparse=False,
    )
    with pytest.raises(ParsingTriggerPersistenceError):
        create_parsing_trigger_request(
            db_session,
            extracted_text_id=extracted.id,
            requested_by_actor_type="admin",
            trigger_reason="different reason still duplicate",
            rerun_allowed=True,
            force_reparse=False,
        )


def test_rerun_allowed_does_not_bypass_duplicate_protection(db_session):
    extracted = _seed_extracted_text(db_session)
    create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="worker",
        trigger_reason="first",
        rerun_allowed=False,
        force_reparse=False,
    )
    with pytest.raises(ParsingTriggerPersistenceError):
        create_parsing_trigger_request(
            db_session,
            extracted_text_id=extracted.id,
            requested_by_actor_type="admin",
            trigger_reason="second",
            rerun_allowed=True,
            force_reparse=False,
        )


def test_force_reparse_allows_new_trigger(db_session):
    extracted = _seed_extracted_text(db_session)
    first = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="worker",
        trigger_reason="same request",
        force_reparse=False,
    )
    second = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="worker",
        trigger_reason="same request",
        force_reparse=True,
    )
    assert first.id != second.id
    assert first.trigger_hash != second.trigger_hash


def test_parsing_trigger_result_persistence_and_append_only_history(db_session):
    extracted = _seed_extracted_text(db_session)
    request = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="system",
        trigger_reason="queue trigger",
    )
    first = persist_parsing_trigger_result(
        db_session,
        parsing_trigger_request_id=request.id,
        trigger_status="failed",
        error_category="parsing_pipeline_unavailable",
        error_message="worker not reachable",
    )
    second = persist_parsing_trigger_result(
        db_session,
        parsing_trigger_request_id=request.id,
        trigger_status="queued",
        queued_at=utc_now(),
        notes="retry queued",
    )

    all_results = list_trigger_results_for_request(
        db_session, parsing_trigger_request_id=request.id
    )
    latest = get_latest_trigger_result_for_request(
        db_session, parsing_trigger_request_id=request.id
    )
    assert [r.id for r in all_results] == [first.id, second.id]
    assert latest is not None
    assert latest.id == second.id


def test_failed_rejected_skipped_results_preserved(db_session):
    extracted = _seed_extracted_text(db_session)
    request = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="test",
        trigger_reason="status coverage",
    )
    for status, category in [
        ("rejected", "extracted_text_not_eligible"),
        ("skipped", None),
        ("duplicate_rejected", None),
    ]:
        persist_parsing_trigger_result(
            db_session,
            parsing_trigger_request_id=request.id,
            trigger_status=status,
            error_category=category,
        )
    assert len(list_trigger_results_for_request(db_session, parsing_trigger_request_id=request.id)) == 3


def test_enum_validation(db_session):
    extracted = _seed_extracted_text(db_session)
    with pytest.raises(ValueError):
        create_parsing_trigger_request(
            db_session,
            extracted_text_id=extracted.id,
            requested_by_actor_type="invalid",
            trigger_reason="bad actor",
        )


def test_fk_integrity_and_get_request(db_session):
    extracted = _seed_extracted_text(db_session)
    request = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="admin",
        trigger_reason="fk integrity check",
    )
    loaded = get_parsing_trigger_request(db_session, parsing_trigger_request_id=request.id)
    assert loaded is not None
    assert loaded.extracted_text_id == extracted.id


def test_extracted_text_eligibility_extraction_not_completed(db_session):
    extracted = _seed_extracted_text(db_session, extraction_status="failed")
    with pytest.raises(ParsingTriggerPersistenceError) as exc:
        create_parsing_trigger_request(
            db_session,
            extracted_text_id=extracted.id,
            requested_by_actor_type="admin",
            trigger_reason="should fail",
        )
    assert "extraction_not_completed" in str(exc.value)


def test_extracted_text_missing(db_session):
    from uuid import uuid4

    with pytest.raises(ParsingTriggerPersistenceError) as exc:
        create_parsing_trigger_request(
            db_session,
            extracted_text_id=uuid4(),
            requested_by_actor_type="admin",
            trigger_reason="missing text",
        )
    assert "extracted_text_missing" in str(exc.value)


def test_find_existing_default_trigger_for_extracted_text(db_session):
    extracted = _seed_extracted_text(db_session)
    request = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="user",
        trigger_reason="existing lookup",
    )
    existing = find_existing_default_trigger_for_extracted_text(
        db_session, extracted_text_id=extracted.id
    )
    assert existing is not None
    assert existing.id == request.id


def test_parser_run_id_reference_without_auto_creation(db_session):
    extracted = _seed_extracted_text(db_session)
    run = db_session.get(ExtractionRun, extracted.extraction_run_id)
    parser_runs_before = db_session.query(ParserRun).count()
    parser_run = ParserRun(
        extraction_run_id=run.id,
        parser_name="test_parser",
        parser_version="1.0.0",
        parser_status="success",
        started_at=utc_now(),
        completed_at=utc_now(),
    )
    db_session.add(parser_run)
    db_session.flush()

    request = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="test",
        trigger_reason="parser run linkage",
    )
    result = persist_parsing_trigger_result(
        db_session,
        parsing_trigger_request_id=request.id,
        trigger_status="completed",
        parser_run_id=parser_run.id,
        completed_at=utc_now(),
    )
    assert result.parser_run_id == parser_run.id
    assert db_session.query(ParserRun).count() == parser_runs_before + 1


def test_no_side_effects_on_parsing_or_legal_memory(db_session):
    extracted = _seed_extracted_text(db_session)
    parser_runs_before = db_session.query(ParserRun).count()
    parsed_before = db_session.query(ParsedStructure).count()
    legal_before = db_session.query(LegalObject).count()

    request = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="admin",
        trigger_reason="persistence only",
    )
    persist_parsing_trigger_result(
        db_session,
        parsing_trigger_request_id=request.id,
        trigger_status="accepted",
    )

    assert db_session.query(ParserRun).count() == parser_runs_before
    assert db_session.query(ParsedStructure).count() == parsed_before
    assert db_session.query(LegalObject).count() == legal_before


def test_db_rejects_duplicate_default_trigger_at_constraint_level(db_session):
    extracted = _seed_extracted_text(db_session)
    now = utc_now()
    first = ParsingTriggerRequest(
        extracted_text_id=extracted.id,
        requested_by_actor_type="worker",
        requested_by_actor_identifier=None,
        trigger_reason="direct insert one",
        requested_at=now,
        rerun_allowed=False,
        force_reparse=False,
        trigger_hash=compute_trigger_hash(extracted_text_id=extracted.id, force_reparse=False),
        notes=None,
        created_at=now,
    )
    db_session.add(first)
    db_session.flush()

    second = ParsingTriggerRequest(
        extracted_text_id=extracted.id,
        requested_by_actor_type="admin",
        requested_by_actor_identifier=None,
        trigger_reason="direct insert two",
        requested_at=now,
        rerun_allowed=True,
        force_reparse=False,
        trigger_hash=compute_trigger_hash(extracted_text_id=extracted.id, force_reparse=False),
        notes=None,
        created_at=now,
    )
    db_session.add(second)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_db_allows_multiple_force_reparse_triggers_same_extracted_text(db_session):
    extracted = _seed_extracted_text(db_session)
    now = utc_now()
    for _ in range(2):
        row = ParsingTriggerRequest(
            extracted_text_id=extracted.id,
            requested_by_actor_type="worker",
            requested_by_actor_identifier=None,
            trigger_reason="force replay",
            requested_at=now,
            rerun_allowed=True,
            force_reparse=True,
            trigger_hash=compute_trigger_hash(extracted_text_id=extracted.id, force_reparse=True),
            notes=None,
            created_at=now,
        )
        db_session.add(row)
    db_session.flush()


def test_tables_present_after_persist(db_session):
    extracted = _seed_extracted_text(db_session)
    request = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="test",
        trigger_reason="table presence check",
    )
    persist_parsing_trigger_result(
        db_session,
        parsing_trigger_request_id=request.id,
        trigger_status="pending",
    )
    assert db_session.execute(select(ParsingTriggerRequest)).scalar_one_or_none() is not None
    assert db_session.execute(select(ParsingTriggerResult)).scalar_one_or_none() is not None
