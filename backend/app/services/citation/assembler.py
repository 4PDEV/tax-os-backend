"""Assemble deterministic citations from legal objects and pinned source versions."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.models.source_document import SourceDocument
from app.models.source_version import SourceVersion
from app.services.citation.authority import resolve_authority_type
from app.services.citation.contract import ASSEMBLER_VERSION
from app.services.citation.exceptions import (
    LegalObjectVersionMismatchError,
    MissingLocationReferenceError,
    MissingSourceVersionError,
    SourceDocumentMismatchError,
)
from app.services.citation.formatter import CitationFormatter
from app.services.citation.hash import citation_id_from_hash, compute_citation_hash
from app.services.citation.location import build_location_reference
from app.services.citation.models import CitationAssemblyRequest, CitationResult


class CitationAssembler:
    """Construct source-backed citations — assembly only, no legal reasoning."""

    def __init__(self, formatter: CitationFormatter | None = None):
        self._formatter = formatter or CitationFormatter()

    def assemble(
        self,
        db: Session,
        legal_object: LegalObject,
        *,
        legal_object_version_id: UUID,
    ) -> CitationResult:
        """Assemble a citation for a legal object at an explicit version pin."""
        version = self._load_version(
            db,
            legal_object_id=legal_object.legal_object_id,
            legal_object_version_id=legal_object_version_id,
        )
        return self._assemble_from_version(db, legal_object, version)

    def assemble_by_request(
        self,
        db: Session,
        request: CitationAssemblyRequest,
    ) -> CitationResult:
        legal_object = (
            db.query(LegalObject)
            .filter(LegalObject.legal_object_id == request.legal_object_id)
            .first()
        )
        if legal_object is None:
            raise MissingSourceVersionError(
                f"legal object not found: {request.legal_object_id}"
            )
        return self.assemble(
            db,
            legal_object,
            legal_object_version_id=request.legal_object_version_id,
        )

    def _load_version(
        self,
        db: Session,
        *,
        legal_object_id: str,
        legal_object_version_id: UUID,
    ) -> LegalObjectVersion:
        version = (
            db.query(LegalObjectVersion)
            .filter(LegalObjectVersion.legal_object_version_id == legal_object_version_id)
            .first()
        )
        if version is None:
            raise MissingSourceVersionError(
                f"legal object version not found: {legal_object_version_id}"
            )
        if version.legal_object_id != legal_object_id:
            raise LegalObjectVersionMismatchError(
                "legal_object_version_id does not belong to legal_object_id"
            )
        if version.source_version_id is None:
            raise MissingSourceVersionError("source_version_id is required for citation assembly")
        return version

    def _assemble_from_version(
        self,
        db: Session,
        legal_object: LegalObject,
        version: LegalObjectVersion,
    ) -> CitationResult:
        try:
            location_reference = build_location_reference(
                object_type=legal_object.object_type,
                object_label=version.object_label,
            )
        except ValueError as exc:
            raise MissingLocationReferenceError(str(exc)) from exc

        source_version = (
            db.query(SourceVersion)
            .filter(SourceVersion.id == version.source_version_id)
            .first()
        )
        if source_version is None:
            raise MissingSourceVersionError(
                f"source version not found: {version.source_version_id}"
            )

        if source_version.source_document_id != legal_object.source_document_id:
            raise SourceDocumentMismatchError(
                "source_version.source_document_id does not match legal_object.source_document_id"
            )

        document = (
            db.query(SourceDocument)
            .filter(SourceDocument.id == legal_object.source_document_id)
            .first()
        )
        if document is None:
            raise MissingSourceVersionError(
                f"source document not found: {legal_object.source_document_id}"
            )

        authority_type = resolve_authority_type(
            source_type=document.source_type,
            authority_level=document.authority_level,
        )

        citation_hash = compute_citation_hash(
            source_version_id=source_version.id,
            legal_object_id=legal_object.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            location_reference=location_reference,
        )

        effective_from = version.effective_from
        effective_to = version.effective_to
        source_version_effective_from = source_version.effective_from
        source_version_effective_to = source_version.effective_to
        publication_date = source_version.publication_date

        citation_text = self._formatter.format(
            source_title=document.title,
            location_reference=location_reference,
            authority_type=authority_type,
            version_label=source_version.version_label,
            effective_from=effective_from,
            source_version_effective_from=source_version_effective_from,
            source_version_effective_to=source_version_effective_to,
            official_reference=document.official_reference,
        )

        assembled_at = utc_now()
        return CitationResult(
            citation_id=citation_id_from_hash(citation_hash),
            source_document_id=document.id,
            source_version_id=source_version.id,
            legal_object_id=legal_object.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            authority_type=authority_type,
            source_title=document.title,
            official_reference=document.official_reference,
            publication_date=publication_date,
            effective_from=effective_from,
            effective_to=effective_to,
            source_version_effective_from=source_version_effective_from,
            source_version_effective_to=source_version_effective_to,
            location_reference=location_reference,
            citation_text=citation_text,
            citation_hash=citation_hash,
            assembled_at=assembled_at,
            assembler_version=ASSEMBLER_VERSION,
        )
