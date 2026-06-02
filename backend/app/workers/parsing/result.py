from dataclasses import dataclass


@dataclass(frozen=True)
class ParsingProviderResult:
    success: bool
    parser_status: str | None = None
    error_category: str | None = None
    error_message: str | None = None
    notes: str | None = None
    parser_name: str | None = None
    parser_version: str | None = None


@dataclass(frozen=True)
class ParsingRunSummary:
    triggers_seen: int = 0
    triggers_processed: int = 0
    triggers_skipped: int = 0
    parser_runs_created: int = 0
    trigger_results_created: int = 0
    failures: int = 0
