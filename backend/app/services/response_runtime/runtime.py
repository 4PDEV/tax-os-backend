"""Response runtime orchestration (TASK-010A)."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.answer_result import AnswerResult
from app.services.answer_persistence import (
    get_answer_request,
    get_answer_result,
    list_evidence_entries_for_result,
    list_results_for_request,
    list_uncertainty_flags_for_result,
)
from app.services.response_runtime.models import (
    RESPONSE_STATUS_COMPLETED,
    RESPONSE_STATUS_FAILED,
    SUPPORTED_CONTRACT_VERSIONS,
    ResponseOutcome,
    ResponseRequest,
    ResponseRuntimeError,
)
from app.services.response_runtime.rendering import render_response_package

_NON_DELIVERABLE_STATUSES = frozenset({"failed", "duplicate_rejected", "skipped"})


class ResponseRuntime:
    """Read-only delivery orchestration — renders completed answer persistence only."""

    def validate_request(self, request: ResponseRequest) -> None:
        if not isinstance(request.answer_request_id, UUID):
            raise ResponseRuntimeError(
                "invalid_response_request: invalid answer_request_id",
                error_category="invalid_response_request",
            )
        if not request.contract_version:
            raise ResponseRuntimeError(
                "invalid_response_request: contract_version is required",
                error_category="invalid_response_request",
            )
        if request.contract_version not in SUPPORTED_CONTRACT_VERSIONS:
            raise ResponseRuntimeError(
                "contract_version_unsupported",
                error_category="contract_version_unsupported",
            )

    def _resolve_terminal(self, db: Session, request: ResponseRequest) -> AnswerResult:
        if request.answer_result_id is not None:
            terminal = get_answer_result(db, answer_result_id=request.answer_result_id)
            if terminal is None:
                raise ResponseRuntimeError(
                    "answer_result_not_found",
                    error_category="answer_result_not_found",
                )
            if terminal.answer_request_id != request.answer_request_id:
                raise ResponseRuntimeError(
                    "answer_result_not_found",
                    error_category="answer_result_not_found",
                )
            return terminal

        results = list_results_for_request(db, answer_request_id=request.answer_request_id)
        completed_rows = [row for row in results if row.answer_status == "completed"]
        if not completed_rows:
            raise ResponseRuntimeError(
                "answer_not_completed",
                error_category="answer_not_completed",
            )
        return max(completed_rows, key=lambda row: row.created_at)

    def _resolve_accepted(self, db: Session, *, answer_request_id: UUID) -> AnswerResult:
        results = list_results_for_request(db, answer_request_id=answer_request_id)
        accepted_rows = [row for row in results if row.answer_status == "accepted"]
        if len(accepted_rows) != 1:
            raise ResponseRuntimeError(
                "accepted_result_missing",
                error_category="accepted_result_missing",
            )
        return accepted_rows[0]

    def run(self, db: Session, request: ResponseRequest) -> ResponseOutcome:
        self.validate_request(request)

        if get_answer_request(db, answer_request_id=request.answer_request_id) is None:
            raise ResponseRuntimeError(
                "answer_request_not_found",
                error_category="answer_request_not_found",
            )

        terminal = self._resolve_terminal(db, request)
        if terminal.answer_status in _NON_DELIVERABLE_STATUSES:
            return ResponseOutcome(
                response_status=RESPONSE_STATUS_FAILED,
                response_package=None,
                error_category="answer_not_deliverable",
                error_message=f"terminal answer_status={terminal.answer_status}",
            )
        if terminal.answer_status != "completed":
            raise ResponseRuntimeError(
                "answer_not_completed",
                error_category="answer_not_completed",
            )

        accepted = self._resolve_accepted(db, answer_request_id=request.answer_request_id)
        evidence_rows = list_evidence_entries_for_result(db, answer_result_id=accepted.id)
        uncertainty_rows = list_uncertainty_flags_for_result(db, answer_result_id=accepted.id)

        package = render_response_package(
            db,
            request=request,
            terminal=terminal,
            accepted=accepted,
            evidence_rows=evidence_rows,
            uncertainty_rows=uncertainty_rows,
        )
        return ResponseOutcome(
            response_status=RESPONSE_STATUS_COMPLETED,
            response_package=package,
            error_category=None,
            error_message=None,
        )


def build_response(db: Session, request: ResponseRequest) -> ResponseOutcome:
    """Single delivery entrypoint for response runtime."""
    runtime = ResponseRuntime()
    return runtime.run(db, request)
