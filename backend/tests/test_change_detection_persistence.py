import pytest
from sqlalchemy import select

from app.core.datetime_utils import utc_now
from app.models.change_detection_request import ChangeDetectionRequest
from app.models.change_detection_result import ChangeDetectionResult
from app.models.monitoring_candidate import MonitoringCandidate
from app.models.source_version import SourceVersion
from app.services.change_detection import (
    ChangeDetectionPersistenceError,
    create_change_detection_request,
    get_change_detection_request,
    get_latest_change_detection_result_for_request,
    list_change_detection_results_for_request,
    persist_change_detection_result,
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


def _seed_candidate_and_fetch_result(db_session):
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
    fetch_request = create_fetch_request(
        db_session,
        requested_url="fixture://sample.json",
        requested_by_actor_type="worker",
        requested_by_actor_identifier="dry-worker",
        request_reason="seed fetch result for cd request",
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
        content_length=100,
        checksum_sha256="b" * 64,
        storage_backend="local_fixture",
        storage_path="/fixtures/sample.json",
        error_category=None,
        error_message=None,
        fetcher_name="local-fixture-fetcher",
        fetcher_version="0.1.0",
    )
    return source_doc, candidate, fetch_result


def test_change_detection_request_creation(db_session):
    source_doc, _, fetch_result = _seed_candidate_and_fetch_result(db_session)
    request = create_change_detection_request(
        db_session,
        fetch_result_id=fetch_result.id,
        source_document_id=source_doc.id,
        current_artifact_reference="artifact/current.json",
        requested_by_actor_type="worker",
        requested_by_actor_identifier="dry-worker",
        detection_reason="monitoring comparison",
        previous_artifact_reference="artifact/previous.json",
    )
    assert request.id is not None
    assert request.current_artifact_reference == "artifact/current.json"


def test_change_detection_result_persistence(db_session):
    source_doc, _, fetch_result = _seed_candidate_and_fetch_result(db_session)
    request = create_change_detection_request(
        db_session,
        fetch_result_id=fetch_result.id,
        source_document_id=source_doc.id,
        current_artifact_reference="artifact/current.json",
        requested_by_actor_type="worker",
        detection_reason="persist detection result",
    )
    result = persist_change_detection_result(
        db_session,
        change_detection_request_id=request.id,
        detection_status="completed",
        change_detected=True,
        change_type="checksum_changed",
        previous_checksum_sha256="1" * 64,
        current_checksum_sha256="2" * 64,
        metadata_diff_json={"title_changed": True},
        structural_diff_summary="section count changed",
        confidence="medium",
        review_required=True,
        detector_name="checksum-detector",
        detector_version="0.1.0",
        detected_at=utc_now(),
    )
    assert result.id is not None
    assert result.change_type == "checksum_changed"


def test_failed_blocked_skipped_results_persist(db_session):
    source_doc, _, fetch_result = _seed_candidate_and_fetch_result(db_session)
    request = create_change_detection_request(
        db_session,
        fetch_result_id=fetch_result.id,
        source_document_id=source_doc.id,
        current_artifact_reference="artifact/current.json",
        requested_by_actor_type="worker",
        detection_reason="status preservation",
    )
    for status in ("failed", "blocked", "skipped"):
        persist_change_detection_result(
            db_session,
            change_detection_request_id=request.id,
            detection_status=status,
            change_detected=False,
            change_type="unknown",
            previous_checksum_sha256=None,
            current_checksum_sha256=None,
            metadata_diff_json=None,
            structural_diff_summary=None,
            confidence="low",
            review_required=True,
            detector_name="detector",
            detector_version="0.1.0",
            detected_at=utc_now(),
            error_category="unknown_failure",
            error_message=f"{status} status",
        )
    results = list_change_detection_results_for_request(db_session, change_detection_request_id=request.id)
    assert len(results) == 3
    assert {r.detection_status for r in results} == {"failed", "blocked", "skipped"}


def test_multiple_results_append_and_latest_result_retrieval(db_session):
    source_doc, _, fetch_result = _seed_candidate_and_fetch_result(db_session)
    request = create_change_detection_request(
        db_session,
        fetch_result_id=fetch_result.id,
        source_document_id=source_doc.id,
        current_artifact_reference="artifact/current.json",
        requested_by_actor_type="worker",
        detection_reason="append history",
    )
    first = persist_change_detection_result(
        db_session,
        change_detection_request_id=request.id,
        detection_status="failed",
        change_detected=False,
        change_type="unknown",
        previous_checksum_sha256=None,
        current_checksum_sha256=None,
        metadata_diff_json=None,
        structural_diff_summary=None,
        confidence="low",
        review_required=True,
        detector_name="detector",
        detector_version="0.1.0",
        detected_at=utc_now(),
        error_category="diff_failed",
        error_message="first attempt failed",
    )
    second = persist_change_detection_result(
        db_session,
        change_detection_request_id=request.id,
        detection_status="completed",
        change_detected=False,
        change_type="no_change",
        previous_checksum_sha256="1" * 64,
        current_checksum_sha256="1" * 64,
        metadata_diff_json={},
        structural_diff_summary="none",
        confidence="high",
        review_required=False,
        detector_name="detector",
        detector_version="0.1.1",
        detected_at=utc_now(),
    )
    results = list_change_detection_results_for_request(db_session, change_detection_request_id=request.id)
    assert [r.id for r in results] == [first.id, second.id]
    latest = get_latest_change_detection_result_for_request(
        db_session, change_detection_request_id=request.id
    )
    assert latest is not None
    assert latest.id == second.id


def test_enum_validation(db_session):
    with pytest.raises(ChangeDetectionPersistenceError):
        create_change_detection_request(
            db_session,
            current_artifact_reference="artifact/current.json",
            requested_by_actor_type="invalid",
            detection_reason="bad actor type",
        )


def test_fk_integrity_with_fetch_result_and_monitoring_candidate(db_session):
    source_doc, candidate, fetch_result = _seed_candidate_and_fetch_result(db_session)
    before_candidate_state = db_session.get(MonitoringCandidate, candidate.id).candidate_state
    request = create_change_detection_request(
        db_session,
        monitoring_candidate_id=candidate.id,
        fetch_result_id=fetch_result.id,
        source_document_id=source_doc.id,
        current_artifact_reference="artifact/current.json",
        requested_by_actor_type="worker",
        detection_reason="fk integrity",
    )
    persist_change_detection_result(
        db_session,
        change_detection_request_id=request.id,
        detection_status="completed",
        change_detected=True,
        change_type="metadata_changed",
        previous_checksum_sha256=None,
        current_checksum_sha256=None,
        metadata_diff_json={"title": ["old", "new"]},
        structural_diff_summary=None,
        confidence="medium",
        review_required=True,
        detector_name="metadata-detector",
        detector_version="0.1.0",
        detected_at=utc_now(),
    )
    after_candidate_state = db_session.get(MonitoringCandidate, candidate.id).candidate_state
    assert after_candidate_state == before_candidate_state


def test_review_required_doctrine_enforced(db_session):
    source_doc, _, fetch_result = _seed_candidate_and_fetch_result(db_session)
    request = create_change_detection_request(
        db_session,
        fetch_result_id=fetch_result.id,
        source_document_id=source_doc.id,
        current_artifact_reference="artifact/current.json",
        requested_by_actor_type="worker",
        detection_reason="doctrine enforcement",
    )
    with pytest.raises(ChangeDetectionPersistenceError):
        persist_change_detection_result(
            db_session,
            change_detection_request_id=request.id,
            detection_status="completed",
            change_detected=True,
            change_type="content_changed",
            previous_checksum_sha256=None,
            current_checksum_sha256=None,
            metadata_diff_json=None,
            structural_diff_summary="changed",
            confidence="medium",
            review_required=False,
            detector_name="detector",
            detector_version="0.1.0",
            detected_at=utc_now(),
        )


def test_no_source_version_creation(db_session):
    source_doc, _, fetch_result = _seed_candidate_and_fetch_result(db_session)
    before = db_session.query(SourceVersion).count()
    request = create_change_detection_request(
        db_session,
        fetch_result_id=fetch_result.id,
        source_document_id=source_doc.id,
        current_artifact_reference="artifact/current.json",
        requested_by_actor_type="worker",
        detection_reason="no source version side effect",
    )
    persist_change_detection_result(
        db_session,
        change_detection_request_id=request.id,
        detection_status="completed",
        change_detected=False,
        change_type="duplicate_detected",
        previous_checksum_sha256="1" * 64,
        current_checksum_sha256="1" * 64,
        metadata_diff_json={},
        structural_diff_summary="same artifact",
        confidence="high",
        review_required=False,
        detector_name="detector",
        detector_version="0.1.0",
        detected_at=utc_now(),
    )
    after = db_session.query(SourceVersion).count()
    assert after == before


def test_get_change_detection_request_and_table_presence(db_session):
    source_doc, _, fetch_result = _seed_candidate_and_fetch_result(db_session)
    request = create_change_detection_request(
        db_session,
        fetch_result_id=fetch_result.id,
        source_document_id=source_doc.id,
        current_artifact_reference="artifact/current.json",
        requested_by_actor_type="worker",
        detection_reason="table presence",
    )
    fetched = get_change_detection_request(db_session, change_detection_request_id=request.id)
    assert fetched is not None
    persist_change_detection_result(
        db_session,
        change_detection_request_id=request.id,
        detection_status="completed",
        change_detected=False,
        change_type="no_change",
        previous_checksum_sha256="1" * 64,
        current_checksum_sha256="1" * 64,
        metadata_diff_json={},
        structural_diff_summary="none",
        confidence="high",
        review_required=False,
        detector_name="detector",
        detector_version="0.1.0",
        detected_at=utc_now(),
    )
    assert db_session.execute(select(ChangeDetectionRequest)).scalar_one_or_none() is not None
    assert db_session.execute(select(ChangeDetectionResult)).scalar_one_or_none() is not None
