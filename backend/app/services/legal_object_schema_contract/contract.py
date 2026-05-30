"""Canonical Legal Object Persistence Schema Contract.

This module defines the governance boundary for the canonical database schema
contract for persisted legal objects.

Schema contract is strictly planning — NOT implementation. It defines proposed
tables, fields, constraints, indexes, immutability rules, and lineage rules for
future migration tasks.

This layer performs NO SQLAlchemy models, Alembic migrations, repositories,
CRUD APIs, persistence services, or ingestion execution.

The ONLY approved upstream persistence input remains
:class:`app.services.legal_object_convergence.models.ConvergedLegalObjectCandidate`.
"""

from app.services.legal_object_convergence.models import ConvergedLegalObjectCandidate

CANONICAL_PERSISTENCE_INPUT = ConvergedLegalObjectCandidate

PROPOSED_TABLES: tuple[str, ...] = (
    "legal_objects",
    "legal_object_versions",
    "legal_object_lineage",
    "legal_object_duplicates",
)

__all__ = [
    "CANONICAL_PERSISTENCE_INPUT",
    "LegalObjectSchemaContractError",
    "PROPOSED_TABLES",
    "schema_contract_is_complete",
]


class LegalObjectSchemaContractError(Exception):
    """Raised when schema contract validation fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def schema_contract_is_complete() -> bool:
    """Return True when all required proposed tables are defined."""
    from app.services.legal_object_schema_contract.schema_definition import (
        SCHEMA_TABLES,
    )

    defined = {table.name for table in SCHEMA_TABLES}
    return all(name in defined for name in PROPOSED_TABLES)
