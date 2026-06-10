"""Ephemeral answer package assembly (TASK-009A).

Read-only provenance joins — no persistence, no ranking, no retrieval execution.
"""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.citation import Citation
from app.models.legal_object_version import LegalObjectVersion
from app.models.source_document import SourceDocument
from app.models.source_version import SourceVersion
from app.services.answer_assembly.models import (
    CURRENT_CONTRACT_VERSION,
    AnswerAssemblyError,
    AnswerAssemblyMetadata,
    AnswerAssemblyOutcome,
    AnswerEvidenceEntry,
    AnswerPackage,
    CitationReference,
    UncertaintyFlag,
)
from app.services.answer_assembly.validation import (
    load_retrieval_evidence_or_raise,
    resolve_ranking_assembly_inputs,
    validate_evidence_entries,
)
from app.services.citation.authority import resolve_authority_type
from app.services.citation.formatter import CitationFormatter


def _citation_reference_status(
    *,
    citation_id: str | None,
    citation_row: Citation | None,
) -> str:
    if not citation_id:
        return "absent"
    if citation_row is None:
        return "incomplete"
    return "present"


def _render_citation_text_read_only(
    session: Session,
    citation: Citation,
) -> str:
    """Read-only citation display via CitationFormatter over persisted citation pins."""
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
) -> tuple[CitationReference, str]:
    citation_row = None
    if citation_id:
        citation_row = session.execute(
            select(Citation).where(Citation.citation_id == citation_id)
        ).scalar_one_or_none()

    status = _citation_reference_status(citation_id=citation_id, citation_row=citation_row)
    rendered = None
    if include_rendered_citation_text and citation_row is not None:
        rendered = _render_citation_text_read_only(session, citation_row)

    return (
        CitationReference(
            citation_id=citation_id,
            citation_hash=citation_hash,
            rendered_citation_text=rendered,
        ),
        status,
    )


def assemble_answer_package(
    session: Session,
    *,
    ranking_request_id: UUID,
    contract_version: str = CURRENT_CONTRACT_VERSION,
    include_rendered_citation_text: bool = False,
) -> AnswerAssemblyOutcome:
    try:
        inputs = resolve_ranking_assembly_inputs(
            session,
            ranking_request_id=ranking_request_id,
        )
        ranking_request = inputs.ranking_request
        terminal = inputs.terminal_ranking_result
        accepted = inputs.accepted_ranking_result
        ranked_rows = inputs.ranked_rows
        rank_count = terminal.rank_count or 0

        uncertainty_flags: list[UncertaintyFlag] = []
        evidence_entries: list[AnswerEvidenceEntry] = []

        if rank_count == 0:
            uncertainty_flags.append(
                UncertaintyFlag(
                    flag_type="zero_evidence",
                    severity="informational",
                    message="Ranking completed with zero evidence references.",
                    related_evidence_ids=(),
                )
            )
        else:
            for ranked_row in ranked_rows:
                evidence = load_retrieval_evidence_or_raise(
                    session,
                    evidence_id=ranked_row.retrieval_evidence_reference_id,
                )
                if evidence.retrieval_result_id != ranking_request.retrieval_result_id:
                    raise AnswerAssemblyError(
                        "retrieval_result_mismatch",
                        f"evidence retrieval_result_id={evidence.retrieval_result_id}",
                    )

                version = session.get(LegalObjectVersion, evidence.legal_object_version_id)
                if version is None:
                    raise AnswerAssemblyError(
                        "provenance_chain_incomplete",
                        f"legal_object_version missing: {evidence.legal_object_version_id}",
                    )

                citation_ref, citation_status = _build_citation_reference(
                    session,
                    citation_id=evidence.citation_id,
                    citation_hash=evidence.citation_hash,
                    include_rendered_citation_text=include_rendered_citation_text,
                )
                if citation_status == "incomplete":
                    uncertainty_flags.append(
                        UncertaintyFlag(
                            flag_type="incomplete_provenance",
                            severity="warning",
                            message=f"citation_id pin present but citation row missing: {evidence.citation_id}",
                            related_evidence_ids=(evidence.id,),
                        )
                    )

                evidence_entries.append(
                    AnswerEvidenceEntry(
                        presentation_order_index=ranked_row.presentation_order_index,
                        ranked_evidence_reference_id=ranked_row.id,
                        retrieval_evidence_reference_id=evidence.id,
                        retrieval_result_id=evidence.retrieval_result_id,
                        legal_object_id=evidence.legal_object_id,
                        legal_object_version_id=evidence.legal_object_version_id,
                        source_version_id=evidence.source_version_id,
                        citation_reference=citation_ref,
                        object_identifier=evidence.object_identifier,
                        location_reference=evidence.location_reference,
                        citation_reference_status=citation_status,
                        entry_metadata=None,
                    )
                )

            validate_evidence_entries(ranked_rows, evidence_entries)

        package = AnswerPackage(
            answer_package_id=uuid4(),
            contract_version=contract_version,
            ranking_request_id=ranking_request_id,
            retrieval_result_id=ranking_request.retrieval_result_id,
            terminal_ranking_result_id=terminal.id,
            accepted_ranking_result_id=accepted.id,
            ranking_profile=ranking_request.ranking_profile,
            rank_count=rank_count,
            answer_status="completed",
            assembled_at=utc_now(),
            evidence_entries=tuple(evidence_entries),
            uncertainty_flags=tuple(uncertainty_flags),
            assembly_metadata=AnswerAssemblyMetadata(assembly_mode="deterministic"),
        )
        return AnswerAssemblyOutcome(answer_status="completed", answer_package=package)
    except AnswerAssemblyError as exc:
        return AnswerAssemblyOutcome(
            answer_status="failed",
            answer_package=None,
            error_category=exc.category,
            error_message=exc.message,
        )
    except Exception as exc:
        return AnswerAssemblyOutcome(
            answer_status="failed",
            answer_package=None,
            error_category="unknown_failure",
            error_message=str(exc),
        )
