from dataclasses import dataclass
from enum import Enum


class RiskCategory(str, Enum):
    DUPLICATE = "duplicate"
    LINEAGE = "lineage"
    MIGRATION = "migration"
    HISTORICAL_OVERWRITE = "historical_overwrite"
    CONVERGENCE_BYPASS = "convergence_bypass"
    IDENTITY = "identity"
    ROLLBACK = "rollback"
    CROSS_REGIME = "cross_regime"


class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class PersistenceRisk:
    category: RiskCategory
    severity: RiskSeverity
    description: str
    mitigation: str


RISK_REGISTER: tuple[PersistenceRisk, ...] = (
    PersistenceRisk(
        category=RiskCategory.DUPLICATE,
        severity=RiskSeverity.HIGH,
        description="Identical text or hash persisted twice within the same source version.",
        mitigation="Apply duplicate_strategy rules; reject or version-as-new; never overwrite.",
    ),
    PersistenceRisk(
        category=RiskCategory.LINEAGE,
        severity=RiskSeverity.CRITICAL,
        description="Parent-child references corrupted during persistence or migration.",
        mitigation="Enforce lineage_strategy rules; batch validation before commit.",
    ),
    PersistenceRisk(
        category=RiskCategory.MIGRATION,
        severity=RiskSeverity.HIGH,
        description="Migration drift between planning phases and implemented schema.",
        mitigation="Follow migration_plan phase ordering; no skip-ahead without architecture approval.",
    ),
    PersistenceRisk(
        category=RiskCategory.HISTORICAL_OVERWRITE,
        severity=RiskSeverity.CRITICAL,
        description="In-place update of persisted legal text or canonical IDs.",
        mitigation="Append-only persistence; NEVER rules enforced at service layer.",
    ),
    PersistenceRisk(
        category=RiskCategory.CONVERGENCE_BYPASS,
        severity=RiskSeverity.CRITICAL,
        description="Direct persistence from segmentation, structure_parser, or legacy legal_objects.",
        mitigation="assert_canonical_persistence_input; blocked source list in contract.",
    ),
    PersistenceRisk(
        category=RiskCategory.IDENTITY,
        severity=RiskSeverity.HIGH,
        description="Canonical legal_object_id instability across extraction runs.",
        mitigation="Centralize on generate_legal_object_id; validate before persistence planning.",
    ),
    PersistenceRisk(
        category=RiskCategory.ROLLBACK,
        severity=RiskSeverity.HIGH,
        description="Inability to restore prior persisted state after failed persistence batch.",
        mitigation="Version_status transitions only; transactional batch boundaries in future implementation.",
    ),
    PersistenceRisk(
        category=RiskCategory.CROSS_REGIME,
        severity=RiskSeverity.MEDIUM,
        description="Cross-jurisdiction collision of canonical_path or legal_object_id.",
        mitigation="Defer cross-regime merge; namespace by source_version jurisdiction metadata.",
    ),
)

BLOCKED_ASSUMPTIONS: tuple[str, ...] = (
    "Legal objects can be persisted before convergence approval.",
    "Legacy lo-NNNN segment IDs are valid persistence keys.",
    "Duplicate canonical_path within a version can be silently merged.",
    "Historical persisted rows may be updated when source text changes.",
    "Effective-date logic can execute in the same task as initial persistence tables.",
    "Citation anchors may persist before legal objects are stable.",
    "Cross-pipeline deduplication is automatic without explicit strategy.",
)
