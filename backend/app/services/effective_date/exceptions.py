"""Explicit effective-date resolution failures."""


class EffectiveDateResolverError(Exception):
    """Base class for effective-date resolver errors."""


class LegalObjectResolutionNotFoundError(EffectiveDateResolverError):
    """Raised when a requested legal object cannot be resolved."""

    def __init__(self, legal_object_id: str):
        self.legal_object_id = legal_object_id
        super().__init__(f"legal object resolution not found: {legal_object_id}")
