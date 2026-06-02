import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class ChangeDetectionRequest(Base):
    __tablename__ = "change_detection_requests"

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
    fetch_result_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fetch_results.id"),
        nullable=True,
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_documents.id"),
        nullable=True,
    )
    source_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_versions.id"),
        nullable=True,
    )
    previous_artifact_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_artifact_reference: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by_actor_type: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_by_actor_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detection_reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
