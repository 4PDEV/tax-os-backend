from uuid import UUID

from app.core.datetime_utils import utc_now
from app.services.structure_parser.hierarchy import assign_hierarchy
from app.services.structure_parser.models import StructuralUnit
from app.services.structure_parser.patterns import classify_heading_line, split_label_and_title


def _unit_id(sequence: int) -> str:
    return f"su-{sequence:04d}"


def _iter_lines_with_offsets(text: str):
    offset = 0
    for line in text.splitlines(keepends=True):
        yield offset, line
        offset += len(line)


class StructuralParser:
    """Deterministic structural scanner for extracted document text.

    Identifies structural units (Part, Chapter, Section, etc.) using fixed
    regex patterns at line boundaries. Preserves document order, parent-child
    hierarchy, exact offsets, and raw text fidelity. No AI, semantic parsing, or
    legal interpretation is performed.
    """

    name = "generic"
    version = "1.0.0"

    def parse(self, *, source_version_id: UUID, text: str) -> list[StructuralUnit]:
        if not source_version_id:
            raise ValueError("source_version_id is required")

        headings = []
        for line_start, line in _iter_lines_with_offsets(text):
            match = classify_heading_line(line, line_start)
            if match:
                headings.append(match)

        if not headings:
            return []

        detected_at = utc_now()
        units: list[StructuralUnit] = []

        for index, heading in enumerate(headings):
            start_offset = heading.line_start
            end_offset = headings[index + 1].line_start if index + 1 < len(headings) else len(text)
            raw_text = text[start_offset:end_offset]
            unit_label, unit_title = split_label_and_title(heading.full_heading, heading.unit_label)

            units.append(
                StructuralUnit(
                    source_version_id=source_version_id,
                    unit_id=_unit_id(index),
                    unit_type=heading.unit_type,
                    unit_label=unit_label,
                    unit_title=unit_title,
                    full_heading=heading.full_heading,
                    parent_unit_id=None,
                    hierarchy_level=0,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    raw_text=raw_text,
                    detected_at=detected_at,
                    parser_version=self.version,
                )
            )

        assign_hierarchy(units)
        return units
