from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.extraction_trigger_request import ExtractionTriggerRequest
from app.models.source_version import SourceVersion
from app.services.extraction.enums import ExtractionStatus
from app.services.extraction_trigger.persistence import (
    get_latest_trigger_result_for_request,
    persist_extraction_trigger_result,
)
from app.services.extraction_trigger.validation import validate_actor_type
from app.services.ingestion.extraction_persistence import create_extraction_run
from app.workers.extraction.dry_run_provider import ExtractionProvider
from app.workers.extraction.result import ExtractionRunSummary

DRY_RUN_EXTRACTOR_NAME = "dry_run_extraction_provider"
DRY_RUN_EXTRACTOR_VERSION = "0.1.0"

NON_ELIGIBLE_LATEST_STATUSES = frozenset({"duplicate_rejected", "rejected"})
TERMINAL_SKIP_STATUSES = frozenset({"completed", "failed", "skipped"})


class ExtractionWorkerError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ExtractionWorker:
    def __init__(self, *, provider: ExtractionProvider, dry_run: bool):
        self._provider = provider
        self._dry_run = dry_run
        if not self._dry_run:
            raise ExtractionWorkerError("non-dry-run extraction execution is prohibited in TASK-006O")

    def load_trigger_requests(self, db: Session) -> list[ExtractionTriggerRequest]:
        stmt = select(ExtractionTriggerRequest).order_by(
            ExtractionTriggerRequest.created_at.asc(),
            ExtractionTriggerRequest.id.asc(),
        )
        return list(db.execute(stmt).scalars().all())

    def is_eligible(self, db: Session, request: ExtractionTriggerRequest) -> bool:
        if not request.trigger_reason or not request.trigger_reason.strip():
            return False
        try:
            validate_actor_type(request.requested_by_actor_type)
        except ValueError:
            return False

        source_version = db.get(SourceVersion, request.source_version_id)
        if source_version is None:
            return False
        if source_version.version_status in {"archived", "rejected"}:
            return False

        latest = get_latest_trigger_result_for_request(
            db, extraction_trigger_request_id=request.id
        )
        if latest is not None and latest.trigger_status in NON_ELIGIBLE_LATEST_STATUSES:
            return False
        if latest is not None and latest.trigger_status in TERMINAL_SKIP_STATUSES:
            return request.force_reprocess
        return True

    def run(
        self,
        db: Session,
        *,
        worker_name: str = "extraction-worker",
        worker_version: str = DRY_RUN_EXTRACTOR_VERSION,
    ) -> ExtractionRunSummary:
        summary = ExtractionRunSummary()
        triggers_seen = processed = skipped = runs_created = results_created = failures = 0

        for request in self.load_trigger_requests(db):
            triggers_seen += 1
            if not self.is_eligible(db, request):
                skipped += 1
                continue

            source_version = db.get(SourceVersion, request.source_version_id)
            if source_version is None:
                skipped += 1
                continue

            now = utc_now()
            try:
                accepted = persist_extraction_trigger_result(
                    db,
                    extraction_trigger_request_id=request.id,
                    trigger_status="accepted",
                    notes=f"accepted by {worker_name}",
                )
                results_created += 1

                queued = persist_extraction_trigger_result(
                    db,
                    extraction_trigger_request_id=request.id,
                    trigger_status="queued",
                    queued_at=now,
                    notes="dry-run queue",
                )
                results_created += 1

                started = persist_extraction_trigger_result(
                    db,
                    extraction_trigger_request_id=request.id,
                    trigger_status="started",
                    started_at=now,
                    notes="dry-run start",
                )
                results_created += 1

                provider_result = self._provider.run_extraction(source_version, request)
                if not provider_result.success:
                    persist_extraction_trigger_result(
                        db,
                        extraction_trigger_request_id=request.id,
                        trigger_status="failed",
                        completed_at=utc_now(),
                        error_category=provider_result.error_category or "unknown_failure",
                        error_message=provider_result.error_message,
                        notes=provider_result.notes,
                    )
                    results_created += 1
                    failures += 1
                    processed += 1
                    continue

                run = create_extraction_run(
                    db,
                    source_version_id=request.source_version_id,
                    extractor_name=DRY_RUN_EXTRACTOR_NAME,
                    extractor_version=worker_version,
                    extraction_status=ExtractionStatus.SUCCESS.value,
                    started_at=now,
                    completed_at=utc_now(),
                    error_message=None,
                )
                runs_created += 1

                completed = persist_extraction_trigger_result(
                    db,
                    extraction_trigger_request_id=request.id,
                    trigger_status="completed",
                    extraction_run_id=run.id,
                    completed_at=utc_now(),
                    notes=provider_result.notes or "dry-run lifecycle completed",
                )
                results_created += 1
                _ = accepted, queued, started, completed
                processed += 1
            except Exception as exc:
                persist_extraction_trigger_result(
                    db,
                    extraction_trigger_request_id=request.id,
                    trigger_status="failed",
                    completed_at=utc_now(),
                    error_category="unknown_failure",
                    error_message=str(exc),
                    notes=f"worker failure recorded by {worker_name}",
                )
                results_created += 1
                failures += 1
                processed += 1

        return ExtractionRunSummary(
            triggers_seen=triggers_seen,
            triggers_processed=processed,
            triggers_skipped=skipped,
            extraction_runs_created=runs_created,
            trigger_results_created=results_created,
            failures=failures,
        )
