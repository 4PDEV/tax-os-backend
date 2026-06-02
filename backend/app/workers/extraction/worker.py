from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.extraction_trigger_request import ExtractionTriggerRequest
from app.models.source_version import SourceVersion
from app.services.extraction.enums import ExtractionStatus
from app.services.extraction_trigger.persistence import (
    get_latest_trigger_result_for_request,
    persist_extraction_trigger_result,
    source_version_has_completed_extraction,
)
from app.services.extraction_trigger.validation import validate_actor_type
from app.services.ingestion.extraction_persistence import (
    create_extraction_run,
    persist_extracted_text,
)
from app.services.ingestion.enums import STORAGE_BACKEND_DATABASE
from app.workers.extraction.controlled_local_provider import (
    CONTROLLED_LOCAL_EXTRACTOR_NAME,
    CONTROLLED_LOCAL_EXTRACTOR_VERSION,
)
from app.workers.extraction.dry_run_provider import ExtractionProvider
from app.workers.extraction.result import ExtractionRunSummary

DRY_RUN_EXTRACTOR_NAME = "dry_run_extraction_provider"
DRY_RUN_EXTRACTOR_VERSION = "0.1.0"

EXECUTION_MODE_DRY_RUN = "dry_run"
EXECUTION_MODE_CONTROLLED_LOCAL = "controlled_local"
ALLOWED_EXECUTION_MODES = frozenset({EXECUTION_MODE_DRY_RUN, EXECUTION_MODE_CONTROLLED_LOCAL})

NON_ELIGIBLE_LATEST_STATUSES = frozenset({"duplicate_rejected", "rejected"})
TERMINAL_SKIP_STATUSES = frozenset({"completed", "failed", "skipped"})


class ExtractionWorkerError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ExtractionWorker:
    def __init__(self, *, provider: ExtractionProvider, mode: str):
        if mode not in ALLOWED_EXECUTION_MODES:
            raise ExtractionWorkerError(f"unsupported extraction execution mode: {mode}")
        self._provider = provider
        self._mode = mode

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
            if request.force_reprocess:
                return True
            return False

        if not request.force_reprocess and source_version_has_completed_extraction(
            db, source_version_id=request.source_version_id
        ):
            return False

        return True

    def _default_extractor(self) -> tuple[str, str]:
        if self._mode == EXECUTION_MODE_CONTROLLED_LOCAL:
            return CONTROLLED_LOCAL_EXTRACTOR_NAME, CONTROLLED_LOCAL_EXTRACTOR_VERSION
        return DRY_RUN_EXTRACTOR_NAME, DRY_RUN_EXTRACTOR_VERSION

    def run(
        self,
        db: Session,
        *,
        worker_name: str = "extraction-worker",
        worker_version: str | None = None,
    ) -> ExtractionRunSummary:
        default_name, default_version = self._default_extractor()
        resolved_version = worker_version or default_version

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
            queue_note = (
                "controlled local queue"
                if self._mode == EXECUTION_MODE_CONTROLLED_LOCAL
                else "dry-run queue"
            )
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
                    notes=queue_note,
                )
                results_created += 1

                started = persist_extraction_trigger_result(
                    db,
                    extraction_trigger_request_id=request.id,
                    trigger_status="started",
                    started_at=now,
                    notes=(
                        "controlled local start"
                        if self._mode == EXECUTION_MODE_CONTROLLED_LOCAL
                        else "dry-run start"
                    ),
                )
                results_created += 1

                provider_result = self._provider.run_extraction(source_version, request)
                extractor_name = provider_result.extractor_name or default_name
                extractor_version = provider_result.extractor_version or resolved_version

                if not provider_result.success:
                    failed_run = create_extraction_run(
                        db,
                        source_version_id=request.source_version_id,
                        extractor_name=extractor_name,
                        extractor_version=extractor_version,
                        extraction_status=ExtractionStatus.FAILED.value,
                        started_at=now,
                        completed_at=utc_now(),
                        error_message=provider_result.error_message,
                    )
                    runs_created += 1

                    persist_extraction_trigger_result(
                        db,
                        extraction_trigger_request_id=request.id,
                        trigger_status="failed",
                        extraction_run_id=failed_run.id,
                        completed_at=utc_now(),
                        error_category=provider_result.error_category or "unknown_failure",
                        error_message=provider_result.error_message,
                        notes=provider_result.notes,
                    )
                    results_created += 1
                    failures += 1
                    processed += 1
                    _ = accepted, queued, started, failed_run
                    continue

                extraction_status = provider_result.extraction_status or ExtractionStatus.SUCCESS.value
                run = create_extraction_run(
                    db,
                    source_version_id=request.source_version_id,
                    extractor_name=extractor_name,
                    extractor_version=extractor_version,
                    extraction_status=extraction_status,
                    started_at=now,
                    completed_at=utc_now(),
                    content_hash=provider_result.content_hash,
                    raw_text_length=provider_result.raw_text_length,
                    error_message=None,
                )
                runs_created += 1

                if (
                    self._mode == EXECUTION_MODE_CONTROLLED_LOCAL
                    and provider_result.raw_text is not None
                ):
                    persist_extracted_text(
                        db,
                        extraction_run_id=run.id,
                        raw_text=provider_result.raw_text,
                        storage_backend=STORAGE_BACKEND_DATABASE,
                    )

                completed = persist_extraction_trigger_result(
                    db,
                    extraction_trigger_request_id=request.id,
                    trigger_status="completed",
                    extraction_run_id=run.id,
                    completed_at=utc_now(),
                    notes=provider_result.notes or "extraction lifecycle completed",
                )
                results_created += 1
                _ = accepted, queued, started, completed
                processed += 1
            except Exception as exc:
                try:
                    failed_run = create_extraction_run(
                        db,
                        source_version_id=request.source_version_id,
                        extractor_name=default_name,
                        extractor_version=resolved_version,
                        extraction_status=ExtractionStatus.FAILED.value,
                        started_at=now,
                        completed_at=utc_now(),
                        error_message=str(exc),
                    )
                    runs_created += 1
                    failed_run_id = failed_run.id
                except Exception:
                    failed_run_id = None

                persist_extraction_trigger_result(
                    db,
                    extraction_trigger_request_id=request.id,
                    trigger_status="failed",
                    extraction_run_id=failed_run_id,
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
