from enum import Enum


class PipelineArtifactState(str, Enum):
    """Operational ingestion pipeline states (artifact layer).

    Distinct from ``source_versions.ingestion_status`` (worker queue workflow)
    and from legal/temporal lifecycle statuses.
    """

    SOURCE_REGISTERED = "source_registered"
    EXTRACTED = "extracted"
    PARSED = "parsed"
    LEGAL_OBJECTS_CREATED = "legal_objects_created"
    FAILED = "failed"
    PARTIAL = "partial"


class ParserRunStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


STORAGE_BACKEND_DATABASE = "database"
STORAGE_BACKEND_FILESYSTEM = "filesystem"
STORAGE_BACKEND_OBJECT_STORAGE = "object_storage"

STRUCTURE_TYPE_STRUCTURAL_UNITS = "structural_units"
