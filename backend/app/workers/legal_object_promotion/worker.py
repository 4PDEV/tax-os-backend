from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.extraction_run import ExtractionRun
from app.models.legal_object_promotion_request import LegalObjectPromotionRequest
from app.models.parsed_structure import ParsedStructure
from app.models.source_version import SourceVersion
from app.services.legal_object_promotion.persistence import (
    get_latest_result_for_request,
    persist_promotion_result,
)
from app.services.legal_object_promotion.validation import (
    validate_actor_type,
    validate_parsed_structure_eligibility,
)
from app.models.parser_run import ParserRun
from app.workers.legal_object_promotion.dry_run_provider import (
    DRY_RUN_PROMOTION_PROVIDER_NAME,
    DRY_RUN_PROMOTION_PROVIDER_VERSION,
    LegalObjectPromotionProvider,
)
from app.workers.legal_object_promotion.result import LegalObjectPromotionRunSummary

EXECUTION_MODE_DRY_RUN = "dry_run"
ALLOWED_EXECUTION_MODES = frozenset({EXECUTION_MODE_DRY_RUN})

NON_ELIGIBLE_LATEST_STATUSES = frozenset({"duplicate_rejected", "rejected"})
TERMINAL_SKIP_STATUSES = frozenset({"promoted", "failed", "skipped"})

# Dry-run successful lifecycle ends in ``skipped`` (not ``promoted``) because no legal object exists.
DRY_RUN_TERMINAL_STATUS = "skipped"


class LegalObjectPromotionWorkerError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def parsed_structure_has_promoted_result(db: Session, *, parsed_structure_id: UUID) -> bool:
    """True when any promotion result for this structure reached promoted status."""
    from app.models.legal_object_promotion_result import LegalObjectPromotionResult

    row = db.execute(
        select(LegalObjectPromotionResult.id)
        .where(
            LegalObjectPromotionResult.parsed_structure_id == parsed_structure_id,
            LegalObjectPromotionResult.promotion_status == "promoted",
        )
        .limit(1)
    ).scalar_one_or_none()
    return row is not None


class LegalObjectPromotionWorker:
    def __init__(self, *, provider: LegalObjectPromotionProvider, mode: str):
        if mode not in ALLOWED_EXECUTION_MODES:
            raise LegalObjectPromotionWorkerError(
                f"unsupported legal object promotion execution mode: {mode}"
            )
        self._provider = provider
        self._mode = mode

    def load_promotion_requests(self, db: Session) -> list[LegalObjectPromotionRequest]:
        stmt = select(LegalObjectPromotionRequest).order_by(
            LegalObjectPromotionRequest.created_at.asc(),
            LegalObjectPromotionRequest.id.asc(),
        )
        return list(db.execute(stmt).scalars().all())

    def is_eligible(self, db: Session, request: LegalObjectPromotionRequest) -> bool:
        if not request.promotion_reason or not request.promotion_reason.strip():
            return False
        try:
            validate_actor_type(request.requested_by_actor_type)
        except ValueError:
            return False

        parsed_structure = db.get(ParsedStructure, request.parsed_structure_id)
        if parsed_structure is None:
            return False

        source_version = db.get(SourceVersion, request.source_version_id)
        if source_version is None:
            return False

        parser_run = db.get(ParserRun, parsed_structure.parser_run_id)
        extraction_run = (
            db.get(ExtractionRun, parser_run.extraction_run_id) if parser_run is not None else None
        )
        try:
            validate_parsed_structure_eligibility(
                parsed_structure,
                parser_run,
                extraction_run,
                source_version,
                source_version_id=request.source_version_id,
            )
        except ValueError:
            return False

        latest = get_latest_result_for_request(
            db, legal_object_promotion_request_id=request.id
        )
        if latest is not None and latest.promotion_status in NON_ELIGIBLE_LATEST_STATUSES:
            return False
        if latest is not None and latest.promotion_status in TERMINAL_SKIP_STATUSES:
            if request.force_repromotion:
                return True
            return False

        if not request.force_repromotion and parsed_structure_has_promoted_result(
            db, parsed_structure_id=request.parsed_structure_id
        ):
            return False

        return True

    def run(
        self,
        db: Session,
        *,
        worker_name: str = "legal-object-promotion-worker",
        worker_version: str | None = None,
    ) -> LegalObjectPromotionRunSummary:
        resolved_version = worker_version or DRY_RUN_PROMOTION_PROVIDER_VERSION

        requests_seen = processed = skipped = results_created = failures = 0

        for request in self.load_promotion_requests(db):
            requests_seen += 1
            if not self.is_eligible(db, request):
                skipped += 1
                continue

            parsed_structure = db.get(ParsedStructure, request.parsed_structure_id)
            if parsed_structure is None:
                skipped += 1
                continue

            try:
                persist_promotion_result(
                    db,
                    legal_object_promotion_request_id=request.id,
                    promotion_status="accepted",
                    notes=f"accepted by {worker_name}",
                )
                results_created += 1

                provider_result = self._provider.run_promotion(parsed_structure, request)
                provider_name = provider_result.provider_name or DRY_RUN_PROMOTION_PROVIDER_NAME
                provider_version = provider_result.provider_version or resolved_version

                if not provider_result.success:
                    persist_promotion_result(
                        db,
                        legal_object_promotion_request_id=request.id,
                        promotion_status="failed",
                        error_category=provider_result.error_category or "unknown_failure",
                        error_message=provider_result.error_message,
                        notes=provider_result.notes
                        or f"provider failure ({provider_name}@{provider_version})",
                    )
                    results_created += 1
                    failures += 1
                    processed += 1
                    continue

                persist_promotion_result(
                    db,
                    legal_object_promotion_request_id=request.id,
                    promotion_status=DRY_RUN_TERMINAL_STATUS,
                    legal_object_id=None,
                    promoted_at=None,
                    notes=provider_result.notes
                    or (
                        f"dry-run promotion lifecycle completed by {worker_name}; "
                        "legal_object_id intentionally null"
                    ),
                )
                results_created += 1
                processed += 1
            except Exception as exc:
                persist_promotion_result(
                    db,
                    legal_object_promotion_request_id=request.id,
                    promotion_status="failed",
                    error_category="unknown_failure",
                    error_message=str(exc),
                    notes=f"worker failure recorded by {worker_name}",
                )
                results_created += 1
                failures += 1
                processed += 1

        return LegalObjectPromotionRunSummary(
            requests_seen=requests_seen,
            requests_processed=processed,
            requests_skipped=skipped,
            results_created=results_created,
            failures=failures,
        )
