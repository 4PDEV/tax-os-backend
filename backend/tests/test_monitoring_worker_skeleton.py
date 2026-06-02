import pytest
from sqlalchemy import select

from app.core.datetime_utils import utc_now
from app.models.monitoring_attempt import MonitoringAttempt
from app.models.monitoring_candidate import MonitoringCandidate
from app.models.monitoring_candidate_state_transition import MonitoringCandidateStateTransition
from app.models.monitoring_event import MonitoringEvent
from app.services.monitoring import (
    SourceAllowlistStatus,
    create_allowlist_entry,
)
from app.workers.monitoring import (
    MonitoringProviderResult,
    MonitoringWorkerError,
    SourceMonitoringWorker,
    run_monitoring_dry_run,
)
from app.workers.monitoring.dry_run_provider import MonitoringProvider

pytestmark = pytest.mark.integration


class FailingProvider(MonitoringProvider):
    def check_source(self, allowlist_entry):
        _ = allowlist_entry
        return MonitoringProviderResult(
            success=False,
            items=[],
            error_category="timeout",
            error_message="synthetic timeout",
        )


def _allowlist(db_session, *, status: str, authority_name: str):
    return create_allowlist_entry(
        db_session,
        jurisdiction="RW",
        authority_name=authority_name,
        source_type="official_gazette",
        base_url=f"https://example.test/{authority_name.lower()}",
        allowed_patterns_json=["/*"],
        blocked_patterns_json=[],
        monitoring_frequency="daily",
        status=status,
    )


def test_non_dry_run_rejected():
    with pytest.raises(MonitoringWorkerError):
        SourceMonitoringWorker(provider=FailingProvider(), dry_run=False)


def test_dry_run_worker_processes_active_only(db_session):
    _allowlist(db_session, status=SourceAllowlistStatus.ACTIVE.value, authority_name="ActiveOne")
    _allowlist(db_session, status=SourceAllowlistStatus.INACTIVE.value, authority_name="InactiveOne")
    _allowlist(db_session, status=SourceAllowlistStatus.SUSPENDED.value, authority_name="SuspendedOne")

    summary = run_monitoring_dry_run(db_session, dry_run=True, agent_name="dry-worker", agent_version="1.0.0")

    assert summary.attempts_started == 1
    assert summary.attempts_completed == 1
    assert summary.attempts_failed == 0
    assert summary.events_created == 1
    assert summary.candidates_created == 1

    attempt = db_session.execute(select(MonitoringAttempt)).scalar_one()
    assert attempt.agent_name == "dry-worker"
    assert attempt.completed_at is not None
    assert attempt.attempt_status == "completed"


def test_dry_run_creates_event_candidate_and_detected_state(db_session):
    _allowlist(db_session, status=SourceAllowlistStatus.ACTIVE.value, authority_name="AuthorityA")
    summary = run_monitoring_dry_run(db_session, dry_run=True)
    assert summary.events_created == 1
    assert summary.candidates_created == 1

    event = db_session.execute(select(MonitoringEvent)).scalar_one()
    assert event.detected_title == "Dry Run Monitoring Candidate"
    assert event.change_type == "new_document"
    assert event.confidence == "low"

    candidate = db_session.execute(select(MonitoringCandidate)).scalar_one()
    assert candidate.candidate_state == "detected"
    assert candidate.approved_for_ingestion_at is None

    transitions = db_session.execute(select(MonitoringCandidateStateTransition)).scalars().all()
    assert len(transitions) == 1
    assert transitions[0].from_state is None
    assert transitions[0].to_state == "detected"


def test_worker_records_failed_attempt_on_provider_failure(db_session):
    _allowlist(db_session, status=SourceAllowlistStatus.ACTIVE.value, authority_name="FailureAuthority")
    worker = SourceMonitoringWorker(provider=FailingProvider(), dry_run=True)

    summary = worker.run(db_session, agent_name="failing-worker", agent_version="1.0.0")
    assert summary.attempts_started == 1
    assert summary.attempts_completed == 0
    assert summary.attempts_failed == 1
    assert summary.events_created == 0
    assert summary.candidates_created == 0

    attempt = db_session.execute(select(MonitoringAttempt)).scalar_one()
    assert attempt.attempt_status == "failed"
    assert attempt.error_category == "timeout"
    assert attempt.error_message == "synthetic timeout"


def test_summary_counts_with_multiple_active_entries(db_session):
    _allowlist(db_session, status=SourceAllowlistStatus.ACTIVE.value, authority_name="A1")
    _allowlist(db_session, status=SourceAllowlistStatus.ACTIVE.value, authority_name="A2")
    _allowlist(db_session, status=SourceAllowlistStatus.ACTIVE.value, authority_name="A3")
    summary = run_monitoring_dry_run(db_session, dry_run=True)
    assert summary.attempts_started == 3
    assert summary.attempts_completed == 3
    assert summary.attempts_failed == 0
    assert summary.events_created == 3
    assert summary.candidates_created == 3


def test_no_http_client_libraries_introduced():
    from pathlib import Path

    worker_dir = Path(__file__).resolve().parents[1] / "app" / "workers" / "monitoring"
    forbidden_imports = ("requests", "httpx", "aiohttp", "urllib3")
    for path in worker_dir.glob("*.py"):
        content = path.read_text()
        lowered = content.lower()
        for lib in forbidden_imports:
            assert f"import {lib}" not in lowered
            assert f"from {lib} import" not in lowered
