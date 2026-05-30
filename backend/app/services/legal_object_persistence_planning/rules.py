from dataclasses import dataclass

NEVER_RULES: tuple[str, ...] = (
    "overwrite persisted legal objects",
    "mutate historical text",
    "change canonical IDs after persistence",
    "break lineage chains",
    "persist unconverged candidates",
    "persist rejected convergence outputs",
    "persist directly from segmentation outputs",
    "persist directly from structure_parser outputs",
    "persist directly from legal_object_extraction outputs",
    "persist directly from legacy legal_objects outputs",
    "silently discard source provenance",
    "infer legal meaning during persistence",
)

ALWAYS_RULES: tuple[str, ...] = (
    "preserve historical versions",
    "preserve source_version_id",
    "preserve text_hash",
    "preserve start_offset and end_offset",
    "preserve canonical_path",
    "preserve parent-child lineage",
    "preserve persistence and extraction timestamps",
    "accept only ConvergedLegalObjectCandidate as persistence input",
    "require convergence_status other than rejected before persistence",
    "maintain audit trail for persistence operations",
    "support rollback to prior persisted states",
    "treat effective-date fields as first-class metadata",
)


@dataclass(frozen=True)
class PersistenceRuleSet:
    never: tuple[str, ...]
    always: tuple[str, ...]


PERSISTENCE_RULES = PersistenceRuleSet(never=NEVER_RULES, always=ALWAYS_RULES)


def rules_are_complete() -> bool:
    """Return True when mandatory NEVER and ALWAYS rule sets are non-empty."""
    return bool(NEVER_RULES) and bool(ALWAYS_RULES)
