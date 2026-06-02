import pytest
from sqlalchemy import select

from app.core.datetime_utils import utc_now
from app.models.extracted_text import ExtractedText
from app.models.extraction_run import ExtractionRun
from app.models.extraction_trigger_request import ExtractionTriggerRequest
from app.models.extraction_trigger_result import ExtractionTriggerResult
from app.models.legal_object import LegalObject
from app.models.parsed_structure import ParsedStructure
from app.models.source_version import SourceVersion
from app.services.extraction_trigger import (
    ExtractionTriggerPersistenceError,
    compute_trigger_hash,
    create_extraction_trigger_request,
    find_existing_trigger_by_hash,
    get_extraction_trigger_request,
    get_latest_trigger_result_for_request,
    list_trigger_results_for_request,
    persist_extraction_trigger_result,
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
        notes="seed source version for extraction trigger tests",
        supersedes_version_id=None,
    )
    db_session.add(version)
    db_session.flush()
    return version


def test_trigger_request_creation(db_session):
    source_version = _seed_source_version(db_session)
    request = create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="admin",
        requested_by_actor_identifier="qa-reviewer",
        trigger_reason="manual extraction request",
        rerun_allowed=True,
        force_reprocess=False,
        notes="review-gated trigger",
    )
    assert request.id is not None
    assert request.source_version_id == source_version.id
    assert request.requested_by_actor_type == "admin"
    assert request.rerun_allowed is True
    assert request.force_reprocess is False


def test_trigger_hash_deterministic_and_ignores_timestamp(db_session):
    source_version = _seed_source_version(db_session)
    hash_one = compute_trigger_hash(
        source_version_id=source_version.id,
        trigger_reason="same reason",
        requested_by_actor_type="worker",
        rerun_allowed=False,
        force_reprocess=False,
    )
    hash_two = compute_trigger_hash(
        source_version_id=source_version.id,
        trigger_reason="same reason",
        requested_by_actor_type="worker",
        rerun_allowed=False,
        force_reprocess=False,
    )
    assert hash_one == hash_two


def test_duplicate_trigger_rejected_when_force_reprocess_false(db_session):
    source_version = _seed_source_version(db_session)
    create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="duplicate test",
        force_reprocess=False,
    )
    with pytest.raises(ExtractionTriggerPersistenceError):
        create_extraction_trigger_request(
            db_session,
            source_version_id=source_version.id,
            requested_by_actor_type="worker",
            trigger_reason="duplicate test",
            force_reprocess=False,
        )


def test_force_reprocess_allows_new_trigger(db_session):
    source_version = _seed_source_version(db_session)
    first = create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="same request",
        force_reprocess=False,
    )
    second = create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="same request",
        force_reprocess=True,
    )
    assert first.id != second.id


def test_trigger_result_persistence_and_append_only_history(db_session):
    source_version = _seed_source_version(db_session)
    request = create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="system",
        trigger_reason="queue trigger",
    )
    first = persist_extraction_trigger_result(
        db_session,
        extraction_trigger_request_id=request.id,
        trigger_status="failed",
        error_category="extraction_pipeline_unavailable",
        error_message="worker not reachable",
    )
    second = persist_extraction_trigger_result(
        db_session,
        extraction_trigger_request_id=request.id,
        trigger_status="queued",
        queued_at=utc_now(),
        notes="retry queued",
    )

    all_results = list_trigger_results_for_request(
        db_session, extraction_trigger_request_id=request.id
    )
    latest = get_latest_trigger_result_for_request(
        db_session, extraction_trigger_request_id=request.id
    )
    assert [r.id for r in all_results] == [first.id, second.id]
    assert latest is not None
    assert latest.id == second.id


def test_enum_validation(db_session):
    source_version = _seed_source_version(db_session)
    with pytest.raises(ValueError):
        create_extraction_trigger_request(
            db_session,
            source_version_id=source_version.id,
            requested_by_actor_type="invalid",
            trigger_reason="bad actor",
        )


def test_fk_integrity_and_get_request(db_session):
    source_version = _seed_source_version(db_session)
    request = create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="admin",
        trigger_reason="fk integrity check",
    )
    loaded = get_extraction_trigger_request(
        db_session, extraction_trigger_request_id=request.id
    )
    assert loaded is not None
    assert loaded.source_version_id == source_version.id


def test_source_version_eligibility_validation(db_session):
    archived = _seed_source_version(db_session, status="archived")
    with pytest.raises(ExtractionTriggerPersistenceError):
        create_extraction_trigger_request(
            db_session,
            source_version_id=archived.id,
            requested_by_actor_type="admin",
            trigger_reason="should fail eligibility",
        )


def test_find_existing_trigger_by_hash(db_session):
    source_version = _seed_source_version(db_session)
    request = create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="user",
        trigger_reason="existing hash lookup",
    )
    existing = find_existing_trigger_by_hash(db_session, trigger_hash=request.trigger_hash)
    assert existing is not None
    assert existing.id == request.id


def test_no_side_effects_on_extraction_or_legal_memory(db_session):
    source_version = _seed_source_version(db_session)
    extraction_runs_before = db_session.query(ExtractionRun).count()
    extracted_texts_before = db_session.query(ExtractedText).count()
    parsed_before = db_session.query(ParsedStructure).count()
    legal_before = db_session.query(LegalObject).count()

    request = create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="admin",
        trigger_reason="persistence only",
    )
    persist_extraction_trigger_result(
        db_session,
        extraction_trigger_request_id=request.id,
        trigger_status="accepted",
    )

    extraction_runs_after = db_session.query(ExtractionRun).count()
    extracted_texts_after = db_session.query(ExtractedText).count()
    parsed_after = db_session.query(ParsedStructure).count()
    legal_after = db_session.query(LegalObject).count()

    assert extraction_runs_before == extraction_runs_after
    assert extracted_texts_before == extracted_texts_after
    assert parsed_before == parsed_after
    assert legal_before == legal_after


def test_tables_present_after_persist(db_session):
    source_version = _seed_source_version(db_session)
    request = create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="test",
        trigger_reason="table presence check",
    )
    persist_extraction_trigger_result(
        db_session,
        extraction_trigger_request_id=request.id,
        trigger_status="pending",
    )
    assert db_session.execute(select(ExtractionTriggerRequest)).scalar_one_or_none() is not None
    assert db_session.execute(select(ExtractionTriggerResult)).scalar_one_or_none() is not None
