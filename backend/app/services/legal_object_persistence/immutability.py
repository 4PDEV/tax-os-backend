"""Immutability guards for legal object persistence."""

from typing import Any

from app.services.legal_object_schema_contract.immutability import IMMUTABLE_VERSION_FIELDS

IMMUTABLE_LEGAL_OBJECT_FIELDS: frozenset[str] = frozenset(
    {
        "legal_object_id",
        "source_document_id",
        "country_id",
        "tax_type_id",
        "object_type",
        "canonical_path",
        "created_at",
    }
)

MUTABLE_LEGAL_OBJECT_FIELDS: frozenset[str] = frozenset(
    {
        "status",
        "current_version_id",
        "updated_at",
    }
)

IMMUTABLE_VERSION_FIELD_SET: frozenset[str] = frozenset(IMMUTABLE_VERSION_FIELDS)


class ImmutabilityViolationError(Exception):
    """Raised when a mutation targets immutable legal-memory fields."""


def assert_no_version_field_mutation(
    *,
    field_name: str,
    previous_value: Any,
    new_value: Any,
) -> None:
    if field_name not in IMMUTABLE_VERSION_FIELD_SET:
        return
    if previous_value != new_value:
        raise ImmutabilityViolationError(
            f"legal_object_versions.{field_name} is immutable and cannot be changed"
        )


def assert_no_destructive_legal_object_update(
    *,
    field_name: str,
    previous_value: Any,
    new_value: Any,
) -> None:
    if field_name in IMMUTABLE_LEGAL_OBJECT_FIELDS and previous_value != new_value:
        raise ImmutabilityViolationError(
            f"legal_objects.{field_name} is immutable and cannot be changed"
        )
    if field_name not in MUTABLE_LEGAL_OBJECT_FIELDS:
        raise ImmutabilityViolationError(
            f"legal_objects.{field_name} cannot be updated via service paths"
        )


def assert_hard_delete_prohibited(entity_label: str) -> None:
    raise ImmutabilityViolationError(
        f"hard delete of {entity_label} is prohibited; use archived or superseded status"
    )
