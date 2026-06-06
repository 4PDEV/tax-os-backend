"""Citation assembly governance worker (TASK-006AB dry-run skeleton).

OD-021: single-worker assumption is acceptable. Concurrent citation workers require
execution-time advisory locks or row locks keyed by legal_object_version_id (future task).

Dry-run ``skipped`` means orchestration completed without citation execution — not that the
request was ignored (ineligible requests increment ``requests_skipped`` without a new skipped
result row from ``run()``).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.citation_assembly_governance_request import CitationAssemblyGovernanceRequest
from app.models.citation_assembly_governance_result import CitationAssemblyGovernanceResult
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.models.source_version import SourceVersion
from app.services.citation_assembly_governance.persistence import (
    get_latest_result_for_request,
    persist_citation_assembly_result,
)
from app.services.citation_assembly_governance.validation import (
    validate_actor_type,
    validate_legal_memory_lineage,
)
from app.workers.citation_assembly_governance.controlled_provider import (
    CONTROLLED_CITATION_ASSEMBLY_PROVIDER_NAME,
    CONTROLLED_CITATION_ASSEMBLY_PROVIDER_VERSION,
)
from app.workers.citation_assembly_governance.dry_run_provider import (
    DRY_RUN_CITATION_ASSEMBLY_PROVIDER_NAME,
    DRY_RUN_CITATION_ASSEMBLY_PROVIDER_VERSION,
    CitationAssemblyGovernanceProvider,
)
from app.workers.citation_assembly_governance.result import CitationAssemblyGovernanceRunSummary

EXECUTION_MODE_DRY_RUN = "dry_run"
EXECUTION_MODE_CONTROLLED_EXECUTION = "controlled_execution"
ALLOWED_EXECUTION_MODES = frozenset(
    {EXECUTION_MODE_DRY_RUN, EXECUTION_MODE_CONTROLLED_EXECUTION}
)

NON_ELIGIBLE_LATEST_STATUSES = frozenset({"duplicate_rejected", "rejected"})
TERMINAL_SKIP_STATUSES = frozenset({"assembled", "failed", "skipped"})

DRY_RUN_TERMINAL_STATUS = "skipped"
CONTROLLED_TERMINAL_STATUS = "assembled"


class CitationAssemblyGovernanceWorkerError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def legal_object_version_has_assembled_result(
    db: Session,
    *,
    legal_object_version_id: UUID,
) -> bool:
    """True when any governance result for this version reached assembled status."""
    row = db.execute(
        select(CitationAssemblyGovernanceResult.id)
        .where(
            CitationAssemblyGovernanceResult.legal_object_version_id == legal_object_version_id,
            CitationAssemblyGovernanceResult.citation_status == "assembled",
        )
        .limit(1)
    ).scalar_one_or_none()
    return row is not None


class CitationAssemblyGovernanceWorker:
    def __init__(self, *, provider: CitationAssemblyGovernanceProvider, mode: str):
        if mode not in ALLOWED_EXECUTION_MODES:
            raise CitationAssemblyGovernanceWorkerError(
                f"unsupported citation assembly governance execution mode: {mode}"
            )
        self._provider = provider
        self._mode = mode

    def _default_provider_identity(self) -> tuple[str, str]:
        if self._mode == EXECUTION_MODE_CONTROLLED_EXECUTION:
            return (
                CONTROLLED_CITATION_ASSEMBLY_PROVIDER_NAME,
                CONTROLLED_CITATION_ASSEMBLY_PROVIDER_VERSION,
            )
        return DRY_RUN_CITATION_ASSEMBLY_PROVIDER_NAME, DRY_RUN_CITATION_ASSEMBLY_PROVIDER_VERSION

    def load_requests(self, db: Session) -> list[CitationAssemblyGovernanceRequest]:
        stmt = select(CitationAssemblyGovernanceRequest).order_by(
            CitationAssemblyGovernanceRequest.created_at.asc(),
            CitationAssemblyGovernanceRequest.id.asc(),
        )
        return list(db.execute(stmt).scalars().all())

    def is_eligible(self, db: Session, request: CitationAssemblyGovernanceRequest) -> bool:
        if not request.citation_reason or not request.citation_reason.strip():
            return False
        try:
            validate_actor_type(request.requested_by_actor_type)
        except ValueError:
            return False

        legal_object = db.get(LegalObject, request.legal_object_id)
        legal_object_version = db.get(LegalObjectVersion, request.legal_object_version_id)
        source_version = db.get(SourceVersion, request.source_version_id)
        try:
            validate_legal_memory_lineage(
                legal_object,
                legal_object_version,
                source_version,
                legal_object_id=request.legal_object_id,
                legal_object_version_id=request.legal_object_version_id,
                source_version_id=request.source_version_id,
            )
        except ValueError:
            return False

        latest = get_latest_result_for_request(
            db, citation_assembly_governance_request_id=request.id
        )
        if latest is not None and latest.citation_status in NON_ELIGIBLE_LATEST_STATUSES:
            return False
        if latest is not None and latest.citation_status in TERMINAL_SKIP_STATUSES:
            if request.force_reassembly:
                return True
            return False

        if not request.force_reassembly and legal_object_version_has_assembled_result(
            db, legal_object_version_id=request.legal_object_version_id
        ):
            return False

        return True

    def run(
        self,
        db: Session,
        *,
        worker_name: str = "citation-assembly-governance-worker",
        worker_version: str | None = None,
    ) -> CitationAssemblyGovernanceRunSummary:
        default_name, default_version = self._default_provider_identity()
        resolved_version = worker_version or default_version

        requests_seen = processed = skipped = results_created = failures = replayed = 0

        for request in self.load_requests(db):
            requests_seen += 1
            if not self.is_eligible(db, request):
                skipped += 1
                continue

            if request.force_reassembly:
                replayed += 1

            legal_object_version = db.get(LegalObjectVersion, request.legal_object_version_id)
            if legal_object_version is None:
                skipped += 1
                continue

            try:
                persist_citation_assembly_result(
                    db,
                    citation_assembly_governance_request_id=request.id,
                    citation_status="accepted",
                    notes=f"accepted by {worker_name}",
                )
                results_created += 1

                provider_result = self._provider.run_assembly(
                    db, request, legal_object_version
                )
                provider_name = provider_result.provider_name or default_name
                provider_version = provider_result.provider_version or resolved_version

                if not provider_result.success:
                    persist_citation_assembly_result(
                        db,
                        citation_assembly_governance_request_id=request.id,
                        citation_status="failed",
                        error_category=provider_result.error_category or "unknown_failure",
                        error_message=provider_result.error_message,
                        notes=provider_result.notes
                        or f"provider failure ({provider_name}@{provider_version})",
                    )
                    results_created += 1
                    failures += 1
                    processed += 1
                    continue

                if self._mode == EXECUTION_MODE_CONTROLLED_EXECUTION:
                    persist_citation_assembly_result(
                        db,
                        citation_assembly_governance_request_id=request.id,
                        citation_status=CONTROLLED_TERMINAL_STATUS,
                        citation_id=provider_result.citation_id,
                        assembled_at=provider_result.assembled_at,
                        notes=provider_result.notes
                        or f"controlled citation execution completed by {worker_name}",
                    )
                else:
                    persist_citation_assembly_result(
                        db,
                        citation_assembly_governance_request_id=request.id,
                        citation_status=DRY_RUN_TERMINAL_STATUS,
                        citation_id=None,
                        assembled_at=None,
                        notes=provider_result.notes
                        or (
                            f"dry-run citation assembly lifecycle completed by {worker_name}; "
                            "citation_id intentionally null; no rendering"
                        ),
                    )
                results_created += 1
                processed += 1
            except Exception as exc:
                persist_citation_assembly_result(
                    db,
                    citation_assembly_governance_request_id=request.id,
                    citation_status="failed",
                    error_category="unknown_failure",
                    error_message=str(exc),
                    notes=f"worker failure recorded by {worker_name}",
                )
                results_created += 1
                failures += 1
                processed += 1

        return CitationAssemblyGovernanceRunSummary(
            requests_seen=requests_seen,
            requests_processed=processed,
            requests_skipped=skipped,
            results_created=results_created,
            failures=failures,
            requests_replayed=replayed,
        )
