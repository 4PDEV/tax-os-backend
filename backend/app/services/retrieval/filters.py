"""Deterministic query filters for legal object retrieval."""

from datetime import date

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query, Session

from app.models.country import Country
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.models.tax_type import TaxType
from app.services.legal_object_persistence.status_enums import LegalObjectStatus
from app.services.retrieval.exceptions import (
    InvalidEffectiveDateError,
    LegalObjectRetrievalError,
)
from app.services.retrieval.models import LegalObjectRetrievalRequest


def validate_effective_on(effective_on: date | None) -> date | None:
    if effective_on is None:
        return None
    return effective_on


def version_effective_on_clause(effective_on: date):
    """SQLAlchemy clause: version effective on a given date."""
    return and_(
        or_(
            LegalObjectVersion.effective_from.is_(None),
            LegalObjectVersion.effective_from <= effective_on,
        ),
        or_(
            LegalObjectVersion.effective_to.is_(None),
            LegalObjectVersion.effective_to >= effective_on,
        ),
    )


def python_version_effective_on(
    *,
    effective_from: date | None,
    effective_to: date | None,
    effective_on: date,
) -> bool:
    start_ok = effective_from is None or effective_from <= effective_on
    end_ok = effective_to is None or effective_to >= effective_on
    return start_ok and end_ok


def excluded_statuses(
    *,
    include_superseded: bool,
    include_archived: bool,
) -> set[str]:
    excluded = {LegalObjectStatus.REJECTED.value}
    if not include_archived:
        excluded.add(LegalObjectStatus.ARCHIVED.value)
    if not include_superseded:
        excluded.add(LegalObjectStatus.SUPERSEDED.value)
    return excluded


def apply_status_filter(
    query: Query,
    *,
    include_superseded: bool,
    include_archived: bool,
    active_only: bool = False,
) -> Query:
    if active_only:
        return query.filter(LegalObject.status == LegalObjectStatus.ACTIVE.value)

    excluded = excluded_statuses(
        include_superseded=include_superseded,
        include_archived=include_archived,
    )
    if excluded:
        query = query.filter(LegalObject.status.notin_(sorted(excluded)))
    return query


def apply_effective_date_filter(query: Query, effective_on: date | None) -> Query:
    if effective_on is None:
        return query.join(
            LegalObjectVersion,
            LegalObject.current_version_id == LegalObjectVersion.legal_object_version_id,
        )
    return query.join(LegalObjectVersion, LegalObject.legal_object_id == LegalObjectVersion.legal_object_id).filter(
        version_effective_on_clause(effective_on)
    )


def apply_request_filters(db: Session, query: Query, request: LegalObjectRetrievalRequest) -> Query:
    if request.effective_on is not None:
        try:
            validate_effective_on(request.effective_on)
        except (TypeError, ValueError) as exc:
            raise InvalidEffectiveDateError(str(exc)) from exc

    query = (
        query.join(Country, LegalObject.country_id == Country.id)
        .filter(Country.code == request.jurisdiction_code)
    )

    if request.tax_type_code is not None:
        query = query.join(TaxType, LegalObject.tax_type_id == TaxType.id).filter(
            TaxType.code == request.tax_type_code
        )

    if request.source_document_id is not None:
        query = query.filter(LegalObject.source_document_id == request.source_document_id)

    if request.source_version_id is not None:
        query = query.filter(LegalObjectVersion.source_version_id == request.source_version_id)

    if request.legal_object_type is not None:
        query = query.filter(LegalObject.object_type == request.legal_object_type)

    if request.object_identifier is not None:
        structural_unit_id, separator, object_label = request.object_identifier.partition(":")
        if not separator:
            raise LegalObjectRetrievalError(
                "object_identifier must use format structural_unit_id:object_label"
            )
        query = query.filter(
            LegalObjectVersion.structural_unit_id == structural_unit_id,
            LegalObjectVersion.object_label == object_label,
        )

    return query


def apply_deterministic_order(query: Query) -> Query:
    return query.order_by(
        LegalObjectVersion.effective_from.asc().nullsfirst(),
        LegalObjectVersion.structural_unit_id.asc(),
        LegalObjectVersion.object_label.asc(),
        LegalObjectVersion.created_at.asc(),
        LegalObject.legal_object_id.asc(),
    )
