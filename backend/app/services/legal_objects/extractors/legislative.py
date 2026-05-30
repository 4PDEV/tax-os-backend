from app.services.legal_objects.models import LegalObjectExtractionResult
from app.services.legal_objects.extractors.base import BaseLegalObjectExtractor
from app.services.segmentation.models import SegmentationResult


class LegislativeLegalObjectExtractor(BaseLegalObjectExtractor):
    """Skeleton legislative legal object extractor.

    Intentionally unimplemented. A future, dedicated task will provide
    deterministic legislative-aware legal object extraction (e.g. resolving
    Act / Regulation / Order / Notice / Judgment / Treaty container objects and
    their internal Part / Chapter / Section / Article hierarchy from
    legislative drafting conventions). That work is out of scope here and must
    remain:

    - deterministic and reproducible
    - source-faithful (exact offsets, no rewriting)
    - non-interpretive (no legal meaning, topic classification, authority
      ranking, or legal-effect determination)

    When implemented, ``extract`` must build on the same contract
    (:class:`LegalObjectExtractionResult`) and bump ``version`` accordingly.
    """

    name = "legislative"
    version = "0.0.0"

    def can_handle(self, *, segmentation_result: SegmentationResult, hint: str | None = None) -> bool:
        return False

    def extract(self, *, segmentation_result: SegmentationResult) -> LegalObjectExtractionResult:
        raise NotImplementedError(
            "Legislative legal object extraction is not implemented in TASK-002C"
        )
