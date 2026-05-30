import hashlib
import re
import time

from app.core.datetime_utils import utc_now
from app.services.citation_anchors.enums import CitationAnchorType, GenerationStatus
from app.services.citation_anchors.generators.base import BaseCitationAnchorGenerator
from app.services.citation_anchors.models import (
    CanonicalCitationAnchor,
    CitationAnchorGenerationMetadata,
    CitationAnchorGenerationResult,
    CitationAnchorMetadata,
)
from app.services.legal_objects.enums import LegalObjectType
from app.services.legal_objects.models import LegalObjectCandidate, LegalObjectExtractionResult

# Surface mapping from legal object types to citation anchor types. Pure
# structural relabeling — never semantic classification.
OBJECT_TYPE_TO_ANCHOR_TYPE: dict[LegalObjectType, CitationAnchorType] = {
    LegalObjectType.PART: CitationAnchorType.PART,
    LegalObjectType.CHAPTER: CitationAnchorType.CHAPTER,
    LegalObjectType.SECTION: CitationAnchorType.SECTION,
    LegalObjectType.ARTICLE: CitationAnchorType.ARTICLE,
    LegalObjectType.CLAUSE: CitationAnchorType.CLAUSE,
    LegalObjectType.SUBCLAUSE: CitationAnchorType.SUBCLAUSE,
    LegalObjectType.PARAGRAPH: CitationAnchorType.PARAGRAPH,
    LegalObjectType.SCHEDULE: CitationAnchorType.SCHEDULE,
    LegalObjectType.DEFINITION: CitationAnchorType.DEFINITION,
}

_WHITESPACE = re.compile(r"\s+")


def _map_anchor_type(object_type: LegalObjectType) -> CitationAnchorType:
    return OBJECT_TYPE_TO_ANCHOR_TYPE.get(object_type, CitationAnchorType.UNKNOWN)


def _component_source_value(candidate: LegalObjectCandidate) -> str:
    """Pick the component value: object_label, else heading, else sequence_number."""
    if candidate.object_label:
        return candidate.object_label
    if candidate.heading:
        return candidate.heading
    return str(candidate.sequence_number)


def _normalize_component_value(value: str) -> str:
    normalized = value.strip()
    normalized = _WHITESPACE.sub("-", normalized)
    normalized = normalized.replace("/", "").replace("\\", "")
    return normalized


def _path_component(candidate: LegalObjectCandidate) -> str:
    anchor_type = _map_anchor_type(candidate.object_type)
    value = _normalize_component_value(_component_source_value(candidate))
    return f"{anchor_type.name}:{value}"


def _display_label(candidate: LegalObjectCandidate) -> str:
    anchor_type = _map_anchor_type(candidate.object_type)
    title = anchor_type.value.title()
    suffix = candidate.object_label if candidate.object_label else str(candidate.sequence_number)
    return f"{title} {suffix}"


def _citation_anchor_id(
    source_version_id: str,
    legal_object_id: str,
    canonical_anchor: str,
    start_offset: int,
    end_offset: int,
) -> str:
    raw = f"{source_version_id}|{legal_object_id}|{canonical_anchor}|{start_offset}|{end_offset}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class GenericCitationAnchorGenerator(BaseCitationAnchorGenerator):
    """Deterministic, structure-based citation anchor generator.

    Builds a canonical anchor for each legal object from its structural lineage
    (root -> current), using stable inputs only. Source text and offsets are
    preserved verbatim from the legal object candidate. No semantic
    interpretation, authority ranking, or AI is involved.
    """

    name = "generic"
    version = "1.0.0"

    def can_handle(self, *, extraction_result: LegalObjectExtractionResult, hint: str | None = None) -> bool:
        return isinstance(extraction_result, LegalObjectExtractionResult)

    def _build_hierarchy_path(
        self,
        candidate: LegalObjectCandidate,
        by_id: dict[str, LegalObjectCandidate],
    ) -> tuple[list[str], list[str]]:
        """Return (hierarchy_path, warnings) walking ancestors root -> current.

        If an ancestor reference cannot be resolved, fall back to the current
        object's component only and record an observational warning.
        """
        chain: list[LegalObjectCandidate] = []
        warnings: list[str] = []
        seen: set[str] = set()
        current: LegalObjectCandidate | None = candidate

        while current is not None:
            chain.append(current)
            parent_id = current.parent_legal_object_id
            if parent_id is None:
                break
            if parent_id in seen or parent_id not in by_id:
                warnings.append(
                    f"parent legal object '{parent_id}' not resolvable; "
                    "generated current-object anchor only"
                )
                return [_path_component(candidate)], warnings
            seen.add(parent_id)
            current = by_id[parent_id]

        chain.reverse()
        return [_path_component(member) for member in chain], warnings

    def generate(self, *, extraction_result: LegalObjectExtractionResult) -> CitationAnchorGenerationResult:
        started = time.perf_counter()
        source_version_id = extraction_result.source_version_id
        by_id = {obj.legal_object_id: obj for obj in extraction_result.legal_objects}

        anchors: list[CanonicalCitationAnchor] = []
        all_warnings: list[str] = []

        for candidate in extraction_result.legal_objects:
            hierarchy_path, warnings = self._build_hierarchy_path(candidate, by_id)
            canonical_anchor = "/".join(hierarchy_path)
            anchor_type = _map_anchor_type(candidate.object_type)
            anchor_id = _citation_anchor_id(
                str(source_version_id),
                candidate.legal_object_id,
                canonical_anchor,
                candidate.start_offset,
                candidate.end_offset,
            )
            all_warnings.extend(warnings)

            anchors.append(
                CanonicalCitationAnchor(
                    citation_anchor_id=anchor_id,
                    source_version_id=source_version_id,
                    legal_object_id=candidate.legal_object_id,
                    source_segment_id=candidate.source_segment_id,
                    anchor_type=anchor_type,
                    canonical_anchor=canonical_anchor,
                    display_label=_display_label(candidate),
                    hierarchy_path=hierarchy_path,
                    sequence_number=candidate.sequence_number,
                    start_offset=candidate.start_offset,
                    end_offset=candidate.end_offset,
                    raw_text=candidate.raw_text,
                    metadata=CitationAnchorMetadata(
                        generated_from_object_type=candidate.object_type.value,
                        anchor_generation_warnings=warnings,
                    ),
                )
            )

        duration_ms = (time.perf_counter() - started) * 1000.0

        return CitationAnchorGenerationResult(
            source_version_id=source_version_id,
            generation_status=GenerationStatus.SUCCESS,
            generator_name=self.name,
            generator_version=self.version,
            generated_at=utc_now(),
            citation_anchor_count=len(anchors),
            citation_anchors=anchors,
            metadata=CitationAnchorGenerationMetadata(
                source_object_count=len(extraction_result.legal_objects),
                generated_count=len(anchors),
                duration_ms=duration_ms,
                anchor_generation_warnings=all_warnings,
            ),
        )
