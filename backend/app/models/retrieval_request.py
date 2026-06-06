import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class RetrievalRequest(Base):
    __tablename__ = "retrieval_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    retrieval_mode: Mapped[str] = mapped_column(String(64), nullable=False)
    as_of_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    legal_object_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal_object_versions.legal_object_version_id"),
        nullable=True,
    )
    jurisdiction_code: Mapped[str] = mapped_column(String(16), nullable=False)
    tax_type_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scope_envelope: Mapped[dict] = mapped_column(JSONB, nullable=False)
    requested_by_actor_type: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_by_actor_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    force_replay: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    include_canonical_text: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    include_rendered_citation_text: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
