import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class ParsedStructure(Base):
    """Immutable snapshot of parser output tied to a parser run."""

    __tablename__ = "parsed_structures"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    parser_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parser_runs.id"),
        nullable=False,
    )
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_versions.id"),
        nullable=False,
    )
    structure_type: Mapped[str] = mapped_column(String(64), nullable=False)
    structure_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    structure_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    parser_run = relationship("ParserRun", back_populates="parsed_structures")
    source_version = relationship("SourceVersion")
