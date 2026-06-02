from sqlalchemy.orm import Session

from app.workers.parsing.dry_run_provider import DryRunParsingProvider
from app.workers.parsing.result import ParsingRunSummary
from app.workers.parsing.worker import EXECUTION_MODE_DRY_RUN, ParsingWorker, ParsingWorkerError


def run_parsing_dry_run(
    db: Session,
    *,
    worker_name: str = "parsing-worker",
    worker_version: str = "0.1.0",
    dry_run: bool = True,
) -> ParsingRunSummary:
    if not dry_run:
        raise ParsingWorkerError("dry_run=True is required for run_parsing_dry_run")
    worker = ParsingWorker(
        provider=DryRunParsingProvider(),
        mode=EXECUTION_MODE_DRY_RUN,
    )
    return worker.run(db, worker_name=worker_name, worker_version=worker_version)
