import re
from uuid import UUID

from app.core.datetime_utils import utc_now
from app.services.cross_reference.enums import ReferenceConfidence
from app.services.cross_reference.models import CrossReferenceResult
from app.services.cross_reference.patterns import (
    ALL_PATTERNS,
    ReferencePattern,
    TARGET_OF_PATTERN,
    format_reference_text,
)

_CONFIDENCE_RANK = {
    ReferenceConfidence.HIGH: 3,
    ReferenceConfidence.MEDIUM: 2,
    ReferenceConfidence.LOW: 1,
}


def _source_location(start: int, end: int) -> str:
    return f"{start}:{end}"


def _extract_target_candidate(text: str, match_start: int, match_end: int) -> str | None:
    window = text[match_start : min(len(text), match_end + 120)]
    target_match = TARGET_OF_PATTERN.search(window)
    if target_match:
        return target_match.group(1).strip()
    return None


class CrossReferenceDetector:
    """Deterministic cross-reference detector.

    Identifies structural references in source text using fixed regex patterns.
    No AI, embeddings, semantic inference, authority ranking, or legal
    interpretation is performed.
    """

    name = "generic"
    version = "1.0.0"

    def detect(self, *, source_version_id: UUID, text: str) -> list[CrossReferenceResult]:
        if not source_version_id:
            raise ValueError("source_version_id is required")

        hits: list[tuple[int, int, ReferencePattern, re.Match[str]]] = []

        for ref_pattern in ALL_PATTERNS:
            for match in ref_pattern.pattern.finditer(text):
                hits.append((match.start(), match.end(), ref_pattern, match))

        best_by_span: dict[tuple[int, int], tuple[ReferencePattern, re.Match[str]]] = {}
        for start, end, ref_pattern, match in hits:
            key = (start, end)
            existing = best_by_span.get(key)
            if existing is None or _CONFIDENCE_RANK[ref_pattern.confidence] > _CONFIDENCE_RANK[existing[0].confidence]:
                best_by_span[key] = (ref_pattern, match)

        detected_at = utc_now()
        results: list[CrossReferenceResult] = []

        for (start, end), (ref_pattern, match) in sorted(best_by_span.items(), key=lambda item: item[0][0]):
            reference_text = format_reference_text(match, ref_pattern)
            results.append(
                CrossReferenceResult(
                    source_version_id=source_version_id,
                    source_location=_source_location(start, end),
                    reference_text=reference_text,
                    reference_type=ref_pattern.reference_type,
                    target_candidate=_extract_target_candidate(text, start, end),
                    confidence=ref_pattern.confidence,
                    detected_at=detected_at,
                    detector_version=self.version,
                )
            )

        return results
