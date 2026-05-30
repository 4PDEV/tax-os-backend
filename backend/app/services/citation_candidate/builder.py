"""Build citation-ready candidate DTOs from retrieval and resolution results."""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.country import Country
from app.models.legal_object_version import LegalObjectVersion
from app.models.source_document import SourceDocument
from app.models.source_version import SourceVersion
from app.models.tax_type import TaxType
from app.services.effective_date.models import (
    EffectiveDateResolutionRequest,
    EffectiveDateResolutionResult,
    ResolutionStatus,
)
from app.services.effective_date.resolver import EffectiveDateResolver
from app.services.legal_object_persistence.integrity_hash import verify_text_hash
from app.services.retrieval.models import LegalObjectRetrievalRequest, LegalObjectRetrievalResult
from app.services.retrieval.retrieval_service import LegalObjectRetrievalService
from app.services.citation_candidate.models import (
    CandidateStatus,
    CitationCandidate,
    CitationCandidateRequest,
)


@dataclass(frozen=True)
class _SourceContext:
    jurisdiction_code: str
    tax_type_code: str | None
    source_type: str
    authority_level: str
    source_title: str
    source_short_title: str | None
    issuing_authority: str | None
    official_reference: str | None
    source_url: str | None
    language: str | None
    publication_date: date | None
    retrieved_at: datetime | None


_RESOLUTION_TO_CANDIDATE_STATUS: dict[ResolutionStatus, CandidateStatus] = {
    ResolutionStatus.APPLICABLE: CandidateStatus.READY,
    ResolutionStatus.AMBIGUOUS_OVERLAP: CandidateStatus.DATE_AMBIGUOUS,
    ResolutionStatus.NOT_APPLICABLE: CandidateStatus.DATE_NOT_APPLICABLE,
    ResolutionStatus.MISSING_EFFECTIVE_DATE: CandidateStatus.MISSING_EFFECTIVE_DATE,
    ResolutionStatus.INTEGRITY_FAILED: CandidateStatus.INTEGRITY_FAILED,
}


