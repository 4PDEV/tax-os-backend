from dataclasses import dataclass
from enum import Enum


class MigrationPhase(str, Enum):
    """Proposed phased migration sequence for legal object persistence."""

    PHASE_1_TABLES = "phase_1_legal_object_persistence_tables"
    PHASE_2_LINEAGE = "phase_2_lineage_constraints"
    PHASE_3_EFFECTIVE_DATES = "phase_3_effective_date_indexing"
    PHASE_4_CITATION_ANCHORS = "phase_4_citation_anchor_persistence"


@dataclass(frozen=True)
class MigrationPhasePlan:
    phase: MigrationPhase
    order: int
    title: str
    description: str
    prerequisites: tuple[str, ...]


MIGRATION_PHASES: tuple[MigrationPhasePlan, ...] = (
    MigrationPhasePlan(
        phase=MigrationPhase.PHASE_1_TABLES,
        order=1,
        title="Legal object persistence tables",
        description=(
            "Introduce append-only legal object persistence tables keyed by "
            "legal_object_id and source_version_id. Input: converged candidates only."
        ),
        prerequisites=("TASK-002H convergence approved", "persistence planning contract approved"),
    ),
    MigrationPhasePlan(
        phase=MigrationPhase.PHASE_2_LINEAGE,
        order=2,
        title="Lineage constraints",
        description=(
            "Add foreign-key or application-level lineage constraints for "
            "parent_legal_object_id and lineage_chain integrity."
        ),
        prerequisites=("phase_1_legal_object_persistence_tables",),
    ),
    MigrationPhasePlan(
        phase=MigrationPhase.PHASE_3_EFFECTIVE_DATES,
        order=3,
        title="Effective-date indexing",
        description=(
            "Index effective_from and effective_to for temporal queries without "
            "mutating historical persisted rows."
        ),
        prerequisites=("phase_2_lineage_constraints",),
    ),
    MigrationPhasePlan(
        phase=MigrationPhase.PHASE_4_CITATION_ANCHORS,
        order=4,
        title="Citation anchor persistence",
        description=(
            "Persist citation anchors linked to persisted legal_object_id rows "
            "after legal object persistence is stable."
        ),
        prerequisites=("phase_3_effective_date_indexing",),
    ),
)


def migration_phases_are_ordered() -> bool:
    orders = [plan.order for plan in MIGRATION_PHASES]
    return orders == sorted(orders) and len(orders) == len(set(orders))
