import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class LegalObjectPromotionResult(Base):
    __tablename__ = "legal_object_promotion_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    legal_object_promotion_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal_object_promotion_requests.id"),
        nullable=False,
    )
    parsed_structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parsed_structures.id"),
        nullable=False,
    )
    promotion_status: Mapped[str] = mapped_column(String(64), nullable=False)
    legal_object_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("legal_objects.legal_object_id"),
        nullable=True,
    )
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
