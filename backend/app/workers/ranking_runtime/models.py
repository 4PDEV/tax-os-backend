"""Ranking worker envelope models (U-01).

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


@dataclass(frozen=True)
class RankingWorkerRequest:
    retrieval_result_id: UUID
    ranking_profile: str
    contract_version: str
    force_replay: bool = False
    replay_nonce: str | None = None


@dataclass(frozen=True)
class RankingWorkerOutcome:
    ranking_result_id: UUID
    ranking_status: str
    rank_count: int
    error_category: str | None = None
