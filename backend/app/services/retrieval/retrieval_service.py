"""Deterministic legal object retrieval service."""

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.services.legal_object_persistence.integrity_hash import (
    build_object_identifier,
    compute_content_integrity_hash,
    verify_text_hash,
)
from app.services.retrieval.exceptions import (
    InvalidEffectiveDateError,
    LegalObjectNotFoundError,
    LegalObjectRetrievalError,
    RetrievalIntegrityError,
)
from app.services.retrieval.filters import (
    apply_deterministic_order,
    apply_effective_date_filter,
    apply_request_filters,
    apply_status_filter,
    validate_effective_on,
)
from app.services.retrieval.models import LegalObjectRetrievalRequest, LegalObjectRetrievalResult


class LegalObjectRetrievalService:
    """Canonical deterministic retrieval over persisted legal objects."""

    def retrieve(
        self,
        db: Session,
        request: LegalObjectRetrievalRequest,
    ) -> list[LegalObjectRetrievalResult]:
        validate_effective_on(request.effective_on)
        query = db.query(LegalObject, LegalObjectVersion)
        query = apply_effective_date_filter(query, request.effective_on)
        query = apply_request_filters(db, query, request)
        query = apply_status_filter(
            query,
            include_superseded=request.include_superseded,
            include_archived=request.include_archived,
        )
        query = apply_deterministic_order(query)
        rows = query.offset(request.offset).limit(request.limit).all()
        return [self._to_result(legal_object, version) for legal_object, version in rows]

    def retrieve_by_id(
        self,
        db: Session,
        legal_object_id: str,
        *,
        effective_on: date | None = None,
        include_superseded: bool = False,
        include_archived: bool = False,
    ) -> LegalObjectRetrievalResult:
        validate_effective_on(effective_on)
        query = db.query(LegalObject, LegalObjectVersion).filter(
            LegalObject.legal_object_id == legal_object_id
        )
        query = apply_effective_date_filter(query, effective_on)
        query = apply_status_filter(
            query,
            include_superseded=include_superseded,
            include_archived=include_archived,
        )
        row = query.first()
        if row is None:
            raise LegalObjectNotFoundError(legal_object_id)
        legal_object, version = row
        return self._to_result(legal_object, version)

    def retrieve_active(
        self,
        db: Session,
        request: LegalObjectRetrievalRequest,
    ) -> list[LegalObjectRetrievalResult]:
        validate_effective_on(request.effective_on)
        query = db.query(LegalObject, LegalObjectVersion)
        query = apply_effective_date_filter(query, request.effective_on)
        query = apply_request_filters(db, query, request)
        query = apply_status_filter(
            query,
            include_superseded=False,
            include_archived=False,
            active_only=True,
        )
        query = apply_deterministic_order(query)
        rows = query.offset(request.offset).limit(request.limit).all()
        return [self._to_result(legal_object, version) for legal_object, version in rows]

    def retrieve_effective(
        self,
        db: Session,
        effective_on: date,
        request: LegalObjectRetrievalRequest,
    ) -> list[LegalObjectRetrievalResult]:
        if effective_on is None:
            raise InvalidEffectiveDateError("effective_on is required for retrieve_effective")
        validate_effective_on(effective_on)
        effective_request = request.model_copy(update={"effective_on": effective_on})
        return self.retrieve(db, effective_request)

    def _to_result(
        self,
        legal_object: LegalObject,
        version: LegalObjectVersion,
    ) -> LegalObjectRetrievalResult:
        if version.source_version_id is None:
            raise RetrievalIntegrityError(
                legal_object.legal_object_id,
                "source_version_id is required for traceability",
            )
        if legal_object.source_document_id is None:
            raise RetrievalIntegrityError(
                legal_object.legal_object_id,
                "source_document_id is required for traceability",
            )

        object_identifier = build_object_identifier(
            structural_unit_id=version.structural_unit_id,
            object_label=version.object_label,
        )
        canonical_text = version.raw_text

        if not verify_text_hash(raw_text=canonical_text, text_hash=version.text_hash):
            raise RetrievalIntegrityError(
                legal_object.legal_object_id,
                "text_hash does not match canonical_text",
            )

        integrity_hash = compute_content_integrity_hash(
            source_version_id=str(version.source_version_id),
            object_type=legal_object.object_type,
            object_identifier=object_identifier,
            canonical_text=canonical_text,
            effective_from=version.effective_from,
            effective_to=version.effective_to,
        )

        return LegalObjectRetrievalResult(
            legal_object_id=legal_object.legal_object_id,
            source_document_id=legal_object.source_document_id,
            source_version_id=version.source_version_id,
            object_type=legal_object.object_type,
            object_identifier=object_identifier,
            status=legal_object.status,
            effective_from=version.effective_from,
            effective_to=version.effective_to,
            canonical_text=canonical_text,
            integrity_hash=integrity_hash,
            text_hash=version.text_hash,
            retrieval_timestamp=utc_now(),
        )
