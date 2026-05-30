import time

from app.core.datetime_utils import utc_now
from app.services.legal_objects.enums import ExtractionStatus, LegalObjectType
from app.services.legal_objects.extractors.base import BaseLegalObjectExtractor
from app.services.legal_objects.models import (
    LegalObjectCandidate,
    LegalObjectExtractionMetadata,
    LegalObjectExtractionResult,
    LegalObjectMetadata,
)
from app.services.segmentation.enums import SegmentType
from app.services.segmentation.models import SegmentationResult

# Pure surface mapping from structural segment types to canonical legal object
# types. This is NOT semantic classification — it is a one-to-one structural
# relabeling. `DOCUMENT` has no structural legal-object analogue and maps to
# `UNKNOWN`.
SEGMENT_TYPE_TO_OBJECT_TYPE: dict[SegmentType, LegalObjectType] = {
    SegmentType.PART: LegalObjectType.PART,
    SegmentType.CHAPTER: LegalObjectType.CHAPTER,
    SegmentType.SECTION: LegalObjectType.SECTION,
    SegmentType.ARTICLE: LegalObjectType.ARTICLE,
    SegmentType.CLAUSE: LegalObjectType.CLAUSE,
    SegmentType.SUBCLAUSE: LegalObjectType.SUBCLAUSE,
    SegmentType.PARAGRAPH: LegalObjectType.PARAGRAPH,
    SegmentType.SCHEDULE: LegalObjectType.SCHEDULE,
    SegmentType.UNKNOWN: LegalObjectType.UNKNOWN,
    SegmentType.DOCUMENT: LegalObjectType.UNKNOWN,
}


def _legal_object_id(sequence_number: int) -> str:
    return f"lo-{sequence_number:04d}"


class GenericLegalObjectExtractor(BaseLegalObjectExtractor):
    """Deterministic, source-faithful structural legal object extractor.

    Maps each segment of a :class:`SegmentationResult` to exactly one
    :class:`LegalObjectCandidate` using a fixed surface mapping. Source text,
    offsets, sequencing, and hierarchy are preserved verbatim from the
    segmentation layer. No semantic interpretation, summarization, or legal
    classification is performed.
    """

    name = "generic"
    version = "1.0.0"

    def can_handle(self, *, segmentation_result: SegmentationResult, hint: str | None = None) -> bool:
        return isinstance(segmentation_result, SegmentationResult)

    def extract(self, *, segmentation_result: SegmentationResult) -> LegalObjectExtractionResult:
        started = time.perf_counter()

        source_version_id = segmentation_result.source_version_id

        # Map each source segment id to its derived legal object id so that
        # parent/child relationships from segmentation are preserved.
        segment_id_to_object_id: dict[str, str] = {
            segment.segment_id: _legal_object_id(segment.sequence_number)
            for segment in segmentation_result.segments
        }

        legal_objects: list[LegalObjectCandidate] = []
        for segment in segmentation_result.segments:
            object_type = SEGMENT_TYPE_TO_OBJECT_TYPE.get(
                segment.segment_type, LegalObjectType.UNKNOWN
            )
            parent_object_id = (
                segment_id_to_object_id.get(segment.parent_segment_id)
                if segment.parent_segment_id is not None
                else None
            )
            # Structural confidence: full when the segment type maps to an
            # identically named legal object type, zero for the structural
            # fallback (e.g. DOCUMENT -> UNKNOWN). Observational only.
            confidence = 1.0 if segment.segment_type.value == object_type.value else 0.0
            object_label = segment.heading if segment.heading else object_type.value

            legal_objects.append(
                LegalObjectCandidate(
                    legal_object_id=_legal_object_id(segment.sequence_number),
                    source_version_id=source_version_id,
                    source_segment_id=segment.segment_id,
                    object_type=object_type,
                    object_label=object_label,
                    heading=segment.heading,
                    raw_text=segment.raw_text,
                    start_offset=segment.start_offset,
                    end_offset=segment.end_offset,
                    sequence_number=segment.sequence_number,
                    parent_legal_object_id=parent_object_id,
                    hierarchy_level=segment.hierarchy_level,
                    metadata=LegalObjectMetadata(
                        mapped_from_segment_type=segment.segment_type.value,
                        confidence_of_structural_mapping=confidence,
                    ),
                )
            )

        duration_ms = (time.perf_counter() - started) * 1000.0

        return LegalObjectExtractionResult(
            source_version_id=source_version_id,
            extraction_status=ExtractionStatus.SUCCESS,
            extractor_name=self.name,
            extractor_version=self.version,
            extracted_at=utc_now(),
            legal_object_count=len(legal_objects),
            legal_objects=legal_objects,
            metadata=LegalObjectExtractionMetadata(
                source_segment_count=len(segmentation_result.segments),
                mapped_count=len(legal_objects),
                duration_ms=duration_ms,
            ),
        )
