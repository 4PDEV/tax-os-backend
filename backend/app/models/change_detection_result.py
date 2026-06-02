import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class ChangeDetectionResult(Base):
    __tablename__ = "change_detection_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    change_detection_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("change_detection_requests.id"),
        nullable=False,
    )
    detection_status: Mapped[str] = mapped_column(String(32), nullable=False)
    change_detected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    change_type: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_diff_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    structural_diff_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)
    review_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    detector_name: Mapped[str] = mapped_column(String(128), nullable=False)
    detector_version: Mapped[str] = mapped_column(String(64), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
