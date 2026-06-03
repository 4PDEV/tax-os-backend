from uuid import UUID

from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.models.source_version import SourceVersion

REQUESTED_BY_ACTOR_TYPES = {"user", "system", "worker", "admin", "test"}
CITATION_STATUSES = {
    "pending",
    "accepted",
    "rejected",
    "assembled",
    "failed",
    "skipped",
    "duplicate_rejected",
}
CITATION_ERROR_CATEGORIES = {
    "legal_object_missing",
    "version_missing",
    "provenance_incomplete",
    "duplicate_citation",
    "invalid_request",
    "citation_pipeline_unavailable",
    "unknown_failure",
}


def validate_actor_type(actor_type: str) -> None:
    if actor_type not in REQUESTED_BY_ACTOR_TYPES:
        raise ValueError(f"invalid requested_by_actor_type: {actor_type}")


def validate_citation_status(citation_status: str) -> None:
    if citation_status not in CITATION_STATUSES:
        raise ValueError(f"invalid citation_status: {citation_status}")


def validate_citation_error_category(error_category: str | None) -> None:
    if error_category is not None and error_category not in CITATION_ERROR_CATEGORIES:
        raise ValueError(f"invalid error_category: {error_category}")


def validate_legal_memory_lineage(
    legal_object: LegalObject | None,
    legal_object_version: LegalObjectVersion | None,
    source_version: SourceVersion | None,
    *,
    legal_object_id: str,
    legal_object_version_id: UUID,
    source_version_id: UUID,
) -> None:
    if legal_object is None:
        raise ValueError("legal_object_missing")
    if legal_object_version is None:
        raise ValueError("version_missing")
    if source_version is None:
        raise ValueError("provenance_incomplete")
    if legal_object_version.legal_object_id != legal_object_id:
        raise ValueError("invalid_request")
    if legal_object_version.source_version_id != source_version_id:
        raise ValueError("provenance_incomplete")
