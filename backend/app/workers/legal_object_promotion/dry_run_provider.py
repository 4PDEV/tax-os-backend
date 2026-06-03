from typing import Protocol

from app.models.legal_object_promotion_request import LegalObjectPromotionRequest
from app.models.parsed_structure import ParsedStructure
from app.workers.legal_object_promotion.result import LegalObjectPromotionProviderResult

DRY_RUN_PROMOTION_PROVIDER_NAME = "dry_run_legal_object_promotion_provider"
DRY_RUN_PROMOTION_PROVIDER_VERSION = "0.1.0"


class LegalObjectPromotionProvider(Protocol):
    def run_promotion(
        self,
        parsed_structure: ParsedStructure,
        promotion_request: LegalObjectPromotionRequest,
    ) -> LegalObjectPromotionProviderResult:
        """Return deterministic promotion lifecycle outcome for one request."""


class DryRunLegalObjectPromotionProvider:
    """Synthetic provider for internal validation only.

    Must never create legal objects, versions, citations, answers, or legal interpretation.
    """

    def run_promotion(
        self,
        parsed_structure: ParsedStructure,
        promotion_request: LegalObjectPromotionRequest,
    ) -> LegalObjectPromotionProviderResult:
        _ = parsed_structure
        return LegalObjectPromotionProviderResult(
            success=True,
            notes=(
                f"dry-run synthetic promotion lifecycle for request={promotion_request.id}; "
                "no legal_object_id assigned"
            ),
            provider_name=DRY_RUN_PROMOTION_PROVIDER_NAME,
            provider_version=DRY_RUN_PROMOTION_PROVIDER_VERSION,
        )
