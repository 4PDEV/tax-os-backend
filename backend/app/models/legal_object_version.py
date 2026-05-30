import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class LegalObjectVersion(Base):
    __tablename__ = "legal_object_versions"

    legal_object_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    legal_object_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("legal_objects.legal_object_id"),
        nullable=False,
    )

    source_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_versions.id"),
        nullable=False,
    )

    parent_legal_object_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("legal_objects.legal_object_id"),
        nullable=True,
    )

    structural_unit_id: Mapped[str] = mapped_column(String(255), nullable=False)
    object_label: Mapped[str] = mapped_column(String(512), nullable=False)
    object_title: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)

    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    version_status: Mapped[str] = mapped_column(String(50), nullable=False)
    extraction_status: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    legal_object = relationship(
        "LegalObject",
        back_populates="versions",
        foreign_keys=[legal_object_id],
    )
    source_version = relationship("SourceVersion")
    parent_legal_object = relationship(
        "LegalObject",
        foreign_keys=[parent_legal_object_id],
    )
