from pathlib import Path

import pytest
from sqlalchemy import select

from app.core.datetime_utils import utc_now
from app.models.change_detection_request import ChangeDetectionRequest
from app.models.change_detection_result import ChangeDetectionResult
from app.models.legal_object import LegalObject
from app.models.monitoring_candidate import MonitoringCandidate
from app.models.source_version import SourceVersion
from app.services.change_detection import (
    ChangeDetectionEngineError,
    ChecksumChangeDetectionEngine,
    ChecksumChangeDetectionRequest,
)
from app.services.fetch.persistence import create_fetch_request, persist_fetch_result
from app.services.monitoring import (
    create_allowlist_entry,
    create_monitoring_attempt,
    create_monitoring_candidate,
    create_monitoring_event,
)
from tests.monitoring_test_helpers import seed_source_document

pytestmark = pytest.mark.integration


def _seed_context(db_session):
    source_doc = seed_source_document(db_session)
    allowlist = create_allowlist_entry(
        db_session,
        jurisdiction="RW",
        authority_name="RRA",
        source_type="tax_authority_portal",
        base_url="https://example.test/rra",
        allowed_patterns_json=["/*"],
        blocked_patterns_json=[],
        monitoring_frequency="daily",
        status="active",
    )
    attempt = create_monitoring_attempt(
        db_session,
        source_allowlist_entry_id=allowlist.id,
        agent_name="dry-worker",
        agent_version="1.0.0",
        started_at=utc_now(),
    )
    event = create_monitoring_event(
        db_session,
        monitoring_attempt_id=attempt.id,
        source_registry_id=source_doc.id,
        source_url=allowlist.base_url,
        source_name="RRA",
        source_type=allowlist.source_type,
        detected_title="Candidate",
        detected_url="https://example.test/rra/item",
        detected_at=utc_now(),
        detection_method="checksum",
        checksum_sha256="a" * 64,
        previous_checksum_sha256=None,
        change_type="new_document",
        confidence="low",
    )
    candidate = create_monitoring_candidate(db_session, monitoring_event_id=event.id)
    return source_doc, allowlist, candidate


def _seed_fetch_result(db_session, *, checksum: str | None, context):
    source_doc, allowlist, candidate = context
    fetch_request = create_fetch_request(
        db_session,
        requested_url="fixture://sample.json",
        requested_by_actor_type="worker",
        requested_by_actor_identifier="dry-worker",
        request_reason="seed result for engine tests",
        dry_run=True,
        local_fixture_mode=True,
        monitoring_candidate_id=candidate.id,
        source_allowlist_entry_id=allowlist.id,
    )
    fetch_result = persist_fetch_result(
        db_session,
        fetch_request_id=fetch_request.id,
        fetched_url="fixture://sample.json",
        final_url="/fixtures/sample.json",
        fetch_status="success",
        fetched_at=utc_now(),
        http_status_code=None,
        content_type="application/json",
        content_length=50,
        checksum_sha256=checksum,
        storage_backend="local_fixture",
        storage_path="/fixtures/sample.json",
        error_category=None,
        error_message=None,
        fetcher_name="local-fixture-fetcher",
        fetcher_version="0.1.0",
    )
    return fetch_result, candidate


def _request(current_id, previous_id=None):
    return ChecksumChangeDetectionRequest(
        current_fetch_result_id=current_id,
        previous_fetch_result_id=previous_id,
        requested_by_actor_type="worker",
        requested_by_actor_identifier="dry-worker",
        detection_reason="checksum skeleton detection",
        notes="engine test",
    )


def test_new_artifact_when_previous_missing(db_session):
    context = _seed_context(db_session)
    current, _ = _seed_fetch_result(db_session, checksum="1" * 64, context=context)
    engine = ChecksumChangeDetectionEngine(session=db_session)
    result = engine.detect(_request(current.id))
    assert result.change_type == "new_artifact"
    assert result.change_detected is True
    assert result.review_required is True
    assert result.confidence == "medium"


def test_no_change_when_checksums_equal(db_session):
    context = _seed_context(db_session)
    previous, _ = _seed_fetch_result(db_session, checksum="2" * 64, context=context)
    current, _ = _seed_fetch_result(db_session, checksum="2" * 64, context=context)
    engine = ChecksumChangeDetectionEngine(session=db_session)
    result = engine.detect(_request(current.id, previous.id))
    assert result.change_type == "no_change"
    assert result.change_detected is False
    assert result.review_required is False
    assert result.confidence == "high"


def test_checksum_changed_when_checksums_differ(db_session):
    context = _seed_context(db_session)
    previous, _ = _seed_fetch_result(db_session, checksum="3" * 64, context=context)
    current, _ = _seed_fetch_result(db_session, checksum="4" * 64, context=context)
    engine = ChecksumChangeDetectionEngine(session=db_session)
    result = engine.detect(_request(current.id, previous.id))
    assert result.change_type == "checksum_changed"
    assert result.change_detected is True
    assert result.review_required is True
    assert result.confidence == "high"


def test_unknown_when_current_checksum_missing(db_session):
    context = _seed_context(db_session)
    previous, _ = _seed_fetch_result(db_session, checksum="5" * 64, context=context)
    current, _ = _seed_fetch_result(db_session, checksum=None, context=context)
    engine = ChecksumChangeDetectionEngine(session=db_session)
    result = engine.detect(_request(current.id, previous.id))
    assert result.change_type == "unknown"
    assert result.change_detected is True
    assert result.review_required is True
    assert result.confidence == "low"


