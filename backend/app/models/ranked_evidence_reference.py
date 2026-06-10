import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import utc_now
from app.models.base.base import Base


class RankedEvidenceReference(Base):
    __tablename__ = "ranked_evidence_references"
    __table_args__ = (
        ForeignKeyConstraint(
            ["retrieval_result_id", "retrieval_evidence_reference_id"],
            [
                "retrieval_evidence_references.retrieval_result_id",
                "retrieval_evidence_references.id",
            ],
            name="fk_ranked_evidence_composite_membership",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    ranking_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ranking_results.id"),
        nullable=False,
    )
    retrieval_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("retrieval_results.id"),
        nullable=False,
    )
    retrieval_evidence_reference_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("retrieval_evidence_references.id"),
        nullable=False,
    )
    presentation_order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
