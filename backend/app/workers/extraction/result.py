from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractionProviderResult:
    success: bool
    error_category: str | None = None
    error_message: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class ExtractionRunSummary:
    triggers_seen: int = 0
    triggers_processed: int = 0
    triggers_skipped: int = 0
    extraction_runs_created: int = 0
    trigger_results_created: int = 0
    failures: int = 0
