import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class FetchRequest(Base):
    __tablename__ = "fetch_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    monitoring_candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monitoring_candidates.id"),
        nullable=True,
    )
    source_allowlist_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_allowlist_entries.id"),
        nullable=True,
    )
    requested_url: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by_actor_type: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_by_actor_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    request_reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    local_fixture_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
