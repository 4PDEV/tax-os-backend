"""Append-only retrieval persistence (TASK-007C).

Persistence records retrieval intent, lifecycle, and evidence references only —
no retrieval execution, no ranking, no answer assembly, no AI search.

OD-021: single-worker assumption; concurrent workers need execution-time locks (future task).
"""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.models.retrieval_evidence_reference import RetrievalEvidenceReference
from app.models.retrieval_request import RetrievalRequest
from app.models.retrieval_result import RetrievalResult
from app.models.source_version import SourceVersion
from app.services.retrieval_persistence.hashing import compute_request_hash
from app.services.retrieval_persistence.validation import (
    validate_actor_type,
    validate_citation_reference,
    validate_evidence_metadata,
    validate_legal_memory_lineage,
    validate_retrieval_error_category,
    validate_retrieval_mode,
    validate_retrieval_status,
)


class RetrievalPersistenceError(Exception):
    pass


def find_existing_default_request(
    session: Session,
    *,
    request_hash: str,
) -> RetrievalRequest | None:
    return session.execute(
        select(RetrievalRequest)
        .where(
            RetrievalRequest.request_hash == request_hash,
            RetrievalRequest.force_replay.is_(False),
        )
        .order_by(RetrievalRequest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def get_request_by_hash(
    session: Session,
    *,
    request_hash: str,
) -> RetrievalRequest | None:
    return session.execute(
        select(RetrievalRequest)
        .where(RetrievalRequest.request_hash == request_hash)
        .order_by(RetrievalRequest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def create_retrieval_request(
    session: Session,
    *,
    retrieval_mode: str,
    jurisdiction_code: str,
    scope_envelope: dict,
    include_canonical_text: bool,
    include_rendered_citation_text: bool,
    requested_by_actor_type: str,
    as_of_date: date | None = None,
    legal_object_version_id: UUID | None = None,
    tax_type_code: str | None = None,
    requested_by_actor_identifier: str | None = None,
    requested_at: datetime | None = None,
    force_replay: bool = False,
    notes: str | None = None,
    replay_nonce: str | None = None,
) -> RetrievalRequest:
    try:
        validate_retrieval_mode(retrieval_mode)
        validate_actor_type(requested_by_actor_type)
    except ValueError as exc:
        raise RetrievalPersistenceError(str(exc)) from exc

    request_hash = compute_request_hash(
        retrieval_mode=retrieval_mode,
        jurisdiction_code=jurisdiction_code,
        scope_envelope=scope_envelope,
        include_canonical_text=include_canonical_text,
        include_rendered_citation_text=include_rendered_citation_text,
        tax_type_code=tax_type_code,
        as_of_date=as_of_date,
        legal_object_version_id=legal_object_version_id,
        force_replay=force_replay,
        replay_nonce=replay_nonce,
    )

    if not force_replay:
        existing = find_existing_default_request(session, request_hash=request_hash)
        if existing is not None:
            raise RetrievalPersistenceError("duplicate_default_request_for_hash")

    request = RetrievalRequest(
        request_hash=request_hash,
        retrieval_mode=retrieval_mode,
        as_of_date=as_of_date,
        legal_object_version_id=legal_object_version_id,
        jurisdiction_code=jurisdiction_code,
        tax_type_code=tax_type_code,
        scope_envelope=scope_envelope,
        requested_by_actor_type=requested_by_actor_type,
        requested_by_actor_identifier=requested_by_actor_identifier,
        requested_at=requested_at or utc_now(),
        force_replay=force_replay,
        include_canonical_text=include_canonical_text,
        include_rendered_citation_text=include_rendered_citation_text,
        notes=notes,
        created_at=utc_now(),
    )
    session.add(request)
    session.flush()
    return request


def create_retrieval_result(
    session: Session,
    *,
    retrieval_request_id: UUID,
    retrieval_status: str,
    result_count: int | None = None,
    completed_at: datetime | None = None,
    error_category: str | None = None,
    error_message: str | None = None,
    notes: str | None = None,
) -> RetrievalResult:
    try:
        validate_retrieval_status(retrieval_status)
        validate_retrieval_error_category(error_category)
    except ValueError as exc:
        raise RetrievalPersistenceError(str(exc)) from exc

    request = session.get(RetrievalRequest, retrieval_request_id)
    if request is None:
        raise RetrievalPersistenceError(f"retrieval_request not found: {retrieval_request_id}")

    result = RetrievalResult(
        retrieval_request_id=retrieval_request_id,
        retrieval_status=retrieval_status,
        result_count=result_count,
        completed_at=completed_at,
        error_category=error_category,
        error_message=error_message,
        notes=notes,
        created_at=utc_now(),
    )
    session.add(result)
    session.flush()
    return result


def create_evidence_reference(
    session: Session,
    *,
    retrieval_result_id: UUID,
    legal_object_id: str,
    legal_object_version_id: UUID,
    source_version_id: UUID,
    deterministic_order_index: int,
    citation_id: str | None = None,
    citation_hash: str | None = None,
    source_document_id: UUID | None = None,
    location_reference: str | None = None,
    object_identifier: str | None = None,
    evidence_metadata: dict | None = None,
) -> RetrievalEvidenceReference:
    if deterministic_order_index < 1:
        raise RetrievalPersistenceError("invalid_request")

    try:
        validate_evidence_metadata(evidence_metadata)
    except ValueError as exc:
        raise RetrievalPersistenceError(str(exc)) from exc

    legal_object = session.get(LegalObject, legal_object_id)
    legal_object_version = session.get(LegalObjectVersion, legal_object_version_id)
    source_version = session.get(SourceVersion, source_version_id)
    try:
        validate_legal_memory_lineage(
            legal_object,
            legal_object_version,
            source_version,
            legal_object_id=legal_object_id,
            legal_object_version_id=legal_object_version_id,
            source_version_id=source_version_id,
        )
    except ValueError as exc:
        raise RetrievalPersistenceError(str(exc)) from exc

    try:
        validate_citation_reference(
            session,
            citation_id=citation_id,
            citation_hash=citation_hash,
            legal_object_id=legal_object_id,
            legal_object_version_id=legal_object_version_id,
            source_version_id=source_version_id,
        )
    except ValueError as exc:
        raise RetrievalPersistenceError(str(exc)) from exc

    result = session.get(RetrievalResult, retrieval_result_id)
    if result is None:
        raise RetrievalPersistenceError(f"retrieval_result not found: {retrieval_result_id}")

    reference = RetrievalEvidenceReference(
        retrieval_result_id=retrieval_result_id,
        legal_object_id=legal_object_id,
        legal_object_version_id=legal_object_version_id,
        source_version_id=source_version_id,
        citation_id=citation_id,
        citation_hash=citation_hash,
        source_document_id=source_document_id,
        location_reference=location_reference,
        object_identifier=object_identifier,
        deterministic_order_index=deterministic_order_index,
        evidence_metadata=evidence_metadata,
        created_at=utc_now(),
    )
    session.add(reference)
    session.flush()
    return reference


def get_result(
    session: Session,
    *,
    retrieval_result_id: UUID,
) -> RetrievalResult | None:
    return session.get(RetrievalResult, retrieval_result_id)


def list_evidence_references(
    session: Session,
    *,
    retrieval_result_id: UUID,
) -> list[RetrievalEvidenceReference]:
    return (
        session.execute(
            select(RetrievalEvidenceReference)
            .where(RetrievalEvidenceReference.retrieval_result_id == retrieval_result_id)
            .order_by(RetrievalEvidenceReference.deterministic_order_index.asc())
        )
        .scalars()
        .all()
    )
