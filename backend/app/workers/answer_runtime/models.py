"""Answer worker envelope models (TASK-009C).

Queue lifecycle states are documented only — no queue infrastructure.
"""

from dataclasses import dataclass
from uuid import UUID

# Documented queue lifecycle (no real queue implementation).
QUEUE_LIFECYCLE_ACCEPTED = "accepted"
QUEUE_LIFECYCLE_RUNNING = "running"
QUEUE_LIFECYCLE_COMPLETED = "completed"
QUEUE_LIFECYCLE_FAILED = "failed"

DOCUMENTED_QUEUE_LIFECYCLE = frozenset(
    {
        QUEUE_LIFECYCLE_ACCEPTED,
        QUEUE_LIFECYCLE_RUNNING,
        QUEUE_LIFECYCLE_COMPLETED,
        QUEUE_LIFECYCLE_FAILED,
    }
)


class AnswerWorkerError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class AnswerWorkerRequest:
    ranking_request_id: UUID
    contract_version: str
    assembly_contract_version: str
    include_rendered_citation_text: bool = False
    force_replay: bool = False
    replay_nonce: str | None = None


@dataclass(frozen=True)
class AnswerWorkerOutcome:
    answer_request_id: UUID
    answer_result_id: UUID
    worker_status: str
    answer_status: str
    evidence_entry_count: int
    uncertainty_flag_count: int
    error_category: str | None = None
