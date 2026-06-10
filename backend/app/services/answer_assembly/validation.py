"""Answer assembly validation and RL-O-01 ranking resolution (TASK-009A)."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.ranking_request import RankingRequest
from app.models.retrieval_evidence_reference import RetrievalEvidenceReference
from app.services.answer_assembly.models import AnswerAssemblyError, RankingAssemblyInputs
from app.services.ranking_persistence import list_ranked_evidence_references, list_results_for_request


def resolve_ranking_assembly_inputs(
    session: Session,
    *,
    ranking_request_id: UUID,
) -> RankingAssemblyInputs:
    """RL-O-01: terminal completed + accepted ranking_result + ranked rows on accepted."""
    ranking_request = session.get(RankingRequest, ranking_request_id)
    if ranking_request is None:
        raise AnswerAssemblyError(
            "ranking_result_not_completed",
            f"ranking_request not found: {ranking_request_id}",
        )

    results = list_results_for_request(session, ranking_request_id=ranking_request_id)
    terminal_results = [r for r in results if r.ranking_status == "completed"]
    accepted_results = [r for r in results if r.ranking_status == "accepted"]

    if len(terminal_results) != 1:
        raise AnswerAssemblyError(
            "ranking_result_not_completed",
            f"expected exactly one completed ranking_result, found {len(terminal_results)}",
        )
    terminal = terminal_results[0]

    if len(accepted_results) != 1:
        raise AnswerAssemblyError(
            "accepted_ranking_result_missing",
            f"expected exactly one accepted ranking_result, found {len(accepted_results)}",
        )
    accepted = accepted_results[0]

    ranked_rows = list_ranked_evidence_references(
        session,
        ranking_result_id=accepted.id,
    )
    ranked_rows = sorted(ranked_rows, key=lambda row: row.presentation_order_index)

    rank_count = terminal.rank_count or 0
    if rank_count > 0 and not ranked_rows:
        raise AnswerAssemblyError(
            "ranked_evidence_missing",
            f"rank_count={rank_count} but no ranked rows on accepted result",
        )
    if len(ranked_rows) != rank_count:
        raise AnswerAssemblyError(
            "evidence_count_mismatch",
            f"ranked_rows={len(ranked_rows)} terminal.rank_count={rank_count}",
        )

    expected_retrieval_result_id = ranking_request.retrieval_result_id
    for row in ranked_rows:
        if row.retrieval_result_id != expected_retrieval_result_id:
            raise AnswerAssemblyError(
                "retrieval_result_mismatch",
                f"ranked row retrieval_result_id={row.retrieval_result_id} "
                f"expected={expected_retrieval_result_id}",
            )

    return RankingAssemblyInputs(
        ranking_request=ranking_request,
        terminal_ranking_result=terminal,
        accepted_ranking_result=accepted,
        ranked_rows=tuple(ranked_rows),
    )


def validate_evidence_entries(
    ranked_rows: tuple,
    evidence_entries: list,
) -> None:
    """E-01–E-07: ranked multiset matches answer entries in order."""
    if len(evidence_entries) != len(ranked_rows):
        raise AnswerAssemblyError(
            "assembly_validation_failed",
            "evidence entry count does not match ranked row count",
        )

    for index, (ranked_row, entry) in enumerate(zip(ranked_rows, evidence_entries, strict=True), start=1):
        if entry.presentation_order_index != ranked_row.presentation_order_index:
            raise AnswerAssemblyError(
                "assembly_validation_failed",
                f"presentation_order_index mismatch at position {index}",
            )
        if entry.ranked_evidence_reference_id != ranked_row.id:
            raise AnswerAssemblyError(
                "assembly_validation_failed",
                f"ranked_evidence_reference_id mismatch at position {index}",
            )
        if entry.retrieval_evidence_reference_id != ranked_row.retrieval_evidence_reference_id:
            raise AnswerAssemblyError(
                "assembly_validation_failed",
                f"retrieval_evidence_reference_id mismatch at position {index}",
            )


def load_retrieval_evidence_or_raise(
    session: Session,
    *,
    evidence_id: UUID,
) -> RetrievalEvidenceReference:
    evidence = session.get(RetrievalEvidenceReference, evidence_id)
    if evidence is None:
        raise AnswerAssemblyError(
            "provenance_chain_incomplete",
            f"retrieval_evidence_reference not found: {evidence_id}",
        )
    return evidence

