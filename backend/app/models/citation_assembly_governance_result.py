import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class CitationAssemblyGovernanceResult(Base):
    __tablename__ = "citation_assembly_governance_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    citation_assembly_governance_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("citation_assembly_governance_requests.id"),
        nullable=False,
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
    citation_status: Mapped[str] = mapped_column(String(64), nullable=False)
    citation_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assembled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
