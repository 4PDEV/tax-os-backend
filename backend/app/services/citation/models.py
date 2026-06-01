from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuthorityType(str, Enum):
    """Structural authority classification for assembled citations."""

    STATUTE = "statute"
    REGULATION = "regulation"
    GUIDANCE = "guidance"
    PUBLIC_RULING = "public_ruling"
    PRIVATE_RULING = "private_ruling"
    CASE = "case"
    TRIBUNAL = "tribunal"
    TREATY = "treaty"
    ACCOUNTING_STANDARD = "accounting_standard"
    OTHER = "other"


class LocationReferenceKind(str, Enum):
    """Supported location identification kinds — identification only, no interpretation."""

    SECTION = "section"
    ARTICLE = "article"
    REGULATION = "regulation"
    PART = "part"
    CHAPTER = "chapter"
    SCHEDULE = "schedule"
    PARAGRAPH = "paragraph"
    CLAUSE = "clause"
    SUBSECTION = "subsection"


class CitationAssemblyRequest(BaseModel):
    """Request to assemble a citation for a specific legal object version."""

    model_config = ConfigDict(extra="forbid")

    legal_object_id: str
    legal_object_version_id: UUID = Field(
        description="Required pin to a specific legal object version — never implicit latest.",
    )


class CitationResult(BaseModel):
    """Assembled source-backed citation — deterministic and auditable."""

    model_config = ConfigDict(extra="forbid")

    citation_id: str
    source_document_id: UUID
    source_version_id: UUID
    legal_object_id: str
    authority_type: AuthorityType
    source_title: str
    official_reference: str | None = None
    publication_date: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    location_reference: str
    citation_text: str
    citation_hash: str
    assembled_at: datetime
    assembler_version: str
