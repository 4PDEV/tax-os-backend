from pydantic import BaseModel, ConfigDict, Field

from app.services.legal_object_persistence.enums import PersistenceStatus


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
