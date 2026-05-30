from uuid import UUID

from app.services.segmentation.models import SegmentationResult
from app.services.segmentation.segmenters.base import BaseSegmenter


class LegislativeSegmenter(BaseSegmenter):
    """Skeleton legislative segmenter.

    Intentionally unimplemented. A future, dedicated task will provide
    deterministic legislative-structure segmentation (e.g. Part / Chapter /
    Section / Article / Clause hierarchies specific to legislative drafting
    conventions). That work is out of scope here and must remain:

    - deterministic and reproducible
    - source-faithful (exact offsets, no rewriting)
    - non-interpretive (no legal classification, citation, or inference)

    When implemented, ``segment`` must build on the same contract
    (:class:`SegmentationResult`) and bump ``version`` accordingly.
    """

    name = "legislative"
    version = "0.0.0"

    def can_handle(self, *, raw_text: str, hint: str | None = None) -> bool:
        return False

    def segment(self, *, source_version_id: UUID, raw_text: str) -> SegmentationResult:
        raise NotImplementedError("Legislative segmentation is not implemented in TASK-002B")
