IMMUTABILITY_RULES: tuple[str, ...] = (
    "legal_object_versions rows are immutable after creation",
    "raw_text must never be updated in place",
    "text_hash must never be updated in place",
    "start_offset and end_offset must never be updated in place",
    "historical version rows must not be overwritten or deleted",
    "corrections require new version rows or controlled version_status transitions",
    "legal_objects.updated_at may change only for controlled metadata (status, current_version_id)",
    "legal_objects.canonical_path is set at identity creation and not mutated",
    "legal_object_id is immutable once persisted",
)

MUTABLE_STATUS_FIELDS: tuple[str, ...] = (
    "version_status",
    "status",
    "current_version_id",
    "updated_at",
    "resolution_status",
)

IMMUTABLE_VERSION_FIELDS: tuple[str, ...] = (
    "raw_text",
    "text_hash",
    "start_offset",
    "end_offset",
    "object_label",
    "structural_unit_id",
    "source_version_id",
    "legal_object_version_id",
    "legal_object_id",
)


def immutability_rules_are_documented() -> bool:
    return len(IMMUTABILITY_RULES) >= 5 and len(IMMUTABLE_VERSION_FIELDS) >= 5
