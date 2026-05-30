from app.core.datetime_utils import utc_now
from app.services.legal_object_extraction.enums import LegalObjectExtractionStatus, LegalObjectType
from app.services.legal_object_extraction.identity import (
    build_canonical_path,
    generate_legal_object_id,
    sha256_text,
)
from app.services.legal_object_extraction.models import LegalObjectCandidate
from app.services.structure_parser.enums import StructuralUnitType
from app.services.structure_parser.models import StructuralUnit

EXTRACTOR_VERSION = "1.0.0"

STRUCTURAL_TO_LEGAL: dict[StructuralUnitType, LegalObjectType] = {
    StructuralUnitType.ACT: LegalObjectType.ACT,
    StructuralUnitType.LAW: LegalObjectType.LAW,
    StructuralUnitType.TITLE: LegalObjectType.TITLE,
    StructuralUnitType.PART: LegalObjectType.PART,
    StructuralUnitType.CHAPTER: LegalObjectType.CHAPTER,
    StructuralUnitType.SECTION: LegalObjectType.SECTION,
    StructuralUnitType.ARTICLE: LegalObjectType.ARTICLE,
    StructuralUnitType.REGULATION: LegalObjectType.REGULATION,
    StructuralUnitType.SCHEDULE: LegalObjectType.SCHEDULE,
    StructuralUnitType.PARAGRAPH: LegalObjectType.PARAGRAPH,
    StructuralUnitType.SUBPARAGRAPH: LegalObjectType.SUBPARAGRAPH,
}


def map_object_type(unit_type: StructuralUnitType) -> LegalObjectType:
    return STRUCTURAL_TO_LEGAL.get(unit_type, LegalObjectType.UNKNOWN)


class LegalObjectExtractor:
    """Deterministic extractor: structural units → legal object candidates.

    Preserves source_version_id, structural_unit_id, parent lineage, canonical
    path, offsets, raw text, text hash, and document order. No interpretation,
    persistence, or AI.
    """

    def extract(self, structural_units: list[StructuralUnit]) -> list[LegalObjectCandidate]:
        if not structural_units:
            return []

        extracted_at = utc_now()
        by_id = {unit.unit_id: unit for unit in structural_units}
        unit_id_to_legal_id: dict[str, str] = {}
        candidates: list[LegalObjectCandidate] = []

        for unit in structural_units:
            source_version_id = str(unit.source_version_id)
            object_type = map_object_type(unit.unit_type)
            canonical_path = build_canonical_path(unit, by_id)
            text_hash = sha256_text(unit.raw_text)

            legal_object_id = generate_legal_object_id(
                source_version_id=source_version_id,
                canonical_path=canonical_path,
                object_type=object_type.value,
                object_label=unit.unit_label,
                start_offset=unit.start_offset,
                text_hash=text_hash,
            )

            status = LegalObjectExtractionStatus.SUCCESS
            parent_legal_object_id: str | None = None
            metadata: dict = {}

            if unit.parent_unit_id:
                if unit.parent_unit_id in unit_id_to_legal_id:
                    parent_legal_object_id = unit_id_to_legal_id[unit.parent_unit_id]
                else:
                    status = LegalObjectExtractionStatus.PARTIAL
                    metadata["extraction_warning"] = (
                        f"structural parent '{unit.parent_unit_id}' not found in input batch"
                    )

            candidates.append(
                LegalObjectCandidate(
                    source_version_id=source_version_id,
                    legal_object_id=legal_object_id,
                    object_type=object_type,
                    object_label=unit.unit_label,
                    object_title=unit.unit_title,
                    canonical_path=canonical_path,
                    parent_legal_object_id=parent_legal_object_id,
                    structural_unit_id=unit.unit_id,
                    start_offset=unit.start_offset,
                    end_offset=unit.end_offset,
                    raw_text=unit.raw_text,
                    text_hash=text_hash,
                    extraction_status=status,
                    extracted_at=extracted_at,
                    extractor_version=EXTRACTOR_VERSION,
                    metadata=metadata,
                )
            )
            unit_id_to_legal_id[unit.unit_id] = legal_object_id

        return candidates
