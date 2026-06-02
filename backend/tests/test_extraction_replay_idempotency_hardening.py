import uuid
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.datetime_utils import utc_now
from app.models.extraction_trigger_request import ExtractionTriggerRequest
from app.models.extraction_trigger_result import ExtractionTriggerResult
from app.models.extracted_text import ExtractedText
from app.models.extraction_run import ExtractionRun
from app.models.source_version import SourceVersion
from app.services.extraction_trigger import (
    ExtractionTriggerPersistenceError,
    compute_trigger_hash,
    create_extraction_trigger_request,
    persist_extraction_trigger_result,
    source_version_has_completed_extraction,
)
from app.workers.extraction import run_controlled_local_extraction
from tests.monitoring_test_helpers import seed_source_document

pytestmark = pytest.mark.integration

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "fetch"


def _seed_source_version(db_session) -> SourceVersion:
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
        storage_path="/fixtures/sample.txt",
        mime_type="text/plain",
        file_size=120,
        version_status="active",
        notes="006P1 idempotency regression",
        supersedes_version_id=None,
    )
    db_session.add(version)
    db_session.flush()
    return version


def test_trigger_hash_ignores_request_metadata():
    source_version_id = uuid.uuid4()
    hash_one = compute_trigger_hash(source_version_id=source_version_id, force_reprocess=False)
    hash_two = compute_trigger_hash(source_version_id=source_version_id, force_reprocess=False)
    assert hash_one == hash_two


def test_different_trigger_reason_same_default_hash(db_session):
    source_version = _seed_source_version(db_session)
    hash_a = compute_trigger_hash(source_version_id=source_version.id, force_reprocess=False)
    hash_b = compute_trigger_hash(source_version_id=source_version.id, force_reprocess=False)
    assert hash_a == hash_b


def test_second_default_trigger_rejected_when_reason_or_rerun_allowed_differs(db_session):
    source_version = _seed_source_version(db_session)
    create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="first reason",
        rerun_allowed=False,
        force_reprocess=False,
    )
    with pytest.raises(ExtractionTriggerPersistenceError) as exc:
        create_extraction_trigger_request(
            db_session,
            source_version_id=source_version.id,
            requested_by_actor_type="admin",
            trigger_reason="completely different reason",
            rerun_allowed=True,
            force_reprocess=False,
        )
    assert "duplicate_default_trigger_for_source_version" in str(exc.value)


def test_rerun_allowed_does_not_bypass_default_trigger_duplicate(db_session):
    source_version = _seed_source_version(db_session)
    create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="initial",
        rerun_allowed=False,
        force_reprocess=False,
    )
    with pytest.raises(ExtractionTriggerPersistenceError):
        create_extraction_trigger_request(
            db_session,
            source_version_id=source_version.id,
            requested_by_actor_type="worker",
            trigger_reason="retry with rerun_allowed",
            rerun_allowed=True,
            force_reprocess=False,
        )


def test_mandatory_regression_no_repeat_extraction_after_completed(db_session):
    source_version = _seed_source_version(db_session)
    first_request = create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="first extraction",
        rerun_allowed=False,
        force_reprocess=False,
    )
    first_summary = run_controlled_local_extraction(
        db_session,
        artifact_root=FIXTURE_ROOT,
        controlled_local=True,
    )
    assert first_summary.extraction_runs_created == 1
    assert db_session.query(ExtractedText).count() == 1
    assert source_version_has_completed_extraction(
        db_session, source_version_id=source_version.id
    )

    with pytest.raises(ExtractionTriggerPersistenceError):
        create_extraction_trigger_request(
            db_session,
            source_version_id=source_version.id,
            requested_by_actor_type="admin",
            trigger_reason="second extraction different wording",
            rerun_allowed=True,
            force_reprocess=False,
        )

    second_summary = run_controlled_local_extraction(
        db_session,
        artifact_root=FIXTURE_ROOT,
        controlled_local=True,
    )
    assert second_summary.triggers_processed == 0
    assert db_session.query(ExtractionRun).count() == 1
    assert db_session.query(ExtractedText).count() == 1
    _ = first_request


def test_force_reprocess_allows_new_trigger_and_extraction(db_session):
    source_version = _seed_source_version(db_session)
    create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="first",
        force_reprocess=False,
    )
    _ = run_controlled_local_extraction(
        db_session,
        artifact_root=FIXTURE_ROOT,
        controlled_local=True,
    )

    create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="forced replay",
        rerun_allowed=True,
        force_reprocess=True,
    )
    second = run_controlled_local_extraction(
        db_session,
        artifact_root=FIXTURE_ROOT,
        controlled_local=True,
    )
    assert second.extraction_runs_created == 1
    assert db_session.query(ExtractionRun).count() == 2
    assert db_session.query(ExtractedText).count() == 2


def test_db_rejects_duplicate_default_trigger_at_constraint_level(db_session):
    source_version = _seed_source_version(db_session)
    now = utc_now()
    first = ExtractionTriggerRequest(
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        requested_by_actor_identifier=None,
        trigger_reason="direct insert one",
        requested_at=now,
        rerun_allowed=False,
        force_reprocess=False,
        trigger_hash=compute_trigger_hash(
            source_version_id=source_version.id, force_reprocess=False
        ),
        notes=None,
        created_at=now,
    )
    db_session.add(first)
    db_session.flush()

    second = ExtractionTriggerRequest(
        source_version_id=source_version.id,
        requested_by_actor_type="admin",
        requested_by_actor_identifier=None,
        trigger_reason="direct insert two different reason",
        requested_at=now,
        rerun_allowed=True,
        force_reprocess=False,
        trigger_hash=compute_trigger_hash(
            source_version_id=source_version.id, force_reprocess=False
        ),
        notes=None,
        created_at=now,
    )
    db_session.add(second)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_db_allows_multiple_force_reprocess_triggers_same_source_version(db_session):
    source_version = _seed_source_version(db_session)
    now = utc_now()
    for _ in range(2):
        row = ExtractionTriggerRequest(
            source_version_id=source_version.id,
            requested_by_actor_type="worker",
            requested_by_actor_identifier=None,
            trigger_reason="force replay",
            requested_at=now,
            rerun_allowed=True,
            force_reprocess=True,
            trigger_hash=compute_trigger_hash(
                source_version_id=source_version.id, force_reprocess=True
            ),
            notes=None,
            created_at=now,
        )
        db_session.add(row)
    db_session.flush()
