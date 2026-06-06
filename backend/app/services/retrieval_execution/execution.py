"""Controlled retrieval execution (TASK-007E).

Selects version-pinned evidence and persists retrieval_evidence_references only.
No ranking, answers, citation assembly, AI, or semantic search.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.legal_object import LegalObject
from app.models.source_version import SourceVersion
from app.models.retrieval_request import RetrievalRequest
from app.services.retrieval_execution.citation_lookup import lookup_citation_for_version
from app.services.retrieval_execution.models import EvidenceCandidate, RetrievalExecutionOutcome
from app.services.retrieval_execution.ordering import sort_evidence_candidates
from app.services.retrieval_execution.selection import (
    RetrievalSelectionError,
    select_versions_for_request,
)
from app.services.retrieval_persistence.persistence import (
    RetrievalPersistenceError,
    create_evidence_reference,
)


class RetrievalExecutionError(Exception):
    def __init__(self, category: str, message: str):
        self.category = category
        self.message = message
        super().__init__(message)


def _build_candidates(
    db: Session,
    versions: list,
) -> list[EvidenceCandidate]:
    candidates: list[EvidenceCandidate] = []
    for version in versions:
        legal_object = db.get(LegalObject, version.legal_object_id)
        source_version = db.get(SourceVersion, version.source_version_id)
        if legal_object is None or source_version is None:
            raise RetrievalExecutionError("provenance_incomplete", "legal memory lineage incomplete")

        citation = lookup_citation_for_version(
            db, legal_object_version_id=version.legal_object_version_id
        )
        object_identifier = f"{version.structural_unit_id}:{version.object_label}"
        candidates.append(
            EvidenceCandidate(
                legal_object_id=version.legal_object_id,
                legal_object_version_id=version.legal_object_version_id,
                source_version_id=version.source_version_id,
                source_document_id=legal_object.source_document_id,
                effective_from=version.effective_from,
                object_identifier=object_identifier,
                object_type=legal_object.object_type,
                object_label=version.object_label,
                citation_id=citation.citation_id if citation else None,
                citation_hash=citation.citation_hash if citation else None,
                location_reference=citation.location_reference if citation else None,
            )
        )
    return candidates


def execute_controlled_retrieval(
    db: Session,
    *,
    request: RetrievalRequest,
    retrieval_result_id: UUID,
) -> RetrievalExecutionOutcome:
    try:
        versions = select_versions_for_request(db, request)
    except RetrievalSelectionError as exc:
        raise RetrievalExecutionError(exc.category, exc.message) from exc

    candidates = _build_candidates(db, versions)
    ordered = sort_evidence_candidates(candidates)

    persisted = 0
    for index, candidate in enumerate(ordered, start=1):
        metadata = {
            "object_label": candidate.object_label,
            "object_type": candidate.object_type,
            "location_reference": candidate.location_reference,
        }
        if candidate.location_reference is None:
            metadata.pop("location_reference")
        try:
            create_evidence_reference(
                db,
                retrieval_result_id=retrieval_result_id,
                legal_object_id=candidate.legal_object_id,
                legal_object_version_id=candidate.legal_object_version_id,
                source_version_id=candidate.source_version_id,
                deterministic_order_index=index,
                citation_id=candidate.citation_id,
                citation_hash=candidate.citation_hash,
                source_document_id=candidate.source_document_id,
                location_reference=candidate.location_reference,
                object_identifier=candidate.object_identifier,
                evidence_metadata=metadata,
            )
        except RetrievalPersistenceError as exc:
            raise RetrievalExecutionError(
                "provenance_incomplete" if "citation" in str(exc) or "provenance" in str(exc) else "invalid_request",
                str(exc),
            ) from exc
        persisted += 1

    return RetrievalExecutionOutcome(
        evidence_count=persisted,
        notes=f"controlled retrieval execution; evidence_count={persisted}",
    )
