from sqlalchemy.orm import Session

from app.workers.citation_assembly_governance.dry_run_provider import (
    DryRunCitationAssemblyGovernanceProvider,
)
from app.workers.citation_assembly_governance.result import CitationAssemblyGovernanceRunSummary
from app.workers.citation_assembly_governance.worker import (
    EXECUTION_MODE_DRY_RUN,
    CitationAssemblyGovernanceWorker,
    CitationAssemblyGovernanceWorkerError,
)


def run_citation_assembly_governance_dry_run(
    db: Session,
    *,
    worker_name: str = "citation-assembly-governance-worker",
    worker_version: str = "0.1.0",
    dry_run: bool = True,
) -> CitationAssemblyGovernanceRunSummary:
    if not dry_run:
        raise CitationAssemblyGovernanceWorkerError(
            "dry_run=True is required for run_citation_assembly_governance_dry_run"
        )
    worker = CitationAssemblyGovernanceWorker(
        provider=DryRunCitationAssemblyGovernanceProvider(),
        mode=EXECUTION_MODE_DRY_RUN,
    )
    return worker.run(db, worker_name=worker_name, worker_version=worker_version)


def run_citation_assembly_dry_run(
    db: Session,
    *,
    worker_name: str = "citation-assembly-governance-worker",
    worker_version: str = "0.1.0",
    dry_run: bool = True,
) -> CitationAssemblyGovernanceRunSummary:
    """TASK-006AB spec entrypoint — delegates to governance dry-run runner."""
    return run_citation_assembly_governance_dry_run(
        db,
        worker_name=worker_name,
        worker_version=worker_version,
        dry_run=dry_run,
    )
