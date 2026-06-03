from typing import Protocol

from sqlalchemy.orm import Session

from app.models.citation_assembly_governance_request import CitationAssemblyGovernanceRequest
from app.models.legal_object_version import LegalObjectVersion
from app.workers.citation_assembly_governance.result import CitationAssemblyGovernanceProviderResult

DRY_RUN_CITATION_ASSEMBLY_PROVIDER_NAME = "dry_run_citation_assembly_governance_provider"
DRY_RUN_CITATION_ASSEMBLY_PROVIDER_VERSION = "0.1.0"


class CitationAssemblyGovernanceProvider(Protocol):
    """Governance assembly provider protocol (spec alias: ``CitationAssemblyProvider``)."""
    def run_assembly(
        self,
        db: Session,
        request: CitationAssemblyGovernanceRequest,
        legal_object_version: LegalObjectVersion,
    ) -> CitationAssemblyGovernanceProviderResult:
        """Return deterministic assembly lifecycle outcome for one governance request."""


# Spec alias — distinct from TASK-004D ``CitationAssemblyRequest``.
CitationAssemblyProvider = CitationAssemblyGovernanceProvider


class DryRunCitationAssemblyGovernanceProvider:
    """Synthetic provider for internal validation only.

    Must never invoke TASK-004D CitationAssembler, create citation text, citation_id,
    retrieval results, answers, or legal interpretation.
    """

    def run_assembly(
        self,
        db: Session,
        request: CitationAssemblyGovernanceRequest,
        legal_object_version: LegalObjectVersion,
    ) -> CitationAssemblyGovernanceProviderResult:
        _ = db, legal_object_version
        return CitationAssemblyGovernanceProviderResult(
            success=True,
            notes=(
                f"dry-run synthetic citation assembly lifecycle for request={request.id}; "
                "no citation_id assigned; no citation rendering"
            ),
            provider_name=DRY_RUN_CITATION_ASSEMBLY_PROVIDER_NAME,
            provider_version=DRY_RUN_CITATION_ASSEMBLY_PROVIDER_VERSION,
        )
