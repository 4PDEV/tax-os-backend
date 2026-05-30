from dataclasses import dataclass
from enum import Enum


class LineageExpectation(str, Enum):
    """Planning expectations for parent-child persistence relationships."""

    PRESERVE_PARENT_REFERENCE = "preserve_parent_reference"
    PRESERVE_ANCESTOR_CHAIN = "preserve_ancestor_chain"
    NO_ORPHAN_CHILDREN = "no_orphan_children"
    SUPERSEDE_WITHOUT_MUTATION = "supersede_without_mutation"
    EFFECTIVE_DATE_LINKAGE = "effective_date_linkage"


@dataclass(frozen=True)
class LineageStrategyRule:
    expectation: LineageExpectation
    description: str


LINEAGE_STRATEGY_RULES: tuple[LineageStrategyRule, ...] = (
    LineageStrategyRule(
        expectation=LineageExpectation.PRESERVE_PARENT_REFERENCE,
        description=(
            "parent_legal_object_id must be persisted when present on the "
            "converged candidate; null only for root objects."
        ),
    ),
    LineageStrategyRule(
        expectation=LineageExpectation.PRESERVE_ANCESTOR_CHAIN,
        description=(
            "lineage_chain stores ordered legal_object_id ancestry for audit "
            "and rollback; never recomputed in ways that break history."
        ),
    ),
    LineageStrategyRule(
        expectation=LineageExpectation.NO_ORPHAN_CHILDREN,
        description=(
            "A child must not be persisted when its parent is absent from the "
            "same persistence batch unless convergence_status is partial and "
            "explicitly flagged."
        ),
    ),
    LineageStrategyRule(
        expectation=LineageExpectation.SUPERSEDE_WITHOUT_MUTATION,
        description=(
            "Superseding a source version marks prior persisted objects as "
            "superseded; historical rows and text remain immutable."
        ),
    ),
    LineageStrategyRule(
        expectation=LineageExpectation.EFFECTIVE_DATE_LINKAGE,
        description=(
            "effective_from and effective_to on persisted objects link to "
            "source_version temporal metadata; execution deferred to later task."
        ),
    ),
)

SUPERSEDING_RULES: tuple[str, ...] = (
    "New source_version supersedes prior version objects via version_status only.",
    "Historical persisted text and hashes are never updated in place.",
    "Lineage references remain valid after supersession.",
)

VERSION_CHAIN_EXPECTATIONS: tuple[str, ...] = (
    "Each persisted legal object belongs to exactly one source_version_id.",
    "Cross-version lineage is expressed via metadata links, not ID mutation.",
    "Rollback restores prior version_status without deleting historical rows.",
)