def test_unknown_when_previous_checksum_missing(db_session):
    context = _seed_context(db_session)
    previous, _ = _seed_fetch_result(db_session, checksum=None, context=context)
    current, _ = _seed_fetch_result(db_session, checksum="6" * 64, context=context)
    engine = ChecksumChangeDetectionEngine(session=db_session)
    result = engine.detect(_request(current.id, previous.id))
    assert result.change_type == "unknown"
    assert result.change_detected is True
    assert result.review_required is True
    assert result.confidence == "low"


def test_persisted_request_and_result_created(db_session):
    context = _seed_context(db_session)
    current, _ = _seed_fetch_result(db_session, checksum="7" * 64, context=context)
    engine = ChecksumChangeDetectionEngine(session=db_session)
    output = engine.detect(_request(current.id))
    request = db_session.get(ChangeDetectionRequest, output.change_detection_request_id)
    result = db_session.get(ChangeDetectionResult, output.change_detection_result_id)
    assert request is not None
    assert result is not None
    assert result.detector_name == "checksum_change_detection_engine"
    assert result.detector_version == "0.1.0"
    assert result.metadata_diff_json is None
    assert result.structural_diff_summary is None


def test_review_required_doctrine_preserved(db_session):
    context = _seed_context(db_session)
    previous, _ = _seed_fetch_result(db_session, checksum="8" * 64, context=context)
    current, _ = _seed_fetch_result(db_session, checksum="9" * 64, context=context)
    engine = ChecksumChangeDetectionEngine(session=db_session)
    output = engine.detect(_request(current.id, previous.id))
    result = db_session.get(ChangeDetectionResult, output.change_detection_result_id)
    assert result is not None
    if result.change_type in {"no_change", "duplicate_detected"}:
        assert result.review_required is False
    else:
        assert result.review_required is True


def test_invalid_fetch_result_id_rejected(db_session):
    engine = ChecksumChangeDetectionEngine(session=db_session)
    with pytest.raises(ChangeDetectionEngineError):
        engine.detect(
            ChecksumChangeDetectionRequest(
                current_fetch_result_id="00000000-0000-0000-0000-000000000000",  # type: ignore[arg-type]
                previous_fetch_result_id=None,
                requested_by_actor_type="worker",
                requested_by_actor_identifier=None,
                detection_reason="invalid id",
            )
        )


def test_no_source_versions_created(db_session):
    context = _seed_context(db_session)
    current, _ = _seed_fetch_result(db_session, checksum="a" * 64, context=context)
    before = db_session.query(SourceVersion).count()
    engine = ChecksumChangeDetectionEngine(session=db_session)
    engine.detect(_request(current.id))
    after = db_session.query(SourceVersion).count()
    assert before == after


def test_no_candidate_state_autochanged(db_session):
    context = _seed_context(db_session)
    current, candidate = _seed_fetch_result(db_session, checksum="b" * 64, context=context)
    before_state = db_session.get(MonitoringCandidate, candidate.id).candidate_state
    engine = ChecksumChangeDetectionEngine(session=db_session)
    engine.detect(_request(current.id))
    after_state = db_session.get(MonitoringCandidate, candidate.id).candidate_state
    assert before_state == after_state


def test_no_legal_object_creation(db_session):
    context = _seed_context(db_session)
    current, _ = _seed_fetch_result(db_session, checksum="c" * 64, context=context)
    before = db_session.query(LegalObject).count()
    engine = ChecksumChangeDetectionEngine(session=db_session)
    engine.detect(_request(current.id))
    after = db_session.query(LegalObject).count()
    assert before == after


def test_no_parsing_diff_ai_imports_introduced():
    cd_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "change_detection"
    forbidden_imports = ("openai", "anthropic", "spacy", "nltk", "difflib")
    for path in cd_dir.glob("*.py"):
        lowered = path.read_text().lower()
        for lib in forbidden_imports:
            assert f"import {lib}" not in lowered
            assert f"from {lib} import" not in lowered


def test_confidence_assignment_rules(db_session):
    context = _seed_context(db_session)
    current_only, _ = _seed_fetch_result(db_session, checksum="d" * 64, context=context)
    previous_missing, _ = _seed_fetch_result(db_session, checksum=None, context=context)
    current_with_previous, _ = _seed_fetch_result(db_session, checksum="e" * 64, context=context)
    engine = ChecksumChangeDetectionEngine(session=db_session)

    result_new = engine.detect(_request(current_only.id))
    assert result_new.confidence == "medium"

    result_low = engine.detect(_request(current_with_previous.id, previous_missing.id))
    assert result_low.confidence == "low"

    result_high = engine.detect(_request(current_with_previous.id, current_with_previous.id))
    assert result_high.confidence == "high"


def test_engine_result_records_ids_and_outcome(db_session):
    context = _seed_context(db_session)
    current, _ = _seed_fetch_result(db_session, checksum="f" * 64, context=context)
    engine = ChecksumChangeDetectionEngine(session=db_session)
    result = engine.detect(_request(current.id))
    assert result.change_detection_request_id is not None
    assert result.change_detection_result_id is not None
    persisted = db_session.execute(
        select(ChangeDetectionResult).where(ChangeDetectionResult.id == result.change_detection_result_id)
    ).scalar_one()
    assert persisted.change_type == result.change_type
