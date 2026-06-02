from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.source_allowlist_entry import SourceAllowlistEntry
from app.services.monitoring import (
    AttemptStatus,
    CandidateState,
    ErrorCategory,
    SourceAllowlistStatus,
    complete_monitoring_attempt,
    create_monitoring_attempt,
    create_monitoring_candidate,
    create_monitoring_event,
    fail_monitoring_attempt,
)
from app.services.monitoring.errors import MonitoringPersistenceError
from app.workers.monitoring.dry_run_provider import MonitoringProvider
from app.workers.monitoring.result import MonitoringRunSummary


class MonitoringWorkerError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class SourceMonitoringWorker:
    def __init__(self, *, provider: MonitoringProvider, dry_run: bool):
        self._provider = provider
        self._dry_run = dry_run
        if not self._dry_run:
            raise MonitoringWorkerError("non-dry-run monitoring execution is prohibited in TASK-006E")

    def load_eligible_allowlist_entries(self, db: Session) -> list[SourceAllowlistEntry]:
        stmt = (
            select(SourceAllowlistEntry)
            .where(SourceAllowlistEntry.status == SourceAllowlistStatus.ACTIVE.value)
            .order_by(SourceAllowlistEntry.created_at.asc(), SourceAllowlistEntry.id.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def run(self, db: Session, *, agent_name: str, agent_version: str) -> MonitoringRunSummary:
        summary = MonitoringRunSummary()
        entries = self.load_eligible_allowlist_entries(db)
        started = completed = failed = events = candidates = 0

        for entry in entries:
            attempt = create_monitoring_attempt(
                db,
                source_allowlist_entry_id=entry.id,
                agent_name=agent_name,
                agent_version=agent_version,
                started_at=utc_now(),
                attempt_status=AttemptStatus.STARTED.value,
            )
            started += 1

            try:
                provider_result = self._provider.check_source(entry)
                if not provider_result.success:
                    fail_monitoring_attempt(
                        db,
                        monitoring_attempt_id=attempt.id,
                        completed_at=utc_now(),
                        error_category=provider_result.error_category
                        or ErrorCategory.UNKNOWN_FAILURE.value,
                        error_message=provider_result.error_message,
                    )
                    failed += 1
                    continue

                for item in provider_result.items:
                    source_registry_id = (
                        UUID(item.source_registry_id) if item.source_registry_id is not None else None
                    )
                    event = create_monitoring_event(
                        db,
                        monitoring_attempt_id=attempt.id,
                        source_registry_id=source_registry_id,
                        source_url=item.source_url,
                        source_name=item.source_name,
                        source_type=item.source_type,
                        detected_title=item.detected_title,
                        detected_url=item.detected_url,
                        detected_at=utc_now(),
                        detection_method=item.detection_method,
                        checksum_sha256=item.checksum_sha256,
                        previous_checksum_sha256=item.previous_checksum_sha256,
                        change_type=item.change_type,
                        confidence=item.confidence,
                        notes=item.notes,
                    )
                    events += 1

                    candidate = create_monitoring_candidate(
                        db,
                        monitoring_event_id=event.id,
                        candidate_state=CandidateState.DETECTED.value,
                        actor_type="system",
                        actor_identifier=agent_name,
                        transition_reason="dry-run detection",
                    )
                    _ = candidate
                    candidates += 1

                complete_monitoring_attempt(
                    db,
                    monitoring_attempt_id=attempt.id,
                    completed_at=utc_now(),
                    attempt_status=AttemptStatus.COMPLETED.value,
                )
                completed += 1
            except (MonitoringPersistenceError, ValueError) as exc:
                fail_monitoring_attempt(
                    db,
                    monitoring_attempt_id=attempt.id,
                    completed_at=utc_now(),
                    error_category=ErrorCategory.UNKNOWN_FAILURE.value,
                    error_message=str(exc),
                )
                failed += 1

        return MonitoringRunSummary(
            attempts_started=started,
            attempts_completed=completed,
            attempts_failed=failed,
            events_created=events,
            candidates_created=candidates,
        )
