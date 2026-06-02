from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.extracted_text import ExtractedText
from app.models.extraction_run import ExtractionRun
from app.models.parsing_trigger_request import ParsingTriggerRequest
from app.services.ingestion.enums import ParserRunStatus
from app.services.ingestion.parser_persistence import create_parser_run, persist_parsed_structure
from app.services.parsing_trigger.persistence import (
    extracted_text_has_completed_parsing,
    get_latest_trigger_result_for_request,
    persist_parsing_trigger_result,
)
from app.services.parsing_trigger.validation import (
    validate_actor_type,
    validate_extracted_text_eligibility,
)
from app.workers.parsing.dry_run_provider import ParsingProvider
from app.workers.parsing.result import ParsingRunSummary
from app.workers.parsing.structural import (
    CONTROLLED_STRUCTURAL_PARSER_NAME,
    CONTROLLED_STRUCTURAL_PARSER_VERSION,
)

DRY_RUN_PARSER_NAME = "dry_run_parsing_provider"
DRY_RUN_PARSER_VERSION = "0.1.0"

EXECUTION_MODE_DRY_RUN = "dry_run"
EXECUTION_MODE_CONTROLLED_STRUCTURAL = "controlled_structural"
ALLOWED_EXECUTION_MODES = frozenset(
    {EXECUTION_MODE_DRY_RUN, EXECUTION_MODE_CONTROLLED_STRUCTURAL}
)

NON_ELIGIBLE_LATEST_STATUSES = frozenset({"duplicate_rejected", "rejected"})
TERMINAL_SKIP_STATUSES = frozenset({"completed", "failed", "skipped"})


