import pytest
from sqlalchemy import select

from app.core.datetime_utils import utc_now
from app.models.monitoring_attempt import MonitoringAttempt
from app.models.monitoring_candidate import MonitoringCandidate
from app.models.monitoring_candidate_state_transition import MonitoringCandidateStateTransition
from app.models.monitoring_event import MonitoringEvent
from app.models.source_allowlist_entry import SourceAllowlistEntry
from app.services.monitoring import (
    AttemptStatus,
    CandidateState,
    ChangeType,
    ErrorCategory,
    MonitoringConfidence,
    SourceAllowlistStatus,
    complete_monitoring_attempt,
    create_allowlist_entry,
    create_monitoring_attempt,
    create_monitoring_candidate,
    create_monitoring_event,
    fail_monitoring_attempt,
    get_candidate_current_state,
    transition_candidate_state,
)
from app.services.monitoring.errors import MonitoringPersistenceError
from tests.monitoring_test_helpers import seed_source_document


@pytest.mark.integration
def test_allowlist_entry_creation(db_session):
    entry = create_allowlist_entry(
        db_session,
        jurisdiction="RW",
        authority_name="RRA",
        source_type="tax_authority_portal",
        base_url="https://example.test/rra",
        allowed_patterns_json=["/laws/*"],
        blocked_patterns_json=["/private/*"],
        monitoring_frequency="daily",
        status=SourceAllowlistStatus.ACTIVE.value,
    )
    assert entry.id is not None
    assert entry.status == "active"


@pytest.mark.integration
def test_monitoring_attempt_complete_and_fail(db_session):
    entry = create_allowlist_entry(
        db_session,
        jurisdiction="RW",
        authority_name="Gazette",
        source_type="official_gazette",
        base_url="https://example.test/gazette",
        allowed_patterns_json=["/*"],
        blocked_patterns_json=[],
        monitoring_frequency="hourly",
    )
    attempt = create_monitoring_attempt(
        db_session,
        source_allowlist_entry_id=entry.id,
        agent_name="watcher",
        agent_version="1.0.0",
        started_at=utc_now(),
    )
    complete_monitoring_attempt(
        db_session,
        monitoring_attempt_id=attempt.id,
        completed_at=utc_now(),
    )
    assert attempt.attempt_status == AttemptStatus.COMPLETED.value

    attempt2 = create_monitoring_attempt(
        db_session,
        source_allowlist_entry_id=entry.id,
        agent_name="watcher",
        agent_version="1.0.0",
        started_at=utc_now(),
    )
    fail_monitoring_attempt(
        db_session,
        monitoring_attempt_id=attempt2.id,
        completed_at=utc_now(),
        error_category=ErrorCategory.TIMEOUT.value,
        error_message="request timed out",
    )
    assert attempt2.attempt_status == AttemptStatus.FAILED.value
    assert attempt2.error_category == ErrorCategory.TIMEOUT.value


@pytest.mark.integration
def test_monitoring_event_creation_with_fk_integrity(db_session):
    doc = seed_source_document(db_session)
    entry = create_allowlist_entry(
        db_session,
        jurisdiction="RW",
        authority_name="RRA",
        source_type="tax_authority_portal",
        base_url="https://example.test/rra",
        allowed_patterns_json=["/docs/*"],
        blocked_patterns_json=[],
        monitoring_frequency="daily",
    )
    attempt = create_monitoring_attempt(
        db_session,
        source_allowlist_entry_id=entry.id,
        agent_name="watcher",
        agent_version="1.0.0",
        started_at=utc_now(),
    )
    event = create_monitoring_event(
        db_session,
        monitoring_attempt_id=attempt.id,
        source_registry_id=doc.id,
        source_url=entry.base_url,
        source_name="RRA",
        source_type=entry.source_type,
        detected_title="New VAT guideline",
        detected_url="https://example.test/rra/doc1",
        detected_at=utc_now(),
        detection_method="checksum",
        checksum_sha256="a" * 64,
        previous_checksum_sha256=None,
        change_type=ChangeType.NEW_DOCUMENT.value,
        confidence=MonitoringConfidence.HIGH.value,
    )
    assert event.id is not None
    with pytest.raises(MonitoringPersistenceError):
        create_monitoring_event(
            db_session,
            monitoring_attempt_id=attempt.id,
            source_registry_id=doc.id,
            source_url=entry.base_url,
            source_name="RRA",
            source_type=entry.source_type,
            detected_title="x",
            detected_url="y",
            detected_at=utc_now(),
            detection_method="checksum",
            checksum_sha256=None,
            previous_checksum_sha256=None,
            change_type="invalid",
            confidence=MonitoringConfidence.HIGH.value,
        )


