import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class RankingRequest(Base):
    __tablename__ = "ranking_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    ranking_request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    retrieval_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("retrieval_results.id"),
        nullable=False,
    )
    ranking_profile: Mapped[str] = mapped_column(String(64), nullable=False)
    contract_version: Mapped[str] = mapped_column(String(32), nullable=False)
    requested_by_actor_type: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_by_actor_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    force_replay: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
