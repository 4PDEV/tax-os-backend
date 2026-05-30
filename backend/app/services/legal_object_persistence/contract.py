"""Legal Object Persistence Repository Contract.

This module defines the controlled write-path boundary for persisting converged
legal object candidates into canonical legal object tables.

The ONLY permitted persistence input is
:class:`app.services.legal_object_convergence.models.ConvergedLegalObjectCandidate`.

This layer performs NO CRUD APIs, ingestion wiring, batch jobs, topic
classification, citation persistence, answer generation, or AI.
"""

from typing import Any

from app.services.legal_object_convergence.models import ConvergedLegalObjectCandidate

CANONICAL_PERSISTENCE_INPUT = ConvergedLegalObjectCandidate

BLOCKED_DIRECT_WRITE_SOURCES: tuple[str, ...] = (
    "segmentation",
    "structure_parser",
    "legal_object_extraction",
    "legal_objects",
)

__all__ = [
    "BLOCKED_DIRECT_WRITE_SOURCES",
    "CANONICAL_PERSISTENCE_INPUT",
    "LegalObjectPersistenceError",
    "assert_converged_persistence_input",
    "is_converged_persistence_input",
]


class LegalObjectPersistenceError(Exception):
    """Raised when persistence input or operation violates the contract."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def is_converged_persistence_input(value: Any) -> bool:
    return isinstance(value, ConvergedLegalObjectCandidate)


def assert_converged_persistence_input(value: Any) -> ConvergedLegalObjectCandidate:
    if not is_converged_persistence_input(value):
        raise LegalObjectPersistenceError(
            "persistence input must be ConvergedLegalObjectCandidate from "
            "legal_object_convergence; direct writes from upstream pipelines "
            f"are prohibited (blocked: {', '.join(BLOCKED_DIRECT_WRITE_SOURCES)})"
        )
    return value
