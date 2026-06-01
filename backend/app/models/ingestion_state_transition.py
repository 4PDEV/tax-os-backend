import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class IngestionStateTransition(Base):
    """Append-only operational ingestion pipeline state history.

    Distinct from ``source_versions.ingestion_status`` (worker/queue workflow).
    """

    __tablename__ = "ingestion_state_transitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_versions.id"),
        nullable=False,
    )
    pipeline_state: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_pipeline_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extraction_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extraction_runs.id"),
        nullable=True,
    )
    parser_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parser_runs.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    source_version = relationship("SourceVersion")
