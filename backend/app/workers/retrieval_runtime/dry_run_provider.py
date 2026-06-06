from typing import Protocol

from sqlalchemy.orm import Session

from app.models.retrieval_request import RetrievalRequest
from app.workers.retrieval_runtime.result import RetrievalRuntimeProviderResult

DRY_RUN_RETRIEVAL_RUNTIME_PROVIDER_NAME = "dry_run_retrieval_runtime_provider"
DRY_RUN_RETRIEVAL_RUNTIME_PROVIDER_VERSION = "0.1.0"


class RetrievalRuntimeProvider(Protocol):
    def run_retrieval(
        self,
        db: Session,
        request: RetrievalRequest,
    ) -> RetrievalRuntimeProviderResult:
        """Return deterministic retrieval lifecycle outcome for one governance request."""


class DryRunRetrievalRuntimeProvider:
    """Synthetic provider for internal validation only.

    Must never select legal_object_versions, create evidence references, query citations,
    invoke retrieval execution, ranking, answers, or legal interpretation.
    """

    def run_retrieval(
        self,
        db: Session,
        request: RetrievalRequest,
    ) -> RetrievalRuntimeProviderResult:
        _ = db
        return RetrievalRuntimeProviderResult(
            success=True,
            notes=(
                f"dry-run synthetic retrieval lifecycle for request={request.id}; "
                "no evidence references; no retrieval execution"
            ),
            provider_name=DRY_RUN_RETRIEVAL_RUNTIME_PROVIDER_NAME,
            provider_version=DRY_RUN_RETRIEVAL_RUNTIME_PROVIDER_VERSION,
        )
