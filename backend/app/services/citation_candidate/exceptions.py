"""Explicit citation candidate builder failures."""


class CitationCandidateError(Exception):
    """Base class for citation candidate errors."""


class SourceTraceabilityError(CitationCandidateError):
    """Raised when required source linkage is missing."""

    def __init__(self, message: str):
        super().__init__(message)
