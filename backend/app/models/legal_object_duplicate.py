import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class LegalObjectDuplicate(Base):
    __tablename__ = "legal_object_duplicates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    primary_legal_object_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("legal_objects.legal_object_id"),
        nullable=False,
    )

    duplicate_legal_object_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("legal_objects.legal_object_id"),
        nullable=False,
    )

    duplicate_type: Mapped[str] = mapped_column(String(50), nullable=False)
    text_hash_match: Mapped[bool] = mapped_column(Boolean, nullable=False)
    canonical_path_match: Mapped[bool] = mapped_column(Boolean, nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    primary_legal_object = relationship("LegalObject", foreign_keys=[primary_legal_object_id])
    duplicate_legal_object = relationship(
        "LegalObject",
        foreign_keys=[duplicate_legal_object_id],
    )
