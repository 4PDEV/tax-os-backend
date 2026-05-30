import re
from dataclasses import dataclass

from app.services.structure_parser.enums import StructuralUnitType

# Structural depth ranking for parent/child resolution only (not legal hierarchy).
STRUCTURAL_RANK: dict[StructuralUnitType, int] = {
    StructuralUnitType.ACT: 0,
    StructuralUnitType.LAW: 0,
    StructuralUnitType.TITLE: 1,
    StructuralUnitType.PART: 2,
    StructuralUnitType.CHAPTER: 3,
    StructuralUnitType.ARTICLE: 4,
    StructuralUnitType.SECTION: 5,
    StructuralUnitType.REGULATION: 6,
    StructuralUnitType.SCHEDULE: 7,
    StructuralUnitType.PARAGRAPH: 8,
    StructuralUnitType.SUBPARAGRAPH: 9,
    StructuralUnitType.UNKNOWN: 10,
}

# Separator between structural label and optional title on the same line.
TITLE_SEPARATOR = re.compile(r"\s*[—–\-:\u2013\u2014]\s*")


@dataclass(frozen=True)
class HeadingMatch:
    unit_type: StructuralUnitType
    unit_label: str
    line_start: int
    line_end: int
    full_heading: str


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


# Line-start structural heading patterns. Order: higher structural level first.
HEADING_PATTERNS: tuple[tuple[StructuralUnitType, re.Pattern[str], str], ...] = (
    (
        StructuralUnitType.ACT,
        _compile(r"^(.+?\sAct)\s*$"),
        r"\1",
    ),
    (
        StructuralUnitType.LAW,
        _compile(r"^(.+?\sLaw)\s*$"),
        r"\1",
    ),
    (
        StructuralUnitType.TITLE,
        _compile(r"^(Title\s+.+)"),
        r"\1",
    ),
    (
        StructuralUnitType.PART,
        _compile(r"^(PART\s+(?:[IVXLCDM]+|\d+))\b"),
        r"\1",
    ),
    (
        StructuralUnitType.CHAPTER,
        _compile(r"^(CHAPTER\s+(?:[IVXLCDM]+|\d+))\b"),
        r"\1",
    ),
    (
        StructuralUnitType.ARTICLE,
        _compile(r"^(Article\s+\d+(?:\.\d+)*)"),
        r"\1",
    ),
    (
        StructuralUnitType.SECTION,
        _compile(r"^(Section\s+\d+(?:\.\d+)*)"),
        r"\1",
    ),
    (
        StructuralUnitType.REGULATION,
        _compile(r"^(Regulation\s+\d+(?:\.\d+)*)"),
        r"\1",
    ),
    (
        StructuralUnitType.SCHEDULE,
        _compile(r"^(Schedule\s+(?:[A-Z]|\d+))"),
        r"\1",
    ),
    (
        StructuralUnitType.PARAGRAPH,
        _compile(r"^(Paragraph\s+\d+(?:\.\d+)*)"),
        r"\1",
    ),
    (
        StructuralUnitType.SUBPARAGRAPH,
        _compile(r"^(Subparagraph\s+\([a-z]\)|\([a-z]\))"),
        r"\1",
    ),
)


def classify_heading_line(line: str, line_start: int) -> HeadingMatch | None:
    stripped = line.strip()
    if not stripped:
        return None
    for unit_type, pattern, _ in HEADING_PATTERNS:
        match = pattern.match(stripped)
        if match:
            unit_label = match.group(1).strip()
            return HeadingMatch(
                unit_type=unit_type,
                unit_label=unit_label,
                line_start=line_start,
                line_end=line_start + len(line),
                full_heading=stripped,
            )
    return None


def split_label_and_title(full_heading: str, unit_label: str) -> tuple[str, str | None]:
    parts = TITLE_SEPARATOR.split(full_heading, maxsplit=1)
    if len(parts) == 2 and parts[1].strip():
        return parts[0].strip(), parts[1].strip()
    return unit_label, None
