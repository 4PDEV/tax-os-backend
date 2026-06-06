import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class RetrievalEvidenceReference(Base):
    __tablename__ = "retrieval_evidence_references"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    retrieval_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("retrieval_results.id"),
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
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_versions.id"),
        nullable=False,
    )
    citation_id: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("citations.citation_id"),
        nullable=True,
    )
    citation_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    location_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    object_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deterministic_order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
