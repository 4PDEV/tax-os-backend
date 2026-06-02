"""Deterministic structural segmentation from extracted text (non-interpretive)."""

from __future__ import annotations

import re
from typing import Any

ARTICLE_RE = re.compile(r"^Article\s+(\S+)\s*$", re.IGNORECASE)
SECTION_RE = re.compile(r"^Section\s+(\S+)\s*$", re.IGNORECASE)
SCHEDULE_RE = re.compile(r"^Schedule\s+(\S*)\s*$", re.IGNORECASE)
CLAUSE_RE = re.compile(r"^(\d+(?:\.\d+)*)\.\s+")
SUBCLAUSE_RE = re.compile(r"^\(([a-zA-Z0-9]+)\)\s+")
HEADING_RE = re.compile(r"^[A-Z][A-Z0-9\s\-]{2,80}$")

CONTROLLED_STRUCTURAL_PARSER_NAME = "controlled_structural_parsing_provider"
CONTROLLED_STRUCTURAL_PARSER_VERSION = "0.1.0"


def _line_char_offsets(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        start = offset
        offset += len(line)
        spans.append((start, offset, line.rstrip("\n\r")))
    return spans


def _unit(
    *,
    unit_type: str,
    unit_label: str | None,
    full_heading: str,
    raw_text: str,
    start_offset: int,
    end_offset: int,
    hierarchy_level: int,
    parent_unit_id: str | None = None,
    unit_title: str | None = None,
) -> dict[str, Any]:
    return {
        "unit_type": unit_type,
        "unit_label": unit_label,
        "unit_title": unit_title,
        "full_heading": full_heading,
        "parent_unit_id": parent_unit_id,
        "hierarchy_level": hierarchy_level,
        "start_offset": start_offset,
        "end_offset": end_offset,
        "raw_text": raw_text,
    }


def segment_extracted_text_structurally(raw_text: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return hash-stable structure units and JSON envelope metadata."""
    text = raw_text.strip()
    if not text:
        raise ValueError("extracted_text_not_eligible")

    lines = _line_char_offsets(text)
    non_empty = [(s, e, ln) for s, e, ln in lines if ln.strip()]
    if not non_empty:
        raise ValueError("extracted_text_not_eligible")

    warnings: list[str] = []
    units: list[dict[str, Any]] = []
    order = 0

    title: str | None = None
    first_start, first_end, first_line = non_empty[0]
    if len(non_empty) > 1 and len(first_line) <= 120 and not any(
        p.match(first_line) for p in (ARTICLE_RE, SECTION_RE, SCHEDULE_RE, CLAUSE_RE)
    ):
        title = first_line.strip()
        order += 1
        units.append(
            _unit(
                unit_type="heading",
                unit_label=None,
                full_heading=title,
                raw_text=first_line,
                start_offset=first_start,
                end_offset=first_end,
                hierarchy_level=0,
                unit_title=title,
            )
        )
        line_iter = non_empty[1:]
    else:
        line_iter = non_empty

    for start, end, line in line_iter:
        stripped = line.strip()
        if not stripped:
            continue

        order += 1
        unit_type = "paragraph"
        unit_label: str | None = None
        unit_title: str | None = None
        full_heading = stripped
        hierarchy_level = 2

        article = ARTICLE_RE.match(stripped)
        if article:
            unit_type = "article"
            unit_label = article.group(1)
            full_heading = stripped
            hierarchy_level = 1
        else:
            section = SECTION_RE.match(stripped)
            if section:
                unit_type = "section"
                unit_label = section.group(1)
                full_heading = stripped
                hierarchy_level = 1
            else:
                schedule = SCHEDULE_RE.match(stripped)
                if schedule:
                    unit_type = "schedule"
                    unit_label = schedule.group(1) or None
                    full_heading = stripped
                    hierarchy_level = 1
                else:
                    clause = CLAUSE_RE.match(stripped)
                    if clause:
                        unit_type = "clause"
                        unit_label = clause.group(1)
                        full_heading = stripped
                        hierarchy_level = 2
                    else:
                        sub = SUBCLAUSE_RE.match(stripped)
                        if sub:
                            unit_type = "clause"
                            unit_label = sub.group(1)
                            full_heading = stripped
                            hierarchy_level = 3
                        elif HEADING_RE.match(stripped) and len(stripped.split()) <= 12:
                            unit_type = "heading"
                            unit_label = None
                            full_heading = stripped
                            hierarchy_level = 1
                            unit_title = stripped

        units.append(
            _unit(
                unit_type=unit_type,
                unit_label=unit_label,
                full_heading=full_heading,
                raw_text=stripped,
                start_offset=start,
                end_offset=end,
                hierarchy_level=hierarchy_level,
                unit_title=stripped if unit_type == "heading" else None,
            )
        )

    if not units:
        warnings.append("no structural units detected; treating document as single paragraph")
        units.append(
            _unit(
                unit_type="unknown",
                unit_label=None,
                full_heading=text[:80],
                raw_text=text,
                start_offset=0,
                end_offset=len(text),
                hierarchy_level=0,
            )
        )

    envelope = {
        "parser_name": CONTROLLED_STRUCTURAL_PARSER_NAME,
        "parser_version": CONTROLLED_STRUCTURAL_PARSER_VERSION,
        "document": {
            "title": title,
            "unit_count": len(units),
        },
        "warnings": warnings,
    }
    return units, envelope
