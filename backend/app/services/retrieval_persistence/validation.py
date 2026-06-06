from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.citation import Citation
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.models.source_version import SourceVersion

RETRIEVAL_MODES = {"AS_OF_DATE", "EXACT_VERSION", "LATEST_VERSION"}
REQUESTED_BY_ACTOR_TYPES = {"user", "system", "worker", "admin", "test"}
RETRIEVAL_STATUSES = {
    "pending",
    "accepted",
    "completed",
    "failed",
    "skipped",
    "duplicate_rejected",
}
RETRIEVAL_ERROR_CATEGORIES = {
    "invalid_request",
    "temporal_scope_missing",
    "version_missing",
    "citation_missing",
    "provenance_incomplete",
    "duplicate_retrieval",
    "retrieval_pipeline_unavailable",
    "unknown_failure",
}

EVIDENCE_METADATA_ALLOWED_KEYS = {
    "structural_path",
    "source_label",
    "citation_label",
    "object_label",
    "object_type",
    "location_reference",
    "deterministic_sort_key",
    "provenance_notes",
}

EVIDENCE_METADATA_PROHIBITED_KEYS = {
    "answer_text",
    "legal_conclusion",
    "applicability_flag",
    "ranking_score",
    "relevance_score",
    "confidence_score",
    "semantic_score",
    "ai_output",
    "llm_output",
    "recommendation",
    "advice",
    "interpretation",
}

PROHIBITED_TABLE_COLUMNS = {
    "answer_text",
    "legal_conclusion",
    "applicability_flag",
    "ranking_score",
    "relevance_score",
    "confidence_score",
    "semantic_score",
    "ai_output",
}


def validate_retrieval_mode(retrieval_mode: str) -> None:
    if retrieval_mode not in RETRIEVAL_MODES:
        raise ValueError(f"invalid retrieval_mode: {retrieval_mode}")


def validate_actor_type(actor_type: str) -> None:
    if actor_type not in REQUESTED_BY_ACTOR_TYPES:
        raise ValueError(f"invalid requested_by_actor_type: {actor_type}")


def validate_retrieval_status(retrieval_status: str) -> None:
    if retrieval_status not in RETRIEVAL_STATUSES:
        raise ValueError(f"invalid retrieval_status: {retrieval_status}")


def validate_retrieval_error_category(error_category: str | None) -> None:
    if error_category is not None and error_category not in RETRIEVAL_ERROR_CATEGORIES:
        raise ValueError(f"invalid error_category: {error_category}")


def validate_evidence_metadata(evidence_metadata: dict | None) -> None:
    if evidence_metadata is None:
        return
    if not isinstance(evidence_metadata, dict):
        raise ValueError("invalid evidence_metadata")
    for key in evidence_metadata:
        if key in EVIDENCE_METADATA_PROHIBITED_KEYS:
            raise ValueError(f"prohibited evidence_metadata key: {key}")
        if key not in EVIDENCE_METADATA_ALLOWED_KEYS:
            raise ValueError(f"unknown evidence_metadata key: {key}")


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


def validate_citation_reference(
    session: Session,
    *,
    citation_id: str | None,
    citation_hash: str | None,
    legal_object_id: str,
    legal_object_version_id: UUID,
    source_version_id: UUID,
) -> None:
    if citation_id is None and citation_hash is None:
        return
    if (citation_id is None) != (citation_hash is None):
        raise ValueError("citation_id_and_hash_must_be_paired")

    citation = session.execute(
        select(Citation).where(Citation.citation_id == citation_id).limit(1)
    ).scalar_one_or_none()
    if citation is None:
        raise ValueError("citation_missing")
    if citation.citation_hash != citation_hash:
        raise ValueError("citation_hash_mismatch")
    if citation.legal_object_version_id != legal_object_version_id:
        raise ValueError("citation_version_mismatch")
    if citation.legal_object_id != legal_object_id:
        raise ValueError("citation_object_mismatch")
    if citation.source_version_id != source_version_id:
        raise ValueError("citation_source_mismatch")
