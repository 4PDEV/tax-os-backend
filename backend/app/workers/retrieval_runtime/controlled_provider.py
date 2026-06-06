from uuid import UUID

from sqlalchemy.orm import Session

from app.models.retrieval_request import RetrievalRequest
from app.services.retrieval_execution import RetrievalExecutionError, execute_controlled_retrieval
from app.workers.retrieval_runtime.result import RetrievalRuntimeProviderResult

CONTROLLED_RETRIEVAL_RUNTIME_PROVIDER_NAME = "controlled_retrieval_runtime_provider"
CONTROLLED_RETRIEVAL_RUNTIME_PROVIDER_VERSION = "0.1.0"


class ControlledRetrievalRuntimeProvider:
    """Controlled retrieval execution (TASK-007E).

    Selects evidence and persists retrieval_evidence_references — not ranking,
    answers, citation assembly, or AI retrieval.
    OD-021: single-worker mode; concurrent execution requires request_hash-keyed locks (future).
    """

    def run_retrieval(
        self,
        db: Session,
        request: RetrievalRequest,
        *,
        retrieval_result_id: UUID | None = None,
    ) -> RetrievalRuntimeProviderResult:
        if retrieval_result_id is None:
            return RetrievalRuntimeProviderResult(
                success=False,
                error_category="invalid_request",
                error_message="retrieval_result_id is required for controlled execution",
                provider_name=CONTROLLED_RETRIEVAL_RUNTIME_PROVIDER_NAME,
                provider_version=CONTROLLED_RETRIEVAL_RUNTIME_PROVIDER_VERSION,
            )
        try:
            outcome = execute_controlled_retrieval(
                db,
                request=request,
                retrieval_result_id=retrieval_result_id,
            )
            return RetrievalRuntimeProviderResult(
                success=True,
                result_count=outcome.evidence_count,
                notes=outcome.notes,
                provider_name=CONTROLLED_RETRIEVAL_RUNTIME_PROVIDER_NAME,
                provider_version=CONTROLLED_RETRIEVAL_RUNTIME_PROVIDER_VERSION,
            )
        except RetrievalExecutionError as exc:
            category = exc.category
            if category not in {
                "invalid_request",
                "temporal_scope_missing",
                "version_missing",
                "citation_missing",
                "provenance_incomplete",
                "duplicate_retrieval",
                "retrieval_pipeline_unavailable",
                "unknown_failure",
            }:
                category = "unknown_failure"
            return RetrievalRuntimeProviderResult(
                success=False,
                error_category=category,
                error_message=exc.message,
                provider_name=CONTROLLED_RETRIEVAL_RUNTIME_PROVIDER_NAME,
                provider_version=CONTROLLED_RETRIEVAL_RUNTIME_PROVIDER_VERSION,
            )
        except Exception as exc:
            return RetrievalRuntimeProviderResult(
                success=False,
                error_category="unknown_failure",
                error_message=str(exc),
                provider_name=CONTROLLED_RETRIEVAL_RUNTIME_PROVIDER_NAME,
                provider_version=CONTROLLED_RETRIEVAL_RUNTIME_PROVIDER_VERSION,
            )
