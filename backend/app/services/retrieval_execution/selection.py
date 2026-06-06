"""Version selection for controlled retrieval — legal_object_version dates only."""

from datetime import date
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.country import Country
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.models.retrieval_request import RetrievalRequest
from app.models.source_version import SourceVersion
from app.models.tax_type import TaxType


class RetrievalSelectionError(Exception):
    def __init__(self, category: str, message: str):
        self.category = category
        self.message = message
        super().__init__(message)


def version_effective_on_clause(effective_on: date):
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


def _version_matches_scope(
    db: Session,
    version: LegalObjectVersion,
    request: RetrievalRequest,
) -> bool:
    scope = request.scope_envelope or {}
    legal_object = db.get(LegalObject, version.legal_object_id)
    if legal_object is None:
        return False

    country = db.get(Country, legal_object.country_id)
    if country is None or country.code != request.jurisdiction_code:
        return False

    if request.tax_type_code is not None:
        if legal_object.tax_type_id is None:
            return False
        tax_type = db.get(TaxType, legal_object.tax_type_id)
        if tax_type is None or tax_type.code != request.tax_type_code:
            return False

    legal_object_id = scope.get("legal_object_id")
    if legal_object_id is not None and legal_object_id != version.legal_object_id:
        return False

    object_type = scope.get("legal_object_type")
    if object_type is not None and object_type != legal_object.object_type:
        return False

    source_document_id = scope.get("source_document_id")
    if source_document_id is not None:
        if str(legal_object.source_document_id) != str(source_document_id):
            return False

    source_version_id = scope.get("source_version_id")
    if source_version_id is not None and str(version.source_version_id) != str(source_version_id):
        return False

    object_identifier = scope.get("object_identifier")
    if object_identifier is not None:
        expected = f"{version.structural_unit_id}:{version.object_label}"
        if object_identifier != expected:
            return False

    return True


def _base_version_query(db: Session, request: RetrievalRequest):
    return (
        select(LegalObjectVersion)
        .join(LegalObject, LegalObjectVersion.legal_object_id == LegalObject.legal_object_id)
        .join(Country, LegalObject.country_id == Country.id)
        .where(Country.code == request.jurisdiction_code)
    )


def _apply_scope_sql_filters(stmt, request: RetrievalRequest):
    scope = request.scope_envelope or {}
    if request.tax_type_code is not None:
        stmt = stmt.join(TaxType, LegalObject.tax_type_id == TaxType.id).where(
            TaxType.code == request.tax_type_code
        )
    legal_object_id = scope.get("legal_object_id")
    if legal_object_id is not None:
        stmt = stmt.where(LegalObject.legal_object_id == legal_object_id)
    object_type = scope.get("legal_object_type")
    if object_type is not None:
        stmt = stmt.where(LegalObject.object_type == object_type)
    source_document_id = scope.get("source_document_id")
    if source_document_id is not None:
        stmt = stmt.where(LegalObject.source_document_id == source_document_id)
    source_version_id = scope.get("source_version_id")
    if source_version_id is not None:
        stmt = stmt.where(LegalObjectVersion.source_version_id == source_version_id)
    object_identifier = scope.get("object_identifier")
    if object_identifier is not None:
        structural_unit_id, separator, object_label = object_identifier.partition(":")
        if not separator:
            raise RetrievalSelectionError(
                "invalid_request",
                "object_identifier must use format structural_unit_id:object_label",
            )
        stmt = stmt.where(
            LegalObjectVersion.structural_unit_id == structural_unit_id,
            LegalObjectVersion.object_label == object_label,
        )
    return stmt


def select_versions_as_of_date(db: Session, request: RetrievalRequest) -> list[LegalObjectVersion]:
    if request.as_of_date is None:
        raise RetrievalSelectionError(
            "temporal_scope_missing",
            "as_of_date is required for AS_OF_DATE retrieval_mode",
        )
    stmt = _base_version_query(db, request)
    stmt = _apply_scope_sql_filters(stmt, request)
    stmt = stmt.where(version_effective_on_clause(request.as_of_date))
    return list(db.execute(stmt).scalars().all())


def select_version_exact(db: Session, request: RetrievalRequest) -> list[LegalObjectVersion]:
    if request.legal_object_version_id is None:
        raise RetrievalSelectionError(
            "temporal_scope_missing",
            "legal_object_version_id is required for EXACT_VERSION retrieval_mode",
        )
    version = db.get(LegalObjectVersion, request.legal_object_version_id)
    if version is None:
        return []
    if not _version_matches_scope(db, version, request):
        return []
    return [version]


def select_versions_latest(db: Session, request: RetrievalRequest) -> list[LegalObjectVersion]:
    stmt = (
        select(LegalObjectVersion)
        .join(LegalObject, LegalObject.current_version_id == LegalObjectVersion.legal_object_version_id)
        .join(Country, LegalObject.country_id == Country.id)
        .where(
            Country.code == request.jurisdiction_code,
            LegalObject.current_version_id.isnot(None),
        )
    )
    stmt = _apply_scope_sql_filters(stmt, request)
    return list(db.execute(stmt).scalars().all())


def select_versions_for_request(db: Session, request: RetrievalRequest) -> list[LegalObjectVersion]:
    mode = request.retrieval_mode
    if mode == "AS_OF_DATE":
        return select_versions_as_of_date(db, request)
    if mode == "EXACT_VERSION":
        return select_version_exact(db, request)
    if mode == "LATEST_VERSION":
        return select_versions_latest(db, request)
    raise RetrievalSelectionError("invalid_request", f"unsupported retrieval_mode: {mode}")
