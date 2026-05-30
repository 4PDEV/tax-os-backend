"""Legal Object Persistence Planning Contract.

This module defines the governance boundary for legal object persistence planning.

Persistence planning is strictly architecture governance — NOT implementation.
It defines how converged legal object candidates may eventually be persisted
safely and deterministically.

This layer performs NO database operations, migrations, CRUD APIs, storage
pipelines, legal interpretation, or AI. No persistence work may proceed until
this planning contract is reviewed and approved by architecture.

The ONLY approved persistence input is
:class:`app.services.legal_object_convergence.models.ConvergedLegalObjectCandidate`.
"""

from typing import Any

from app.services.legal_object_convergence.models import ConvergedLegalObjectCandidate

CANONICAL_PERSISTENCE_INPUT = ConvergedLegalObjectCandidate

BLOCKED_DIRECT_PERSISTENCE_SOURCES: tuple[str, ...] = (
    "segmentation",
    "structure_parser",
    "legal_object_extraction",
    "legal_objects",
)

__all__ = [
    "BLOCKED_DIRECT_PERSISTENCE_SOURCES",
    "CANONICAL_PERSISTENCE_INPUT",
    "LegalObjectPersistencePlanningError",
    "assert_canonical_persistence_input",
    "is_approved_persistence_input",
]


class LegalObjectPersistencePlanningError(Exception):
    """Raised when persistence planning constraints are violated."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def is_approved_persistence_input(value: Any) -> bool:
    """Return True only when value is a converged legal object candidate."""
    return isinstance(value, ConvergedLegalObjectCandidate)


def assert_canonical_persistence_input(value: Any) -> ConvergedLegalObjectCandidate:
    """Enforce the canonical persistence input rule."""
    if not is_approved_persistence_input(value):
        raise LegalObjectPersistencePlanningError(
            "persistence input must be ConvergedLegalObjectCandidate from "
            "legal_object_convergence; direct persistence from upstream pipelines "
            f"is prohibited (blocked: {', '.join(BLOCKED_DIRECT_PERSISTENCE_SOURCES)})"
        )
    if value.convergence_status.value == "rejected":
        raise LegalObjectPersistencePlanningError(
            "rejected converged candidates must not be planned for persistence"
        )
    return value
