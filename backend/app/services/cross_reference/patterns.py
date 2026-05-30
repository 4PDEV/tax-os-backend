import re
from dataclasses import dataclass

from app.services.cross_reference.enums import ReferenceConfidence, ReferenceType

# Deterministic regex patterns for structural cross-reference detection.
# Order matters when applying: more specific patterns before generic ones.

@dataclass(frozen=True)
class ReferencePattern:
    reference_type: ReferenceType
    confidence: ReferenceConfidence
    pattern: re.Pattern[str]
    group_index: int = 0  # which match group forms reference_text suffix


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


# HIGH confidence — explicit single structural references
PATTERNS_HIGH: tuple[ReferencePattern, ...] = (
    ReferencePattern(ReferenceType.SECTION, ReferenceConfidence.HIGH, _compile(r"\bSection\s+(\d+(?:\.\d+)*)")),
    ReferencePattern(ReferenceType.ARTICLE, ReferenceConfidence.HIGH, _compile(r"\bArticle\s+(\d+(?:\.\d+)*)")),
    ReferencePattern(ReferenceType.REGULATION, ReferenceConfidence.HIGH, _compile(r"\bRegulation\s+(\d+(?:\.\d+)*)")),
    ReferencePattern(ReferenceType.SCHEDULE, ReferenceConfidence.HIGH, _compile(r"\bSchedule\s+(\d+(?:\.\d+)*)")),
    ReferencePattern(ReferenceType.PART, ReferenceConfidence.HIGH, _compile(r"\bPart\s+([IVXLCDM]+|\d+(?:\.\d+)*)")),
    ReferencePattern(ReferenceType.CHAPTER, ReferenceConfidence.HIGH, _compile(r"\bChapter\s+([IVXLCDM]+|\d+(?:\.\d+)*)")),
)

# MEDIUM confidence — explicit range references
PATTERNS_MEDIUM: tuple[ReferencePattern, ...] = (
    ReferencePattern(
        ReferenceType.SECTION,
        ReferenceConfidence.MEDIUM,
        _compile(r"\bSections\s+(\d+(?:\.\d+)*)\s*-\s*(\d+(?:\.\d+)*)"),
    ),
    ReferencePattern(
        ReferenceType.ARTICLE,
        ReferenceConfidence.MEDIUM,
        _compile(r"\bArticles\s+(\d+(?:\.\d+)*)\s*-\s*(\d+(?:\.\d+)*)"),
    ),
)

# LOW confidence — vague textual references (surface form only, no interpretation)
PATTERNS_LOW: tuple[ReferencePattern, ...] = (
    ReferencePattern(ReferenceType.UNKNOWN, ReferenceConfidence.LOW, _compile(r"\bthe above provision\b")),
    ReferencePattern(ReferenceType.UNKNOWN, ReferenceConfidence.LOW, _compile(r"\baforementioned\b")),
    ReferencePattern(ReferenceType.UNKNOWN, ReferenceConfidence.LOW, _compile(r"\bas provided herein\b")),
    ReferencePattern(ReferenceType.UNKNOWN, ReferenceConfidence.LOW, _compile(r"\bthe foregoing\b")),
)

ALL_PATTERNS: tuple[ReferencePattern, ...] = PATTERNS_HIGH + PATTERNS_MEDIUM + PATTERNS_LOW

# Extract target candidate from trailing "of the X" / "of X Act" context.
TARGET_OF_PATTERN = _compile(
    r"(?:Section|Sections|Article|Articles|Regulation|Schedule|Part|Chapter)\s+"
    r"[\dIVXLCDM.\-\s]+"
    r"\s+of\s+(?:the\s+)?([A-Z][A-Za-z0-9\s\-]+?(?:Act|Law|Regulation|Code|Treaty|Order|Notice|Ruling|Judgment|Guidance))"
)


def format_reference_text(match: re.Match[str], ref_pattern: ReferencePattern) -> str:
    """Build the matched reference_text string from a regex match."""
    if ref_pattern.confidence is ReferenceConfidence.MEDIUM:
        groups = match.groups()
        label = ref_pattern.reference_type.value.title()
        if len(groups) >= 2 and groups[1]:
            return f"{label}s {groups[0]}-{groups[1]}"
        return match.group(0)
    return match.group(0)
