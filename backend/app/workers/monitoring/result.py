from dataclasses import dataclass, field


@dataclass(frozen=True)
class MonitoringDetectedItem:
    source_url: str
    source_name: str
    source_type: str
    detected_title: str
    detected_url: str
    detection_method: str
    change_type: str
    confidence: str
    notes: str | None = None
    checksum_sha256: str | None = None
    previous_checksum_sha256: str | None = None
    source_registry_id: str | None = None


@dataclass(frozen=True)
class MonitoringProviderResult:
    success: bool
    items: list[MonitoringDetectedItem] = field(default_factory=list)
    error_category: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class MonitoringRunSummary:
    attempts_started: int = 0
    attempts_completed: int = 0
    attempts_failed: int = 0
    events_created: int = 0
    candidates_created: int = 0
