from app.services.citation_anchors.generators.base import BaseCitationAnchorGenerator
from app.services.citation_anchors.models import CitationAnchorGenerationResult
from app.services.legal_objects.models import LegalObjectExtractionResult


class LegislativeCitationAnchorGenerator(BaseCitationAnchorGenerator):
    """Skeleton legislative citation anchor generator.

    Intentionally unimplemented. A future, dedicated task will provide
    deterministic legislative-aware anchor generation (e.g. jurisdiction- and
    instrument-specific canonical citation lineages that follow legislative
    drafting and citation conventions). That work is out of scope here and must
    remain:

    - deterministic, stable, and reproducible
    - source-faithful (exact offsets, no rewriting)
    - non-interpretive (no AI, semantic interpretation, authority ranking, or
      mutable display formatting feeding the canonical anchor)

    When implemented, ``generate`` must build on the same contract
    (:class:`CitationAnchorGenerationResult`) and bump ``version`` accordingly.
    """

    name = "legislative"
    version = "0.0.0"

    def can_handle(self, *, extraction_result: LegalObjectExtractionResult, hint: str | None = None) -> bool:
        return False

    def generate(self, *, extraction_result: LegalObjectExtractionResult) -> CitationAnchorGenerationResult:
        raise NotImplementedError(
            "Legislative citation anchor generation is not implemented in TASK-002D"
        )
