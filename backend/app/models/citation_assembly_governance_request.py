import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class CitationAssemblyGovernanceRequest(Base):
    __tablename__ = "citation_assembly_governance_requests"

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
    legal_object_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("legal_object_versions.legal_object_version_id"),
        nullable=False,
    )
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_versions.id"),
        nullable=False,
    )
    citation_reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by_actor_type: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_by_actor_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    force_reassembly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
