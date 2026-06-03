from sqlalchemy.orm import Session

from app.models.legal_object_promotion_request import LegalObjectPromotionRequest
from app.models.parsed_structure import ParsedStructure
from app.services.legal_object_promotion.materialization import (
    materialize_legal_object_from_parsed_structure,
)
from app.workers.legal_object_promotion.result import LegalObjectPromotionProviderResult

CONTROLLED_LEGAL_OBJECT_PROMOTION_PROVIDER_NAME = "controlled_legal_object_promotion_provider"
CONTROLLED_LEGAL_OBJECT_PROMOTION_PROVIDER_VERSION = "0.1.0"


class ControlledLegalObjectPromotionProvider:
    """Materialize canonical legal memory from parsed_structure only.

    No network, AI, legal interpretation, citations, or answers.
    """

    def run_promotion(
        self,
        db: Session,
        parsed_structure: ParsedStructure,
        promotion_request: LegalObjectPromotionRequest,
    ) -> LegalObjectPromotionProviderResult:
        try:
            outcome = materialize_legal_object_from_parsed_structure(
                db,
                parsed_structure=parsed_structure,
                promotion_request=promotion_request,
            )
            return LegalObjectPromotionProviderResult(
                success=True,
                legal_object_id=outcome.legal_object_id,
                legal_object_version_id=outcome.legal_object_version_id,
                created_legal_object=outcome.created_legal_object,
                created_version=outcome.created_version,
                notes=(
                    "controlled promotion from parsed_structure; "
                    f"created_legal_object={outcome.created_legal_object}; "
                    f"created_version={outcome.created_version}"
                ),
                provider_name=CONTROLLED_LEGAL_OBJECT_PROMOTION_PROVIDER_NAME,
                provider_version=CONTROLLED_LEGAL_OBJECT_PROMOTION_PROVIDER_VERSION,
            )
        except ValueError as exc:
            category = str(exc)
            if category not in {
                "parsed_structure_missing",
                "parser_run_incomplete",
                "provenance_incomplete",
                "duplicate_promotion",
                "invalid_request",
                "promotion_pipeline_unavailable",
                "unknown_failure",
            }:
                category = "unknown_failure"
            return LegalObjectPromotionProviderResult(
                success=False,
                error_category=category,
                error_message=str(exc),
                provider_name=CONTROLLED_LEGAL_OBJECT_PROMOTION_PROVIDER_NAME,
                provider_version=CONTROLLED_LEGAL_OBJECT_PROMOTION_PROVIDER_VERSION,
            )
        except Exception as exc:
            return LegalObjectPromotionProviderResult(
                success=False,
                error_category="unknown_failure",
                error_message=str(exc),
                provider_name=CONTROLLED_LEGAL_OBJECT_PROMOTION_PROVIDER_NAME,
                provider_version=CONTROLLED_LEGAL_OBJECT_PROMOTION_PROVIDER_VERSION,
            )
