from pydantic import BaseModel, ConfigDict, Field

from app.services.legal_object_persistence.enums import (
    IntegrityOperationStatus,
    PersistenceStatus,
)


class LegalObjectPersistenceResult(BaseModel):
    """Result of persisting a converged legal object candidate."""

    model_config = ConfigDict(extra="forbid")

    legal_object_id: str
    legal_object_version_id: str | None = None
    persistence_status: PersistenceStatus
    created_legal_object: bool = False
    created_version: bool = False
    duplicate_detected: bool = False
    warnings: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class LegalObjectIntegrityResult(BaseModel):
    """Result of an integrity-governed lifecycle operation."""

    model_config = ConfigDict(extra="forbid")

    legal_object_id: str
    operation: str
    operation_status: IntegrityOperationStatus
    previous_status: str | None = None
    new_status: str | None = None
    related_legal_object_id: str | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
