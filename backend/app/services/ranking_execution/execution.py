"""Controlled ranking execution (TASK-008D).

Mechanical permutation over completed retrieval evidence — persists via ranking_persistence only.
No workers, APIs, retrieval re-selection, answers, citations, or AI/semantic ranking.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.services.ranking_execution.models import RankingExecutionError, RankingExecutionOutcome
from app.services.ranking_execution.ordering import apply_ranking_profile
from app.services.ranking_execution.validation import (
    load_evidence_rows,
    validate_permutation,
    validate_pre_execution,
)
from app.services.ranking_persistence import (
    CURRENT_CONTRACT_VERSION,
    RankingPersistenceError,
    create_ranked_evidence_reference,
    create_ranking_request,
    create_ranking_result,
)


def execute_controlled_ranking(
    session: Session,
    *,
    retrieval_result_id: UUID,
    ranking_profile: str,
    contract_version: str = CURRENT_CONTRACT_VERSION,
    force_replay: bool = False,
    replay_nonce: str | None = None,
    requested_by_actor_type: str = "worker",
    requested_by_actor_identifier: str | None = None,
    notes: str | None = None,
) -> RankingExecutionOutcome:
    retrieval_result = validate_pre_execution(
        session,
        retrieval_result_id=retrieval_result_id,
        ranking_profile=ranking_profile,
        contract_version=contract_version,
        force_replay=force_replay,
        replay_nonce=replay_nonce,
    )

    try:
        ranking_request = create_ranking_request(
            session,
            retrieval_result_id=retrieval_result_id,
            ranking_profile=ranking_profile,
            contract_version=contract_version,
            requested_by_actor_type=requested_by_actor_type,
            requested_by_actor_identifier=requested_by_actor_identifier,
            force_replay=force_replay,
            notes=notes,
            replay_nonce=replay_nonce,
        )
    except RankingPersistenceError as exc:
        if "duplicate_default_request_for_hash" in str(exc):
            raise RankingExecutionError("duplicate_ranking", str(exc)) from exc
        raise RankingExecutionError("ranking_pipeline_unavailable", str(exc)) from exc

    accepted = create_ranking_result(
        session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=retrieval_result_id,
        ranking_status="accepted",
    )

    try:
        n = retrieval_result.result_count or 0
        if n == 0:
            completed = create_ranking_result(
                session,
                ranking_request_id=ranking_request.id,
                retrieval_result_id=retrieval_result_id,
                ranking_status="completed",
                rank_count=0,
                completed_at=utc_now(),
            )
            return RankingExecutionOutcome(
                ranking_request_id=ranking_request.id,
                ranking_result_id=completed.id,
                ranking_status="completed",
                rank_count=0,
            )

        input_rows = load_evidence_rows(session, retrieval_result_id=retrieval_result_id)
        ordered_rows = apply_ranking_profile(input_rows, ranking_profile=ranking_profile)
        assignments = validate_permutation(
            input_rows,
            ordered_rows,
            expected_count=n,
        )

        for evidence_id, presentation_order_index in assignments:
            create_ranked_evidence_reference(
                session,
                ranking_result_id=accepted.id,
                retrieval_result_id=retrieval_result_id,
                retrieval_evidence_reference_id=evidence_id,
                presentation_order_index=presentation_order_index,
            )

        completed = create_ranking_result(
            session,
            ranking_request_id=ranking_request.id,
            retrieval_result_id=retrieval_result_id,
            ranking_status="completed",
            rank_count=n,
            completed_at=utc_now(),
        )
        return RankingExecutionOutcome(
            ranking_request_id=ranking_request.id,
            ranking_result_id=completed.id,
            ranking_status="completed",
            rank_count=n,
        )
    except RankingExecutionError as exc:
        failed = create_ranking_result(
            session,
            ranking_request_id=ranking_request.id,
            retrieval_result_id=retrieval_result_id,
            ranking_status="failed",
            error_category=exc.category,
            error_message=exc.message,
            completed_at=utc_now(),
        )
        return RankingExecutionOutcome(
            ranking_request_id=ranking_request.id,
            ranking_result_id=failed.id,
            ranking_status="failed",
            rank_count=0,
            error_category=exc.category,
            error_message=exc.message,
        )
    except RankingPersistenceError as exc:
        failed = create_ranking_result(
            session,
            ranking_request_id=ranking_request.id,
            retrieval_result_id=retrieval_result_id,
            ranking_status="failed",
            error_category="ranking_pipeline_unavailable",
            error_message=str(exc),
            completed_at=utc_now(),
        )
        return RankingExecutionOutcome(
            ranking_request_id=ranking_request.id,
            ranking_result_id=failed.id,
            ranking_status="failed",
            rank_count=0,
            error_category="ranking_pipeline_unavailable",
            error_message=str(exc),
        )
    except Exception as exc:
        failed = create_ranking_result(
            session,
            ranking_request_id=ranking_request.id,
            retrieval_result_id=retrieval_result_id,
            ranking_status="failed",
            error_category="unknown_failure",
            error_message=str(exc),
            completed_at=utc_now(),
        )
        return RankingExecutionOutcome(
            ranking_request_id=ranking_request.id,
            ranking_result_id=failed.id,
            ranking_status="failed",
            rank_count=0,
            error_category="unknown_failure",
            error_message=str(exc),
        )