class CitationCandidateBuilder:
    """Prepare citation candidate DTOs without final citation formatting."""

    def __init__(
        self,
        retrieval_service: LegalObjectRetrievalService | None = None,
        resolver: EffectiveDateResolver | None = None,
    ):
        self._retrieval = retrieval_service or LegalObjectRetrievalService()
        self._resolver = resolver or EffectiveDateResolver()

    def build(
        self,
        db: Session,
        request: CitationCandidateRequest,
    ) -> list[CitationCandidate]:
        if request.effective_on is not None:
            resolution_request = EffectiveDateResolutionRequest(
                jurisdiction_code=request.jurisdiction_code,
                tax_type_code=request.tax_type_code,
                legal_object_id=request.legal_object_id,
                source_document_id=request.source_document_id,
                source_version_id=request.source_version_id,
                effective_on=request.effective_on,
                include_superseded=request.include_superseded,
                include_archived=request.include_archived,
                limit=request.limit,
                offset=request.offset,
            )
            results = self._resolver.resolve(db, resolution_request)
            return [
                self.build_from_resolution_result(db, request, result) for result in results
            ]

        retrieval_request = LegalObjectRetrievalRequest(
            jurisdiction_code=request.jurisdiction_code,
            tax_type_code=request.tax_type_code,
            source_document_id=request.source_document_id,
            source_version_id=request.source_version_id,
            legal_object_type=None,
            object_identifier=None,
            effective_on=None,
            include_superseded=request.include_superseded,
            include_archived=request.include_archived,
            limit=request.limit,
            offset=request.offset,
        )
        if request.legal_object_id is not None:
            result = self._retrieval.retrieve_by_id(
                db,
                request.legal_object_id,
                include_superseded=request.include_superseded,
                include_archived=request.include_archived,
            )
            return [self.build_from_retrieval_result(db, request, result)]

        results = self._retrieval.retrieve(db, retrieval_request)
        return [self.build_from_retrieval_result(db, request, result) for result in results]

    def build_from_retrieval_result(
        self,
        db: Session,
        request: CitationCandidateRequest,
        result: LegalObjectRetrievalResult,
    ) -> CitationCandidate:
        version_id = self._resolve_version_id(db, result.legal_object_id, result.text_hash)
        if version_id is None:
            return self._failed_candidate(
                request=request,
                result=result,
                legal_object_version_id=UUID(int=0),
                candidate_status=CandidateStatus.SOURCE_TRACEABILITY_FAILED,
            )

        if not verify_text_hash(raw_text=result.canonical_text, text_hash=result.text_hash):
            return self._failed_candidate(
                request=request,
                result=result,
                legal_object_version_id=version_id,
                candidate_status=CandidateStatus.INTEGRITY_FAILED,
            )

        try:
            source_context = self._load_source_context(
                db,
                source_document_id=result.source_document_id,
                source_version_id=result.source_version_id,
                jurisdiction_code=request.jurisdiction_code,
                tax_type_code=request.tax_type_code,
            )
        except ValueError:
            return self._failed_candidate(
                request=request,
                result=result,
                legal_object_version_id=version_id,
                candidate_status=CandidateStatus.SOURCE_TRACEABILITY_FAILED,
            )

        return self._assemble_candidate(
            request=request,
            result=result,
            legal_object_version_id=version_id,
            source_context=source_context,
            candidate_status=CandidateStatus.READY,
        )

    def build_from_resolution_result(
        self,
        db: Session,
        request: CitationCandidateRequest,
        result: EffectiveDateResolutionResult,
    ) -> CitationCandidate:
        candidate_status = _RESOLUTION_TO_CANDIDATE_STATUS[result.resolution_status]
        retrieval_like = LegalObjectRetrievalResult(
            legal_object_id=result.legal_object_id,
            source_document_id=result.source_document_id,
            source_version_id=result.source_version_id,
            object_type=result.object_type,
            object_identifier=result.object_identifier,
            status=result.status,
            effective_from=result.effective_from,
            effective_to=result.effective_to,
            canonical_text=result.canonical_text,
            integrity_hash=result.integrity_hash,
            text_hash=result.text_hash,
            retrieval_timestamp=utc_now(),
        )

        version_id = result.legal_object_version_id or self._resolve_version_id(
            db,
            result.legal_object_id,
            result.text_hash,
        )
        if version_id is None:
            return self._failed_candidate(
                request=request,
                result=retrieval_like,
                legal_object_version_id=UUID(int=0),
                candidate_status=CandidateStatus.SOURCE_TRACEABILITY_FAILED,
            )

        if candidate_status == CandidateStatus.READY:
            if not verify_text_hash(raw_text=result.canonical_text, text_hash=result.text_hash):
                candidate_status = CandidateStatus.INTEGRITY_FAILED
            else:
                try:
                    source_context = self._load_source_context(
                        db,
                        source_document_id=result.source_document_id,
                        source_version_id=result.source_version_id,
                        jurisdiction_code=request.jurisdiction_code,
                        tax_type_code=request.tax_type_code,
                    )
                except ValueError:
                    candidate_status = CandidateStatus.SOURCE_TRACEABILITY_FAILED
                else:
                    return self._assemble_candidate(
                        request=request,
                        result=retrieval_like,
                        legal_object_version_id=version_id,
                        source_context=source_context,
                        candidate_status=candidate_status,
                    )

        return self._failed_candidate(
            request=request,
            result=retrieval_like,
            legal_object_version_id=version_id,
            candidate_status=candidate_status,
            source_context=self._safe_source_context(db, result),
        )

    def _resolve_version_id(
        self,
        db: Session,
        legal_object_id: str,
        text_hash: str,
    ) -> UUID | None:
        version = (
            db.query(LegalObjectVersion)
            .filter(
                LegalObjectVersion.legal_object_id == legal_object_id,
                LegalObjectVersion.text_hash == text_hash,
            )
            .first()
        )
        return version.legal_object_version_id if version is not None else None

    def _load_source_context(
        self,
        db: Session,
        *,
        source_document_id: UUID,
        source_version_id: UUID,
        jurisdiction_code: str,
        tax_type_code: str | None,
    ) -> _SourceContext:
        document = db.query(SourceDocument).filter(SourceDocument.id == source_document_id).first()
        version = db.query(SourceVersion).filter(SourceVersion.id == source_version_id).first()
        if document is None or version is None:
            raise ValueError("source document or version not found")

        country = db.query(Country).filter(Country.id == document.country_id).first()
        if country is None or country.code != jurisdiction_code:
            raise ValueError("jurisdiction linkage failed")

        resolved_tax_type_code = tax_type_code
        if document.tax_type_id is not None:
            tax_type = db.query(TaxType).filter(TaxType.id == document.tax_type_id).first()
            if tax_type is None:
                raise ValueError("tax type linkage failed")
            resolved_tax_type_code = tax_type.code
            if tax_type_code is not None and tax_type.code != tax_type_code:
                raise ValueError("tax type mismatch")

        return _SourceContext(
            jurisdiction_code=country.code,
            tax_type_code=resolved_tax_type_code,
            source_type=document.source_type,
            authority_level=document.authority_level,
            source_title=document.title,
            source_short_title=document.short_title,
            issuing_authority=document.issuing_authority,
            official_reference=document.official_reference,
            source_url=document.source_url,
            language=document.language,
            publication_date=version.publication_date,
            retrieved_at=version.retrieved_at,
        )

    def _load_relaxed_source_context(
        self,
        db: Session,
        *,
        source_document_id: UUID,
        source_version_id: UUID,
    ) -> _SourceContext | None:
        document = db.query(SourceDocument).filter(SourceDocument.id == source_document_id).first()
        version = db.query(SourceVersion).filter(SourceVersion.id == source_version_id).first()
        if document is None or version is None:
            return None

        country = db.query(Country).filter(Country.id == document.country_id).first()
        tax_type_code = None
        if document.tax_type_id is not None:
            tax_type = db.query(TaxType).filter(TaxType.id == document.tax_type_id).first()
            tax_type_code = tax_type.code if tax_type is not None else None

        return _SourceContext(
            jurisdiction_code=country.code if country is not None else "unknown",
            tax_type_code=tax_type_code,
            source_type=document.source_type,
            authority_level=document.authority_level,
            source_title=document.title,
            source_short_title=document.short_title,
            issuing_authority=document.issuing_authority,
            official_reference=document.official_reference,
            source_url=document.source_url,
            language=document.language,
            publication_date=version.publication_date,
            retrieved_at=version.retrieved_at,
        )

    def _safe_source_context(
        self,
        db: Session,
        result: EffectiveDateResolutionResult,
    ) -> _SourceContext | None:
        return self._load_relaxed_source_context(
            db,
            source_document_id=result.source_document_id,
            source_version_id=result.source_version_id,
        )

    def _parse_object_label(self, object_identifier: str) -> str | None:
        _, separator, object_label = object_identifier.partition(":")
        return object_label if separator else None

    def _assemble_candidate(
        self,
        *,
        request: CitationCandidateRequest,
        result: LegalObjectRetrievalResult,
        legal_object_version_id: UUID,
        source_context: _SourceContext,
        candidate_status: CandidateStatus,
    ) -> CitationCandidate:
        return CitationCandidate(
            legal_object_id=result.legal_object_id,
            legal_object_version_id=legal_object_version_id,
            source_document_id=result.source_document_id,
            source_version_id=result.source_version_id,
            jurisdiction_code=source_context.jurisdiction_code,
            tax_type_code=source_context.tax_type_code,
            source_type=source_context.source_type,
            authority_level=source_context.authority_level,
            source_title=source_context.source_title,
            source_short_title=source_context.source_short_title,
            issuing_authority=source_context.issuing_authority,
            official_reference=source_context.official_reference,
            source_url=source_context.source_url,
            language=source_context.language,
            object_type=result.object_type,
            object_identifier=result.object_identifier,
            object_label=self._parse_object_label(result.object_identifier),
            effective_from=result.effective_from,
            effective_to=result.effective_to,
            publication_date=source_context.publication_date,
            retrieved_at=source_context.retrieved_at,
            canonical_text=result.canonical_text,
            text_hash=result.text_hash,
            integrity_hash=result.integrity_hash,
            candidate_created_at=utc_now(),
            candidate_status=candidate_status,
        )

    def _failed_candidate(
        self,
        *,
        request: CitationCandidateRequest,
        result: LegalObjectRetrievalResult,
        legal_object_version_id: UUID,
        candidate_status: CandidateStatus,
        source_context: _SourceContext | None = None,
    ) -> CitationCandidate:
        ctx = source_context
        return CitationCandidate(
            legal_object_id=result.legal_object_id,
            legal_object_version_id=legal_object_version_id,
            source_document_id=result.source_document_id,
            source_version_id=result.source_version_id,
            jurisdiction_code=request.jurisdiction_code,
            tax_type_code=request.tax_type_code,
            source_type=ctx.source_type if ctx else "unknown",
            authority_level=ctx.authority_level if ctx else "unknown",
            source_title=ctx.source_title if ctx else "unknown",
            source_short_title=ctx.source_short_title if ctx else None,
            issuing_authority=ctx.issuing_authority if ctx else None,
            official_reference=ctx.official_reference if ctx else None,
            source_url=ctx.source_url if ctx else None,
            language=ctx.language if ctx else None,
            object_type=result.object_type,
            object_identifier=result.object_identifier,
            object_label=self._parse_object_label(result.object_identifier),
            effective_from=result.effective_from,
            effective_to=result.effective_to,
            publication_date=ctx.publication_date if ctx else None,
            retrieved_at=ctx.retrieved_at if ctx else None,
            canonical_text=result.canonical_text,
            text_hash=result.text_hash,
            integrity_hash=result.integrity_hash,
            candidate_created_at=utc_now(),
            candidate_status=candidate_status,
        )
