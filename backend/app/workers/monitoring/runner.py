from sqlalchemy.orm import Session

from app.workers.monitoring.dry_run_provider import DryRunMonitoringProvider
from app.workers.monitoring.result import MonitoringRunSummary
from app.workers.monitoring.worker import SourceMonitoringWorker


def run_monitoring_dry_run(
    db: Session,
    *,
    agent_name: str = "source-monitoring-worker",
    agent_version: str = "0.1.0",
    dry_run: bool = True,
) -> MonitoringRunSummary:
    worker = SourceMonitoringWorker(provider=DryRunMonitoringProvider(), dry_run=dry_run)
    return worker.run(db, agent_name=agent_name, agent_version=agent_version)
