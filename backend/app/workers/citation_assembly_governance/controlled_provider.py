from sqlalchemy.orm import Session

from app.models.citation_assembly_governance_request import CitationAssemblyGovernanceRequest
from app.models.legal_object_version import LegalObjectVersion
from app.services.citation_execution import CitationRenderError, execute_controlled_citation
from app.workers.citation_assembly_governance.result import CitationAssemblyGovernanceProviderResult

CONTROLLED_CITATION_ASSEMBLY_PROVIDER_NAME = "controlled_citation_assembly_governance_provider"
CONTROLLED_CITATION_ASSEMBLY_PROVIDER_VERSION = "0.1.0"


class ControlledCitationAssemblyGovernanceProvider:
    """Deterministic citation rendering and entity persistence (TASK-006AD).

    Uses citation_execution service — not retrieval, ranking, answers, or legal inference.
    OD-021: single-worker mode; concurrent execution requires citation_hash-keyed locks (future).
    """

    def run_assembly(
        self,
        db: Session,
        request: CitationAssemblyGovernanceRequest,
        legal_object_version: LegalObjectVersion,
    ) -> CitationAssemblyGovernanceProviderResult:
        try:
            outcome = execute_controlled_citation(
                db,
                request=request,
                legal_object_version=legal_object_version,
            )
            return CitationAssemblyGovernanceProviderResult(
                success=True,
                citation_id=outcome.citation.citation_id,
                assembled_at=outcome.assembled_at,
                notes=(
                    "controlled citation execution; "
                    f"created={outcome.created}; "
                    f"citation_id={outcome.citation.citation_id}"
                ),
                provider_name=CONTROLLED_CITATION_ASSEMBLY_PROVIDER_NAME,
                provider_version=CONTROLLED_CITATION_ASSEMBLY_PROVIDER_VERSION,
            )
        except CitationRenderError as exc:
            category = exc.category
            if category not in {
                "legal_object_missing",
                "version_missing",
                "provenance_incomplete",
                "duplicate_citation",
                "invalid_request",
                "citation_pipeline_unavailable",
                "unknown_failure",
            }:
                category = "unknown_failure"
            return CitationAssemblyGovernanceProviderResult(
                success=False,
                error_category=category,
                error_message=exc.message,
                provider_name=CONTROLLED_CITATION_ASSEMBLY_PROVIDER_NAME,
                provider_version=CONTROLLED_CITATION_ASSEMBLY_PROVIDER_VERSION,
            )
        except Exception as exc:
            return CitationAssemblyGovernanceProviderResult(
                success=False,
                error_category="unknown_failure",
                error_message=str(exc),
                provider_name=CONTROLLED_CITATION_ASSEMBLY_PROVIDER_NAME,
                provider_version=CONTROLLED_CITATION_ASSEMBLY_PROVIDER_VERSION,
            )