class ParsingWorkerError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ParsingWorker:
    def __init__(self, *, provider: ParsingProvider, mode: str):
        if mode not in ALLOWED_EXECUTION_MODES:
            raise ParsingWorkerError(f"unsupported parsing execution mode: {mode}")
        self._provider = provider
        self._mode = mode

    def load_trigger_requests(self, db: Session) -> list[ParsingTriggerRequest]:
        stmt = select(ParsingTriggerRequest).order_by(
            ParsingTriggerRequest.created_at.asc(),
            ParsingTriggerRequest.id.asc(),
        )
        return list(db.execute(stmt).scalars().all())

    def is_eligible(self, db: Session, request: ParsingTriggerRequest) -> bool:
        if not request.trigger_reason or not request.trigger_reason.strip():
            return False
        try:
            validate_actor_type(request.requested_by_actor_type)
        except ValueError:
            return False

        extracted_text = db.get(ExtractedText, request.extracted_text_id)
        if extracted_text is None:
            return False

        extraction_run = db.get(ExtractionRun, extracted_text.extraction_run_id)
        try:
            validate_extracted_text_eligibility(extracted_text, extraction_run)
        except ValueError:
            return False

        latest = get_latest_trigger_result_for_request(
            db, parsing_trigger_request_id=request.id
        )
        if latest is not None and latest.trigger_status in NON_ELIGIBLE_LATEST_STATUSES:
            return False
        if latest is not None and latest.trigger_status in TERMINAL_SKIP_STATUSES:
            if request.force_reparse:
                return True
            return False

        if not request.force_reparse and extracted_text_has_completed_parsing(
            db, extracted_text_id=request.extracted_text_id
        ):
            return False

        return True

    def _default_parser(self) -> tuple[str, str]:
        if self._mode == EXECUTION_MODE_CONTROLLED_STRUCTURAL:
            return CONTROLLED_STRUCTURAL_PARSER_NAME, CONTROLLED_STRUCTURAL_PARSER_VERSION
        return DRY_RUN_PARSER_NAME, DRY_RUN_PARSER_VERSION

    def _queue_note(self) -> str:
        if self._mode == EXECUTION_MODE_CONTROLLED_STRUCTURAL:
            return "controlled structural queue"
        return "dry-run queue"

    def _start_note(self) -> str:
        if self._mode == EXECUTION_MODE_CONTROLLED_STRUCTURAL:
            return "controlled structural start"
        return "dry-run start"

    def run(
        self,
        db: Session,
        *,
        worker_name: str = "parsing-worker",
        worker_version: str | None = None,
    ) -> ParsingRunSummary:
        default_name, default_version = self._default_parser()
        resolved_version = worker_version or default_version

        triggers_seen = processed = skipped = runs_created = results_created = failures = 0

        for request in self.load_trigger_requests(db):
            triggers_seen += 1
            if not self.is_eligible(db, request):
                skipped += 1
                continue

            extracted_text = db.get(ExtractedText, request.extracted_text_id)
            if extracted_text is None:
                skipped += 1
                continue

            now = utc_now()
            try:
                accepted = persist_parsing_trigger_result(
                    db,
                    parsing_trigger_request_id=request.id,
                    trigger_status="accepted",
                    notes=f"accepted by {worker_name}",
                )
                results_created += 1

                queued = persist_parsing_trigger_result(
                    db,
                    parsing_trigger_request_id=request.id,
                    trigger_status="queued",
                    queued_at=now,
                    notes=self._queue_note(),
                )
                results_created += 1

                started = persist_parsing_trigger_result(
                    db,
                    parsing_trigger_request_id=request.id,
                    trigger_status="started",
                    started_at=now,
                    notes=self._start_note(),
                )
                results_created += 1

                provider_result = self._provider.run_parsing(extracted_text, request)
                parser_name = provider_result.parser_name or default_name
                parser_version = provider_result.parser_version or resolved_version

                if not provider_result.success:
                    failed_run = create_parser_run(
                        db,
                        extraction_run_id=extracted_text.extraction_run_id,
                        parser_name=parser_name,
                        parser_version=parser_version,
                        parser_status=ParserRunStatus.FAILED.value,
                        started_at=now,
                        completed_at=utc_now(),
                        error_message=provider_result.error_message,
                    )
                    runs_created += 1

                    persist_parsing_trigger_result(
                        db,
                        parsing_trigger_request_id=request.id,
                        trigger_status="failed",
                        parser_run_id=failed_run.id,
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

                parser_status = provider_result.parser_status or ParserRunStatus.SUCCESS.value
                run = create_parser_run(
                    db,
                    extraction_run_id=extracted_text.extraction_run_id,
                    parser_name=parser_name,
                    parser_version=parser_version,
                    parser_status=parser_status,
                    started_at=now,
                    completed_at=utc_now(),
                    error_message=None,
                )
                runs_created += 1

                if (
                    self._mode == EXECUTION_MODE_CONTROLLED_STRUCTURAL
                    and provider_result.structure_units is not None
                ):
                    persist_parsed_structure(
                        db,
                        parser_run_id=run.id,
                        structure_units=provider_result.structure_units,
                        structure_json_extra=provider_result.structure_envelope,
                    )

                completed = persist_parsing_trigger_result(
                    db,
                    parsing_trigger_request_id=request.id,
                    trigger_status="completed",
                    parser_run_id=run.id,
                    completed_at=utc_now(),
                    notes=provider_result.notes or "parsing lifecycle completed",
                )
                results_created += 1
                _ = accepted, queued, started, completed
                processed += 1
            except Exception as exc:
                try:
                    failed_run = create_parser_run(
                        db,
                        extraction_run_id=extracted_text.extraction_run_id,
                        parser_name=default_name,
                        parser_version=resolved_version,
                        parser_status=ParserRunStatus.FAILED.value,
                        started_at=now,
                        completed_at=utc_now(),
                        error_message=str(exc),
                    )
                    runs_created += 1
                    failed_run_id = failed_run.id
                except Exception:
                    failed_run_id = None

                persist_parsing_trigger_result(
                    db,
                    parsing_trigger_request_id=request.id,
                    trigger_status="failed",
                    parser_run_id=failed_run_id,
                    completed_at=utc_now(),
                    error_category="unknown_failure",
                    error_message=str(exc),
                    notes=f"worker failure recorded by {worker_name}",
                )
                results_created += 1
                failures += 1
                processed += 1

        return ParsingRunSummary(
            triggers_seen=triggers_seen,
            triggers_processed=processed,
            triggers_skipped=skipped,
            parser_runs_created=runs_created,
            trigger_results_created=results_created,
            failures=failures,
        )
