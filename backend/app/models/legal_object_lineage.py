import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class LegalObjectLineage(Base):
    __tablename__ = "legal_object_lineage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    legal_object_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("legal_objects.legal_object_id"),
        nullable=False,
    )

    parent_legal_object_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("legal_objects.legal_object_id"),
        nullable=True,
    )

    supersedes_legal_object_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("legal_objects.legal_object_id"),
        nullable=True,
    )

    superseded_by_legal_object_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("legal_objects.legal_object_id"),
        nullable=True,
    )

    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)

    source_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_versions.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    legal_object = relationship("LegalObject", foreign_keys=[legal_object_id])
    parent_legal_object = relationship("LegalObject", foreign_keys=[parent_legal_object_id])
    supersedes_legal_object = relationship(
        "LegalObject",
        foreign_keys=[supersedes_legal_object_id],
    )
    superseded_by_legal_object = relationship(
        "LegalObject",
        foreign_keys=[superseded_by_legal_object_id],
    )
    source_version = relationship("SourceVersion")
