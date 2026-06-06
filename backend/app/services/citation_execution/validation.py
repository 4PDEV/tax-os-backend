"""Validation for controlled citation execution."""

from uuid import UUID


class CitationExecutionValidationError(ValueError):
    pass


def validate_citation_hash(citation_hash: str) -> None:
    if not citation_hash or len(citation_hash) != 64:
        raise CitationExecutionValidationError("invalid_citation_hash")


def validate_citation_id(citation_id: str) -> None:
    if not citation_id or not citation_id.startswith("cit_"):
        raise CitationExecutionValidationError("invalid_citation_id")


def validate_location_reference(location_reference: str) -> None:
    if not location_reference or not location_reference.strip():
        raise CitationExecutionValidationError("invalid_location_reference")


def validate_provenance_pins(
    *,
    legal_object_id: str,
    legal_object_version_id: UUID,
    source_version_id: UUID,
) -> None:
    if not legal_object_id or not legal_object_id.strip():
        raise CitationExecutionValidationError("invalid_legal_object_id")
    if legal_object_version_id is None:
        raise CitationExecutionValidationError("invalid_legal_object_version_id")
    if source_version_id is None:
        raise CitationExecutionValidationError("invalid_source_version_id")
