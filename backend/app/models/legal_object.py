import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class LegalObject(Base):
    __tablename__ = "legal_objects"

    legal_object_id: Mapped[str] = mapped_column(String(64), primary_key=True)

    source_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_documents.id"),
        nullable=False,
    )

    country_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("countries.id"),
        nullable=False,
    )

    tax_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tax_types.id"),
        nullable=True,
    )

    object_type: Mapped[str] = mapped_column(String(50), nullable=False)
    canonical_path: Mapped[str] = mapped_column(String(1024), nullable=False)

    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal_object_versions.legal_object_version_id"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    source_document = relationship("SourceDocument")
    country = relationship("Country")
    tax_type = relationship("TaxType")
    current_version = relationship(
        "LegalObjectVersion",
        foreign_keys=[current_version_id],
    )
    versions = relationship(
        "LegalObjectVersion",
        back_populates="legal_object",
        foreign_keys="LegalObjectVersion.legal_object_id",
    )
