from sqlalchemy.orm import Session

from app.workers.extraction.dry_run_provider import DryRunExtractionProvider
from app.workers.extraction.result import ExtractionRunSummary
from app.workers.extraction.worker import ExtractionWorker


def run_extraction_dry_run(
    db: Session,
    *,
    worker_name: str = "extraction-worker",
    worker_version: str = "0.1.0",
    dry_run: bool = True,
) -> ExtractionRunSummary:
    worker = ExtractionWorker(provider=DryRunExtractionProvider(), dry_run=dry_run)
    return worker.run(db, worker_name=worker_name, worker_version=worker_version)
