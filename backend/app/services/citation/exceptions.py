"""Explicit citation assembly failures."""


class CitationAssemblyError(Exception):
    """Base class for citation assembly errors."""


class MissingSourceVersionError(CitationAssemblyError):
    """Raised when a specific source version cannot be resolved."""


class MissingLocationReferenceError(CitationAssemblyError):
    """Raised when location identification is absent."""


class LegalObjectVersionMismatchError(CitationAssemblyError):
    """Raised when the pinned version does not belong to the legal object."""


class SourceDocumentMismatchError(CitationAssemblyError):
    """Raised when source_version lineage does not match the legal object source document."""
