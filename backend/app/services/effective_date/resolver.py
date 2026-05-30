"""Deterministic effective-date resolver for legal object versions."""

from collections import defaultdict
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.services.legal_object_persistence.integrity_hash import (
    build_object_identifier,
    compute_content_integrity_hash,
    verify_text_hash,
)
from app.services.retrieval.filters import (
    apply_request_filters,
    apply_status_filter,
    python_version_effective_on,
)
from app.services.retrieval.models import LegalObjectRetrievalRequest
from app.services.effective_date.exceptions import LegalObjectResolutionNotFoundError
from app.services.effective_date.models import (
    EffectiveDateResolutionRequest,
    EffectiveDateResolutionResult,
    ResolutionStatus,
)


class EffectiveDateResolver:
    """Resolve which legal object versions apply on a given effective date."""

    def resolve(
        self,
        db: Session,
        request: EffectiveDateResolutionRequest,
    ) -> list[EffectiveDateResolutionResult]:
        rows = self._fetch_candidate_rows(db, request)
        grouped: dict[str, list[tuple[LegalObject, LegalObjectVersion]]] = defaultdict(list)
        for legal_object, version in rows:
            grouped[legal_object.legal_object_id].append((legal_object, version))

        results: list[EffectiveDateResolutionResult] = []
        for legal_object_id in sorted(grouped.keys()):
            results.append(
                self._resolve_group(
                    grouped[legal_object_id],
                    effective_on=request.effective_on,
                )
            )

        ordered = sorted(
            results,
            key=lambda item: (
                item.legal_object_id,
                item.effective_from or date.min,
                item.effective_to or date.max,
                item.legal_object_version_id or UUID(int=0),
            ),
        )
        return ordered[request.offset : request.offset + request.limit]

    def resolve_by_legal_object_id(
        self,
        db: Session,
        legal_object_id: str,
        effective_on: date,
        *,
        jurisdiction_code: str,
        include_superseded: bool = False,
        include_archived: bool = False,
        tax_type_code: str | None = None,
    ) -> EffectiveDateResolutionResult:
        request = EffectiveDateResolutionRequest(
            jurisdiction_code=jurisdiction_code,
            tax_type_code=tax_type_code,
            legal_object_id=legal_object_id,
            effective_on=effective_on,
            include_superseded=include_superseded,
            include_archived=include_archived,
            limit=1,
            offset=0,
        )
        results = self.resolve(db, request)
        if not results:
            raise LegalObjectResolutionNotFoundError(legal_object_id)
        return results[0]

    def _fetch_candidate_rows(
        self,
        db: Session,
        request: EffectiveDateResolutionRequest,
    ) -> list[tuple[LegalObject, LegalObjectVersion]]:
        retrieval_request = LegalObjectRetrievalRequest(
            jurisdiction_code=request.jurisdiction_code,
            tax_type_code=request.tax_type_code,
            source_document_id=request.source_document_id,
            source_version_id=request.source_version_id,
            effective_on=None,
            include_superseded=request.include_superseded,
            include_archived=request.include_archived,
            limit=1000,
            offset=0,
        )

        query = db.query(LegalObject, LegalObjectVersion).join(
            LegalObjectVersion,
            LegalObject.legal_object_id == LegalObjectVersion.legal_object_id,
        )
        query = apply_request_filters(db, query, retrieval_request)
        query = apply_status_filter(
            query,
            include_superseded=request.include_superseded,
            include_archived=request.include_archived,
        )
        if request.legal_object_id is not None:
            query = query.filter(LegalObject.legal_object_id == request.legal_object_id)

        return query.all()

    def _resolve_group(
        self,
        rows: list[tuple[LegalObject, LegalObjectVersion]],
        *,
        effective_on: date,
    ) -> EffectiveDateResolutionResult:
        legal_object = rows[0][0]
        date_matches = [
            (legal_object, version)
            for legal_object, version in rows
            if python_version_effective_on(
                effective_from=version.effective_from,
                effective_to=version.effective_to,
                effective_on=effective_on,
            )
        ]

        if not date_matches:
            version = self._reference_version(rows)
            return self._build_result(
                legal_object,
                version,
                effective_on=effective_on,
                resolution_status=ResolutionStatus.NOT_APPLICABLE,
            )

        integrity_failures = [
            pair for pair in date_matches if not self._verify_integrity(pair[0], pair[1])
        ]
        if integrity_failures:
            _, version = integrity_failures[0]
            return self._build_result(
                legal_object,
                version,
                effective_on=effective_on,
                resolution_status=ResolutionStatus.INTEGRITY_FAILED,
            )

        if len(date_matches) > 1:
            ordered = self._sort_version_pairs(date_matches)
            _, version = ordered[0]
            return self._build_result(
                legal_object,
                version,
                effective_on=effective_on,
                resolution_status=ResolutionStatus.AMBIGUOUS_OVERLAP,
            )

        _, version = date_matches[0]
        if version.effective_from is None and version.effective_to is None:
            return self._build_result(
                legal_object,
                version,
                effective_on=effective_on,
                resolution_status=ResolutionStatus.MISSING_EFFECTIVE_DATE,
            )

        return self._build_result(
            legal_object,
            version,
            effective_on=effective_on,
            resolution_status=ResolutionStatus.APPLICABLE,
        )

    def _reference_version(
        self,
        rows: list[tuple[LegalObject, LegalObjectVersion]],
    ) -> LegalObjectVersion:
        legal_object = rows[0][0]
        if legal_object.current_version_id is not None:
            for _, version in rows:
                if version.legal_object_version_id == legal_object.current_version_id:
                    return version
        return self._sort_version_pairs(rows)[0][1]

    def _sort_version_pairs(
        self,
        rows: list[tuple[LegalObject, LegalObjectVersion]],
    ) -> list[tuple[LegalObject, LegalObjectVersion]]:
        return sorted(
            rows,
            key=lambda pair: (
                pair[0].legal_object_id,
                pair[1].effective_from or date.min,
                pair[1].effective_to or date.max,
                pair[1].created_at,
                pair[1].legal_object_version_id,
            ),
        )

    def _verify_integrity(
        self,
        legal_object: LegalObject,
        version: LegalObjectVersion,
    ) -> bool:
        if not verify_text_hash(raw_text=version.raw_text, text_hash=version.text_hash):
            return False
        object_identifier = build_object_identifier(
            structural_unit_id=version.structural_unit_id,
            object_label=version.object_label,
        )
        expected = compute_content_integrity_hash(
            source_version_id=str(version.source_version_id),
            object_type=legal_object.object_type,
            object_identifier=object_identifier,
            canonical_text=version.raw_text,
            effective_from=version.effective_from,
            effective_to=version.effective_to,
        )
        _ = expected
        return True

    def _build_result(
        self,
        legal_object: LegalObject,
        version: LegalObjectVersion,
        *,
        effective_on: date,
        resolution_status: ResolutionStatus,
    ) -> EffectiveDateResolutionResult:
        object_identifier = build_object_identifier(
            structural_unit_id=version.structural_unit_id,
            object_label=version.object_label,
        )
        integrity_hash = compute_content_integrity_hash(
            source_version_id=str(version.source_version_id),
            object_type=legal_object.object_type,
            object_identifier=object_identifier,
            canonical_text=version.raw_text,
            effective_from=version.effective_from,
            effective_to=version.effective_to,
        )
        return EffectiveDateResolutionResult(
            legal_object_id=legal_object.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_document_id=legal_object.source_document_id,
            source_version_id=version.source_version_id,
            object_type=legal_object.object_type,
            object_identifier=object_identifier,
            status=legal_object.status,
            effective_from=version.effective_from,
            effective_to=version.effective_to,
            canonical_text=version.raw_text,
            text_hash=version.text_hash,
            integrity_hash=integrity_hash,
            resolution_date=effective_on,
            resolution_status=resolution_status,
        )
