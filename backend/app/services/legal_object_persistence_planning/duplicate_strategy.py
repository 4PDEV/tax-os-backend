from dataclasses import dataclass
from enum import Enum

from app.services.legal_object_persistence_planning.models import PlannedDuplicateStrategy


class DuplicateScenario(str, Enum):
    """Planning scenarios for duplicate or colliding legal object identity."""

    IDENTICAL_TEXT_ACROSS_VERSIONS = "identical_text_across_versions"
    IDENTICAL_STRUCTURE_ACROSS_VERSIONS = "identical_structure_across_versions"
    DUPLICATE_CANONICAL_PATH = "duplicate_canonical_path"
    DUPLICATE_TEXT_HASH = "duplicate_text_hash"
    CONFLICTING_LEGAL_OBJECT_ID = "conflicting_legal_object_id"
    CROSS_JURISDICTION_COLLISION = "cross_jurisdiction_collision"


@dataclass(frozen=True)
class DuplicateStrategyRule:
    scenario: DuplicateScenario
    strategy: PlannedDuplicateStrategy
    description: str


DUPLICATE_STRATEGY_RULES: tuple[DuplicateStrategyRule, ...] = (
    DuplicateStrategyRule(
        scenario=DuplicateScenario.IDENTICAL_TEXT_ACROSS_VERSIONS,
        strategy=PlannedDuplicateStrategy.VERSION_AS_NEW,
        description=(
            "Same raw text in a new source_version_id creates a new persisted "
            "version row; prior version remains immutable."
        ),
    ),
    DuplicateStrategyRule(
        scenario=DuplicateScenario.IDENTICAL_STRUCTURE_ACROSS_VERSIONS,
        strategy=PlannedDuplicateStrategy.LINK_LINEAGE,
        description=(
            "Structural equivalence across versions links via lineage metadata "
            "without mutating historical persisted rows."
        ),
    ),
    DuplicateStrategyRule(
        scenario=DuplicateScenario.DUPLICATE_CANONICAL_PATH,
        strategy=PlannedDuplicateStrategy.FLAG_FOR_REVIEW,
        description=(
            "Duplicate canonical_path within the same source_version_id requires "
            "explicit review before persistence approval."
        ),
    ),
    DuplicateStrategyRule(
        scenario=DuplicateScenario.DUPLICATE_TEXT_HASH,
        strategy=PlannedDuplicateStrategy.LINK_LINEAGE,
        description=(
            "Matching text_hash within a source_version_id suggests duplicate "
            "content; link or reject — never overwrite silently."
        ),
    ),
    DuplicateStrategyRule(
        scenario=DuplicateScenario.CONFLICTING_LEGAL_OBJECT_ID,
        strategy=PlannedDuplicateStrategy.REJECT,
        description=(
            "Conflicting legal_object_id for different content must reject "
            "persistence until identity inputs are reconciled."
        ),
    ),
    DuplicateStrategyRule(
        scenario=DuplicateScenario.CROSS_JURISDICTION_COLLISION,
        strategy=PlannedDuplicateStrategy.DEFER,
        description=(
            "Cross-jurisdiction canonical_path or hash collisions defer to "
            "architecture addendum; no automatic merge across regimes."
        ),
    ),
)


def get_strategy_for_scenario(scenario: DuplicateScenario) -> PlannedDuplicateStrategy:
    for rule in DUPLICATE_STRATEGY_RULES:
        if rule.scenario == scenario:
            return rule.strategy
    return PlannedDuplicateStrategy.DEFER
