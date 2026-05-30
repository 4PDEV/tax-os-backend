import re
import time
from uuid import UUID

from app.core.datetime_utils import utc_now
from app.services.segmentation.enums import SegmentationStatus, SegmentType
from app.services.segmentation.models import (
    Segment,
    SegmentationMetadata,
    SegmentationResult,
    SegmentMetadata,
)
from app.services.segmentation.segmenters.base import BaseSegmenter

# Structural depth ranking used ONLY to resolve parent/child relationships.
# Lower rank = structurally higher (closer to the document root). These ranks
# carry no legal or semantic meaning; they describe nesting order only.
STRUCTURAL_RANK: dict[SegmentType, int] = {
    SegmentType.DOCUMENT: 0,
    SegmentType.PART: 1,
    SegmentType.SCHEDULE: 1,
    SegmentType.CHAPTER: 2,
    SegmentType.SECTION: 3,
    SegmentType.ARTICLE: 4,
    SegmentType.CLAUSE: 5,
    SegmentType.SUBCLAUSE: 6,
    SegmentType.PARAGRAPH: 7,
    SegmentType.UNKNOWN: 7,
}

# Deterministic structural markers matched against the first line of a block.
# Order matters: more specific / higher-level markers are checked first. These
# are purely structural surface patterns, not legal classification.
_MARKER_PATTERNS: list[tuple[SegmentType, re.Pattern[str]]] = [
    (SegmentType.PART, re.compile(r"^part\s+([ivxlcdm]+|\d+)\b", re.IGNORECASE)),
    (SegmentType.CHAPTER, re.compile(r"^chapter\s+([ivxlcdm]+|\d+)\b", re.IGNORECASE)),
    (SegmentType.SCHEDULE, re.compile(r"^schedule\b", re.IGNORECASE)),
    (SegmentType.SECTION, re.compile(r"^section\s+\d+", re.IGNORECASE)),
    (SegmentType.ARTICLE, re.compile(r"^article\s+\d+", re.IGNORECASE)),
    (SegmentType.SUBCLAUSE, re.compile(r"^\(?[a-z]\)")),
    (SegmentType.CLAUSE, re.compile(r"^\(?\d+[.)]")),
]

# A block is a run of text starting at a non-whitespace character and ending
# at the next blank-line boundary (or end of text). Offsets are preserved.
_BLOCK_PATTERN = re.compile(r"\S.*?(?=\n[ \t]*\n|\Z)", re.DOTALL)


def _segment_id(sequence_number: int) -> str:
    return f"seg-{sequence_number:04d}"


def _classify(first_line: str) -> tuple[SegmentType, str | None]:
    for segment_type, pattern in _MARKER_PATTERNS:
        if pattern.match(first_line):
            return segment_type, first_line
    return SegmentType.PARAGRAPH, None


def _line_count(text: str) -> int:
    return text.count("\n") + 1 if text else 0


class GenericSegmenter(BaseSegmenter):
    """Deterministic, source-faithful structural segmenter.

    Splits extracted text into ordered blocks on blank-line boundaries, labels
    each block with a structural type via surface markers (numbering / headings),
    and reconstructs parent/child hierarchy using structural ranks. No semantic
    interpretation, summarization, or legal inference is performed. Every segment
    preserves exact source offsets so ``raw_text == source[start:end]``.
    """

    name = "generic"
    version = "1.0.0"

    def can_handle(self, *, raw_text: str, hint: str | None = None) -> bool:
        return isinstance(raw_text, str)

    def segment(self, *, source_version_id: UUID, raw_text: str) -> SegmentationResult:
        started = time.perf_counter()

        root_id = _segment_id(0)
        root = Segment(
            segment_id=root_id,
            segment_type=SegmentType.DOCUMENT,
            hierarchy_level=0,
            parent_segment_id=None,
            sequence_number=0,
            heading=None,
            raw_text=raw_text,
            start_offset=0,
            end_offset=len(raw_text),
            metadata=SegmentMetadata(
                char_count=len(raw_text),
                line_count=_line_count(raw_text),
            ),
        )
        segments: list[Segment] = [root]

        # Stack of (segment_id, structural_rank, hierarchy_level) for parent resolution.
        stack: list[tuple[str, int, int]] = [(root_id, 0, 0)]

        sequence_number = 1
        for match in _BLOCK_PATTERN.finditer(raw_text):
            block_text = match.group()
            start_offset = match.start()
            end_offset = match.end()

            first_line = block_text.splitlines()[0].strip() if block_text.strip() else ""
            segment_type, marker = _classify(first_line)
            rank = STRUCTURAL_RANK[segment_type]

            while len(stack) > 1 and stack[-1][1] >= rank:
                stack.pop()

            parent_id, _parent_rank, parent_level = stack[-1]
            hierarchy_level = parent_level + 1

            segment_id = _segment_id(sequence_number)
            segments.append(
                Segment(
                    segment_id=segment_id,
                    segment_type=segment_type,
                    hierarchy_level=hierarchy_level,
                    parent_segment_id=parent_id,
                    sequence_number=sequence_number,
                    heading=marker,
                    raw_text=block_text,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    metadata=SegmentMetadata(
                        char_count=len(block_text),
                        line_count=_line_count(block_text),
                        matched_marker=marker,
                    ),
                )
            )
            stack.append((segment_id, rank, hierarchy_level))
            sequence_number += 1

        duration_ms = (time.perf_counter() - started) * 1000.0
        block_count = len(segments) - 1

        return SegmentationResult(
            source_version_id=source_version_id,
            segmentation_status=SegmentationStatus.SUCCESS,
            segmenter_name=self.name,
            segmenter_version=self.version,
            segmented_at=utc_now(),
            segment_count=len(segments),
            segments=segments,
            metadata=SegmentationMetadata(
                source_char_count=len(raw_text),
                block_count=block_count,
                duration_ms=duration_ms,
            ),
        )
