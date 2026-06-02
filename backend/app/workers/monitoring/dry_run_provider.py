from typing import Protocol

from app.models.source_allowlist_entry import SourceAllowlistEntry
from app.services.monitoring.enums import ChangeType, MonitoringConfidence
from app.workers.monitoring.result import MonitoringDetectedItem, MonitoringProviderResult


class MonitoringProvider(Protocol):
    def check_source(self, allowlist_entry: SourceAllowlistEntry) -> MonitoringProviderResult:
        """Return deterministic monitoring detection results for one source."""


class DryRunMonitoringProvider:
    """Synthetic provider for internal validation only.

    This provider must never perform network, crawler, or scraper behavior.
    """

    def check_source(self, allowlist_entry: SourceAllowlistEntry) -> MonitoringProviderResult:
        item = MonitoringDetectedItem(
            source_url=allowlist_entry.base_url,
            source_name=allowlist_entry.authority_name,
            source_type=allowlist_entry.source_type,
            detected_title="Dry Run Monitoring Candidate",
            detected_url=f"{allowlist_entry.base_url.rstrip('/')}/dry-run",
            detection_method="dry_run_synthetic",
            change_type=ChangeType.NEW_DOCUMENT.value,
            confidence=MonitoringConfidence.LOW.value,
            notes="Synthetic dry-run monitoring event",
        )
        return MonitoringProviderResult(success=True, items=[item])
