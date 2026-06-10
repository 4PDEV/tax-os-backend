from collections import Counter
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.legal_object_version import LegalObjectVersion
from app.models.retrieval_result import RetrievalResult
from app.services.ranking_execution.models import RankingEvidenceRow, RankingExecutionError
from app.services.ranking_persistence import (
    compute_ranking_request_hash,
    find_existing_default_request,
    list_results_for_request,
)
from app.services.ranking_persistence.validation import RANKING_PROFILES
from app.services.retrieval_persistence import get_result, list_evidence_references

TERMINAL_RANKING_STATUSES = frozenset(
    {"completed", "failed", "skipped", "duplicate_rejected"}
)


def validate_ranking_profile_or_raise(ranking_profile: str) -> None:
    if ranking_profile not in RANKING_PROFILES:
        raise RankingExecutionError("profile_not_allowed", f"invalid ranking_profile: {ranking_profile}")


def load_evidence_rows(
    session: Session,
    *,
    retrieval_result_id: UUID,
) -> list[RankingEvidenceRow]:
    evidence_rows = list_evidence_references(session, retrieval_result_id=retrieval_result_id)
    rows: list[RankingEvidenceRow] = []
    for evidence in evidence_rows:
        version = session.get(LegalObjectVersion, evidence.legal_object_version_id)
        if version is None:
            raise RankingExecutionError(
                "provenance_incomplete",
                f"legal_object_version missing: {evidence.legal_object_version_id}",
            )
        rows.append(
            RankingEvidenceRow(
                retrieval_evidence_reference_id=evidence.id,
                retrieval_result_id=evidence.retrieval_result_id,
                deterministic_order_index=evidence.deterministic_order_index,
                legal_object_id=evidence.legal_object_id,
                legal_object_version_id=evidence.legal_object_version_id,
                source_version_id=evidence.source_version_id,
                source_document_id=evidence.source_document_id,
                citation_hash=evidence.citation_hash,
                object_identifier=evidence.object_identifier,
                effective_from=version.effective_from,
            )
        )
    return rows


def validate_pre_execution(
    session: Session,
    *,
    retrieval_result_id: UUID,
    ranking_profile: str,
    contract_version: str,
    force_replay: bool,
    replay_nonce: str | None,
) -> RetrievalResult:
    """V-01 through V-08. Returns validated retrieval_result or raises RankingExecutionError."""
    validate_ranking_profile_or_raise(ranking_profile)

    retrieval_result = get_result(session, retrieval_result_id=retrieval_result_id)
    if retrieval_result is None:
        raise RankingExecutionError(
            "retrieval_result_missing",
            f"retrieval_result not found: {retrieval_result_id}",
        )

    if retrieval_result.retrieval_status != "completed":
        raise RankingExecutionError(
            "retrieval_result_not_completed",
            f"retrieval_status={retrieval_result.retrieval_status}",
        )

    if retrieval_result.result_count is None:
        raise RankingExecutionError(
            "retrieval_result_not_completed",
            "result_count is null",
        )

    evidence_count = len(
        list_evidence_references(session, retrieval_result_id=retrieval_result_id)
    )
    if evidence_count != retrieval_result.result_count:
        raise RankingExecutionError(
            "evidence_reference_missing",
            f"evidence_count={evidence_count} result_count={retrieval_result.result_count}",
        )

    if evidence_count > 0:
        load_evidence_rows(session, retrieval_result_id=retrieval_result_id)

    if not force_replay:
        ranking_request_hash = compute_ranking_request_hash(
            retrieval_result_id=retrieval_result_id,
            ranking_profile=ranking_profile,
            contract_version=contract_version,
            force_replay=False,
            replay_nonce=replay_nonce,
        )
        existing = find_existing_default_request(session, ranking_request_hash=ranking_request_hash)
        if existing is not None:
            results = list_results_for_request(session, ranking_request_id=existing.id)
            if results:
                latest = results[-1]
                if latest.ranking_status == "accepted":
                    raise RankingExecutionError(
                        "duplicate_ranking",
                        "in_flight_accepted_ranking_result",
                    )
            raise RankingExecutionError(
                "duplicate_ranking",
                "duplicate_default_request_for_hash",
            )

    return retrieval_result


def validate_permutation(
    input_rows: list[RankingEvidenceRow],
    ordered_rows: list[RankingEvidenceRow],
    *,
    expected_count: int,
) -> list[tuple[UUID, int]]:
    input_ids = [row.retrieval_evidence_reference_id for row in input_rows]
    output_ids = [row.retrieval_evidence_reference_id for row in ordered_rows]
    n = expected_count

    if len(output_ids) != n:
        raise RankingExecutionError("permutation_mismatch", "P-01 output length mismatch")
    if len(output_ids) != len(input_ids):
        raise RankingExecutionError("permutation_mismatch", "P-02 length mismatch")
    if Counter(output_ids) != Counter(input_ids):
        raise RankingExecutionError("permutation_mismatch", "P-03 multiset mismatch")
    if set(output_ids) != set(input_ids):
        raise RankingExecutionError("permutation_mismatch", "P-04 set mismatch")

    input_counter = Counter(input_ids)
    output_counter = Counter(output_ids)
    for evidence_id, count in input_counter.items():
        if output_counter[evidence_id] < count:
            raise RankingExecutionError("permutation_mismatch", "P-06 missing evidence")
    for evidence_id, count in output_counter.items():
        if input_counter[evidence_id] < count:
            raise RankingExecutionError("permutation_mismatch", "P-05 unexpected evidence")

    assignments: list[tuple[UUID, int]] = []
    seen_indices: set[int] = set()
    for index, row in enumerate(ordered_rows, start=1):
        if index in seen_indices:
            raise RankingExecutionError("permutation_mismatch", "P-08 duplicate slot")
        seen_indices.add(index)
        assignments.append((row.retrieval_evidence_reference_id, index))

    if n > 0 and seen_indices != set(range(1, n + 1)):
        raise RankingExecutionError("permutation_mismatch", "P-07 non-contiguous indices")

    for evidence_id, output_count in output_counter.items():
        if output_count > 1 and input_counter[evidence_id] < 2:
            raise RankingExecutionError("permutation_mismatch", "P-09 duplicate evidence rank")

    return assignments
