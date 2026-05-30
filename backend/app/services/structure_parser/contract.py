"""Structural Section Parser Contract.

This module defines the governance boundary for structural document parsing.

Parsing is strictly: Extracted Text → Structural Units.

The parser must be deterministic, reproducible, traceable, hierarchy-aware, and
source-backed. It must preserve ordering, hierarchy, text integrity, and
structural lineage. It must NEVER interpret law, infer legal meaning, classify
topics, or generate legal conclusions. No AI inference or semantic reasoning
is permitted.

Concrete contract objects:

- :class:`app.services.structure_parser.enums.StructuralUnitType`
- :class:`app.services.structure_parser.models.StructuralUnit`
- :class:`app.services.structure_parser.parser.StructuralParser`
"""

from app.services.structure_parser.enums import StructuralUnitType
from app.services.structure_parser.models import StructuralUnit

__all__ = [
    "StructuralParseError",
    "StructuralUnit",
    "StructuralUnitType",
]


class StructuralParseError(Exception):
    """Raised when structural parsing cannot complete deterministically."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
