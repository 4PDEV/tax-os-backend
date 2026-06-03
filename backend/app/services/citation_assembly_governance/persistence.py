"""Append-only citation assembly governance persistence (TASK-006Z).

Persistence records assembly intent and lifecycle only — no citation rendering,
no TASK-004D assembler calls, no retrieval runtime, no answer assembly.

OD-021: single-worker assumption; concurrent workers need execution-time locks (future task).
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.citation_assembly_governance_request import CitationAssemblyGovernanceRequest
from app.models.citation_assembly_governance_result import CitationAssemblyGovernanceResult
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.models.source_version import SourceVersion
from app.services.citation_assembly_governance.hashing import compute_request_hash
from app.services.citation_assembly_governance.validation import (
    validate_actor_type,
    validate_citation_error_category,
    validate_citation_status,
    validate_legal_memory_lineage,
)


class CitationAssemblyGovernancePersistenceError(Exception):
    pass


def find_existing_default_request_for_version(
    session: Session,
    *,
    legal_object_version_id: UUID,
) -> CitationAssemblyGovernanceRequest | None:
    return session.execute(
        select(CitationAssemblyGovernanceRequest)
        .where(
            CitationAssemblyGovernanceRequest.legal_object_version_id == legal_object_version_id,
            CitationAssemblyGovernanceRequest.force_reassembly.is_(False),
        )
        .order_by(CitationAssemblyGovernanceRequest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def create_citation_assembly_request(
    session: Session,
    *,
    legal_object_id: str,
    legal_object_version_id: UUID,
    source_version_id: UUID,
    requested_by_actor_type: str,
    citation_reason: str,
    requested_by_actor_identifier: str | None = None,
    requested_at: datetime | None = None,
    force_reassembly: bool = False,
    notes: str | None = None,
) -> CitationAssemblyGovernanceRequest:
    validate_actor_type(requested_by_actor_type)
    if not citation_reason or not citation_reason.strip():
        raise CitationAssemblyGovernancePersistenceError("invalid_request")

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
        raise CitationAssemblyGovernancePersistenceError(str(exc)) from exc

    if not force_reassembly:
        existing_default = find_existing_default_request_for_version(
            session, legal_object_version_id=legal_object_version_id
        )
        if existing_default is not None:
            raise CitationAssemblyGovernancePersistenceError(
                "duplicate_default_request_for_version"
            )

    request_hash = compute_request_hash(
        legal_object_version_id=legal_object_version_id,
        force_reassembly=force_reassembly,
    )

    request = CitationAssemblyGovernanceRequest(
        legal_object_id=legal_object_id,
        legal_object_version_id=legal_object_version_id,
        source_version_id=source_version_id,
        citation_reason=citation_reason.strip(),
        requested_by_actor_type=requested_by_actor_type,
        requested_by_actor_identifier=requested_by_actor_identifier,
        requested_at=requested_at or utc_now(),
        force_reassembly=force_reassembly,
        request_hash=request_hash,
        notes=notes,
        created_at=utc_now(),
    )
    session.add(request)
    session.flush()
    return request


def persist_citation_assembly_result(
    session: Session,
    *,
    citation_assembly_governance_request_id: UUID,
    citation_status: str,
    citation_id: str | None = None,
    assembled_at: datetime | None = None,
    error_category: str | None = None,
    error_message: str | None = None,
    notes: str | None = None,
) -> CitationAssemblyGovernanceResult:
    validate_citation_status(citation_status)
    validate_citation_error_category(error_category)

    request = session.get(
        CitationAssemblyGovernanceRequest, citation_assembly_governance_request_id
    )
    if request is None:
        raise CitationAssemblyGovernancePersistenceError(
            f"citation_assembly_governance_request not found: "
            f"{citation_assembly_governance_request_id}"
        )

    if citation_id is not None:
        legal_object = session.get(LegalObject, request.legal_object_id)
        if legal_object is None:
            raise CitationAssemblyGovernancePersistenceError("legal_object_missing")

    result = CitationAssemblyGovernanceResult(
        citation_assembly_governance_request_id=citation_assembly_governance_request_id,
        legal_object_id=request.legal_object_id,
        legal_object_version_id=request.legal_object_version_id,
        citation_status=citation_status,
        citation_id=citation_id,
        assembled_at=assembled_at,
        error_category=error_category,
        error_message=error_message,
        notes=notes,
        created_at=utc_now(),
    )
    session.add(result)
    session.flush()
    return result


def get_citation_assembly_request(
    session: Session,
    *,
    citation_assembly_governance_request_id: UUID,
) -> CitationAssemblyGovernanceRequest | None:
    return session.get(
        CitationAssemblyGovernanceRequest, citation_assembly_governance_request_id
    )


def list_results_for_request(
    session: Session,
    *,
    citation_assembly_governance_request_id: UUID,
) -> list[CitationAssemblyGovernanceResult]:
    return (
        session.execute(
            select(CitationAssemblyGovernanceResult)
            .where(
                CitationAssemblyGovernanceResult.citation_assembly_governance_request_id
                == citation_assembly_governance_request_id
            )
            .order_by(CitationAssemblyGovernanceResult.created_at.asc())
        )
        .scalars()
        .all()
    )


def get_latest_result_for_request(
    session: Session,
    *,
    citation_assembly_governance_request_id: UUID,
) -> CitationAssemblyGovernanceResult | None:
    return session.execute(
        select(CitationAssemblyGovernanceResult)
        .where(
            CitationAssemblyGovernanceResult.citation_assembly_governance_request_id
            == citation_assembly_governance_request_id
        )
        .order_by(CitationAssemblyGovernanceResult.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
