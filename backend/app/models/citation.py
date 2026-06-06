import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class Citation(Base):
    """Canonical persisted citation — provenance-derived identity (TASK-006AD)."""

    __tablename__ = "citations"
    __table_args__ = (UniqueConstraint("citation_hash", name="uq_citations_citation_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    citation_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    citation_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    legal_object_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("legal_objects.legal_object_id"),
        nullable=False,
    )
    legal_object_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal_object_versions.legal_object_version_id"),
        nullable=False,
    )
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_versions.id"),
        nullable=False,
    )
    location_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    rendered_citation_text: Mapped[str] = mapped_column(Text, nullable=False)
    assembled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
