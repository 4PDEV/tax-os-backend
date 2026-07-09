"""Deterministic response package rendering (TASK-010A)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.answer_evidence_entry import AnswerEvidenceEntry
from app.models.answer_result import AnswerResult
from app.models.answer_uncertainty_flag import AnswerUncertaintyFlag
from app.models.citation import Citation
from app.models.legal_object_version import LegalObjectVersion
from app.models.retrieval_evidence_reference import RetrievalEvidenceReference
from app.models.source_document import SourceDocument
from app.models.source_version import SourceVersion
from app.services.citation.authority import resolve_authority_type
from app.services.citation.formatter import CitationFormatter
from app.services.response_runtime.models import (
    CURRENT_CONTRACT_VERSION,
    RENDERING_MODE_DETERMINISTIC,
    ResponseCitationReference,
    ResponseEvidenceEntry,
    ResponseMetadata,
    ResponsePackage,
    ResponseRequest,
    ResponseRuntimeError,
    ResponseUncertaintyFlag,
)


def _render_citation_text_read_only(session: Session, citation: Citation) -> str:
    source_version = session.get(SourceVersion, citation.source_version_id)
    if source_version is None:
        return citation.rendered_citation_text

    source_document = session.get(SourceDocument, source_version.source_document_id)
    version = session.get(LegalObjectVersion, citation.legal_object_version_id)
    source_title = source_document.title if source_document else citation.citation_id
    authority_type = resolve_authority_type(
        source_type=getattr(source_document, "source_type", "law") if source_document else "law",
        authority_level=getattr(source_document, "authority_level", "national")
        if source_document
        else "national",
    )
    formatter = CitationFormatter()
    return formatter.format(
        source_title=source_title,
        location_reference=citation.location_reference,
        authority_type=authority_type,
        version_label=source_version.version_label if source_version else None,
        effective_from=version.effective_from if version else None,
        source_version_effective_from=source_version.effective_from if source_version else None,
        source_version_effective_to=source_version.effective_to if source_version else None,
    )


def _build_citation_reference(
    session: Session,
    *,
    citation_id: str | None,
    citation_hash: str | None,
    include_rendered_citation_text: bool,
) -> ResponseCitationReference | None:
    if not citation_id and not citation_hash:
        return None

    citation_row = None
    if citation_id:
        citation_row = session.execute(
            select(Citation).where(Citation.citation_id == citation_id)
        ).scalar_one_or_none()

    rendered = None
    if include_rendered_citation_text and citation_row is not None:
        try:
            rendered = _render_citation_text_read_only(session, citation_row)
        except Exception as exc:
            raise ResponseRuntimeError(
                f"citation_format_failed: {exc}",
                error_category="citation_format_failed",
            ) from exc

    return ResponseCitationReference(
        citation_id=citation_id,
        citation_hash=citation_hash,
        rendered_citation_text=rendered,
    )


def _provenance_from_retrieval_row(
    retrieval_row: RetrievalEvidenceReference | None,
) -> tuple[str | None, UUID | None, str | None, str | None, str | None, str | None]:
    if retrieval_row is None:
        return None, None, None, None, None, None

    return (
        retrieval_row.legal_object_id,
        retrieval_row.source_version_id,
        retrieval_row.object_identifier,
        retrieval_row.location_reference,
        retrieval_row.citation_id,
        retrieval_row.citation_hash,
    )


def _map_evidence_entry(
    session: Session,
    *,
    entry: AnswerEvidenceEntry,
    include_rendered_citation_text: bool,
) -> ResponseEvidenceEntry:
    retrieval_row = session.get(RetrievalEvidenceReference, entry.retrieval_evidence_reference_id)
    legal_object_id, source_version_id, object_identifier, location_reference, citation_id, citation_hash = (
        _provenance_from_retrieval_row(retrieval_row)
    )

    citation_reference = _build_citation_reference(
        session,
        citation_id=citation_id,
        citation_hash=citation_hash,
        include_rendered_citation_text=include_rendered_citation_text,
    )

    return ResponseEvidenceEntry(
        presentation_order_index=entry.presentation_order_index,
        retrieval_evidence_reference_id=entry.retrieval_evidence_reference_id,
        ranked_evidence_reference_id=entry.ranked_evidence_reference_id,
        legal_object_id=legal_object_id,
        source_version_id=source_version_id,
        object_identifier=object_identifier,
        location_reference=location_reference,
        citation_reference=citation_reference,
        entry_metadata=None,
    )


def _map_uncertainty_flag(flag: AnswerUncertaintyFlag) -> ResponseUncertaintyFlag:
    related_evidence_ids: list[UUID] = []
    if flag.related_retrieval_evidence_reference_id is not None:
        related_evidence_ids = [flag.related_retrieval_evidence_reference_id]
    return ResponseUncertaintyFlag(
        flag_type=flag.flag_type,
        severity=flag.severity,
        message=flag.message,
        related_evidence_ids=related_evidence_ids,
    )


def render_response_package(
    session: Session,
    *,
    request: ResponseRequest,
    terminal: AnswerResult,
    accepted: AnswerResult,
    evidence_rows: list[AnswerEvidenceEntry],
    uncertainty_rows: list[AnswerUncertaintyFlag],
) -> ResponsePackage:
    rank_count = terminal.rank_count if terminal.rank_count is not None else 0
    if rank_count > 0 and len(evidence_rows) != rank_count:
        raise ResponseRuntimeError(
            "evidence_count_mismatch",
            error_category="evidence_count_mismatch",
        )
    if rank_count == 0 and len(evidence_rows) != 0:
        raise ResponseRuntimeError(
            "evidence_count_mismatch",
            error_category="evidence_count_mismatch",
        )

    evidence_entries = [
        _map_evidence_entry(
            session,
            entry=entry,
            include_rendered_citation_text=request.include_rendered_citation_text,
        )
        for entry in evidence_rows
    ]

    return ResponsePackage(
        contract_version=CURRENT_CONTRACT_VERSION,
        answer_request_id=request.answer_request_id,
        answer_result_id=terminal.id,
        rank_count=rank_count,
        evidence_entries=evidence_entries,
        uncertainty_flags=[_map_uncertainty_flag(flag) for flag in uncertainty_rows],
        response_metadata=ResponseMetadata(
            rendering_mode=RENDERING_MODE_DETERMINISTIC,
            include_rendered_citation_text=request.include_rendered_citation_text,
            notes=None,
        ),
    )