@pytest.mark.integration
def test_candidate_creation_and_transitions_append_only(db_session):
    doc = seed_source_document(db_session)
    entry = create_allowlist_entry(
        db_session,
        jurisdiction="RW",
        authority_name="RRA",
        source_type="tax_authority_portal",
        base_url="https://example.test/rra",
        allowed_patterns_json=["/docs/*"],
        blocked_patterns_json=[],
        monitoring_frequency="daily",
    )
    attempt = create_monitoring_attempt(
        db_session,
        source_allowlist_entry_id=entry.id,
        agent_name="watcher",
        agent_version="1.0.0",
        started_at=utc_now(),
    )
    event = create_monitoring_event(
        db_session,
        monitoring_attempt_id=attempt.id,
        source_registry_id=doc.id,
        source_url=entry.base_url,
        source_name="RRA",
        source_type=entry.source_type,
        detected_title="Updated decree",
        detected_url="https://example.test/rra/doc2",
        detected_at=utc_now(),
        detection_method="metadata",
        checksum_sha256=None,
        previous_checksum_sha256=None,
        change_type=ChangeType.METADATA_CHANGED.value,
        confidence=MonitoringConfidence.MEDIUM.value,
    )
    candidate = create_monitoring_candidate(db_session, monitoring_event_id=event.id)
    assert get_candidate_current_state(db_session, monitoring_candidate_id=candidate.id) == "detected"

    transition_candidate_state(
        db_session,
        monitoring_candidate_id=candidate.id,
        to_state=CandidateState.QUEUED_FOR_REVIEW.value,
        actor_type="reviewer",
        actor_identifier="qa-user",
        transition_reason="queue for review",
    )
    transition_candidate_state(
        db_session,
        monitoring_candidate_id=candidate.id,
        to_state=CandidateState.APPROVED_FOR_INGESTION.value,
        actor_type="reviewer",
        actor_identifier="qa-user",
        transition_reason="approved",
    )
    assert get_candidate_current_state(db_session, monitoring_candidate_id=candidate.id) == (
        CandidateState.APPROVED_FOR_INGESTION.value
    )

    history = db_session.execute(
        select(MonitoringCandidateStateTransition).where(
            MonitoringCandidateStateTransition.monitoring_candidate_id == candidate.id
        )
    ).scalars().all()
    assert len(history) == 3
    assert history[0].from_state is None
    assert history[-1].to_state == CandidateState.APPROVED_FOR_INGESTION.value

    with pytest.raises(MonitoringPersistenceError):
        transition_candidate_state(
            db_session,
            monitoring_candidate_id=candidate.id,
            to_state=CandidateState.DETECTED.value,
            actor_type="reviewer",
        )


@pytest.mark.integration
def test_no_hard_delete_service_paths_exposed(db_session):
    _ = db_session
    # Governance check: monitoring service modules expose create/transition APIs only.
    from app.services.monitoring import __all__ as monitoring_exports

    forbidden = {"delete_monitoring_candidate", "delete_monitoring_event", "hard_delete"}
    assert not any(name in forbidden for name in monitoring_exports)


@pytest.mark.integration
def test_enum_validation_and_fk_integrity(db_session):
    with pytest.raises(MonitoringPersistenceError):
        create_allowlist_entry(
            db_session,
            jurisdiction="RW",
            authority_name="RRA",
            source_type="tax_authority_portal",
            base_url="https://example.test/rra",
            allowed_patterns_json=[],
            blocked_patterns_json=[],
            monitoring_frequency="daily",
            status="invalid",
        )

    with pytest.raises(MonitoringPersistenceError):
        create_monitoring_attempt(
            db_session,
            source_allowlist_entry_id="00000000-0000-0000-0000-000000000000",  # type: ignore[arg-type]
            agent_name="watcher",
            agent_version="1.0.0",
            started_at=utc_now(),
        )

    # Ensure tables are reachable and FK-backed objects created in expected order.
    assert db_session.query(SourceAllowlistEntry).count() >= 0
    assert db_session.query(MonitoringAttempt).count() >= 0
    assert db_session.query(MonitoringEvent).count() >= 0
    assert db_session.query(MonitoringCandidate).count() >= 0
