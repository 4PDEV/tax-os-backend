"""Legal Object Candidate Convergence Contract.

This module defines the governance boundary for OD-010 resolution at the contract
level — before any legal object persistence.

Convergence is strictly: upstream candidate outputs → canonical
:class:`app.services.legal_object_extraction.models.LegalObjectCandidate`.

This layer performs NO legal interpretation, topic classification, authority
ranking, conflict resolution, citation generation, answer generation, or
persistence. It enforces one canonical candidate shape and identity policy so
future persistence tasks have a single convergence boundary.

The canonical identity generator is
:func:`app.services.legal_object_extraction.identity.generate_legal_object_id`.
No other legal object ID generator may be used going forward unless approved by
architecture addendum.
"""

from app.services.legal_object_convergence.enums import ConvergenceSource, ConvergenceStatus
from app.services.legal_object_convergence.models import ConvergedLegalObjectCandidate

__all__ = [
    "ConvergedLegalObjectCandidate",
    "ConvergenceSource",
    "ConvergenceStatus",
    "LegalObjectConvergenceError",
]


class LegalObjectConvergenceError(Exception):
    """Raised when convergence cannot complete deterministically."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
