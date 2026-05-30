"""Shared fixtures for retrieval integration tests."""

from uuid import uuid4

from app.core.datetime_utils import utc_now
from app.models.country import Country
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.models.source_document import SourceDocument
from app.models.source_version import SourceVersion
from app.models.tax_type import TaxType
from app.services.legal_object_convergence.enums import ConvergenceSource, ConvergenceStatus
from app.services.legal_object_convergence.models import ConvergedLegalObjectCandidate
from app.services.legal_object_extraction.enums import LegalObjectExtractionStatus, LegalObjectType
from app.services.legal_object_extraction.identity import generate_legal_object_id, sha256_text
from app.services.legal_object_extraction.models import LegalObjectCandidate
from app.services.legal_object_persistence import LegalObjectPersistenceService
from app.services.legal_object_persistence.status_enums import LegalObjectStatus
from app.services.retrieval.models import LegalObjectRetrievalRequest


def make_candidate(
    *,
    source_version_id: str,
    raw_text: str = "Tax is due on supply.",
    canonical_path: str = "PART I > Section 15",
    object_label: str = "Section 15",
    structural_unit_id: str = "su-0001",
    legal_object_id: str | None = None,
) -> LegalObjectCandidate:
    text_hash = sha256_text(raw_text)
    lid = legal_object_id or generate_legal_object_id(
        source_version_id=source_version_id,
        canonical_path=canonical_path,
        object_type=LegalObjectType.SECTION.value,
        object_label=object_label,
        start_offset=10,
        text_hash=text_hash,
    )
    return LegalObjectCandidate(
        source_version_id=source_version_id,
        legal_object_id=lid,
        object_type=LegalObjectType.SECTION,
        object_label=object_label,
        object_title=None,
        canonical_path=canonical_path,
        parent_legal_object_id=None,
        structural_unit_id=structural_unit_id,
        start_offset=10,
        end_offset=20,
        raw_text=raw_text,
        text_hash=text_hash,
        extraction_status=LegalObjectExtractionStatus.SUCCESS,
        extracted_at=utc_now(),
        extractor_version="1.0.0",
        metadata={},
    )


def make_converged(candidate: LegalObjectCandidate) -> ConvergedLegalObjectCandidate:
    return ConvergedLegalObjectCandidate(
        candidate=candidate,
        source_pipeline=ConvergenceSource.STRUCTURAL_UNIT,
        convergence_status=ConvergenceStatus.CANONICAL,
        warnings=[],
        metadata={},
    )


def seed_source_version(db_session, *, country_code: str = "RW", tax_type_code: str = "VAT"):
    country = Country(code=country_code, name="Rwanda", status="active")
    db_session.add(country)
    db_session.flush()

    tax_type = TaxType(country_id=country.id, code=tax_type_code, name="VAT", status="active")
    db_session.add(tax_type)
    db_session.flush()

    document = SourceDocument(
        country_id=country.id,
        tax_type_id=tax_type.id,
        source_type="law",
        authority_level="national",
        title="VAT Law",
        status="active",
    )
    db_session.add(document)
    db_session.flush()

    version = SourceVersion(
        source_document_id=document.id,
        version_label="v1",
        checksum_sha256="a" * 64,
        storage_path="rw/vat/v1.pdf",
        mime_type="application/pdf",
        file_size=1024,
    )
    db_session.add(version)
    db_session.flush()
    return country, tax_type, document, version


def persist_candidate(db_session, candidate: LegalObjectCandidate) -> LegalObjectCandidate:
    LegalObjectPersistenceService().persist(db_session, make_converged(candidate))
    return candidate


def base_request(**overrides) -> LegalObjectRetrievalRequest:
    defaults = {
        "jurisdiction_code": "RW",
        "tax_type_code": "VAT",
        "limit": 100,
        "offset": 0,
    }
    defaults.update(overrides)
    return LegalObjectRetrievalRequest(**defaults)


def set_object_status(db_session, legal_object_id: str, status: str) -> None:
    obj = db_session.query(LegalObject).filter_by(legal_object_id=legal_object_id).one()
    obj.status = status
    db_session.flush()


def set_version_effective_dates(
    db_session,
    legal_object_id: str,
    *,
    effective_from,
    effective_to,
    version_id=None,
) -> LegalObjectVersion:
    legal_object = db_session.query(LegalObject).filter_by(legal_object_id=legal_object_id).one()
    query = db_session.query(LegalObjectVersion).filter_by(legal_object_id=legal_object_id)
    if version_id is not None:
        version = query.filter_by(legal_object_version_id=version_id).one()
    else:
        version = query.filter_by(legal_object_version_id=legal_object.current_version_id).one()
    version.effective_from = effective_from
    version.effective_to = effective_to
    db_session.flush()
    return version


def add_version_row(
    db_session,
    *,
    legal_object_id: str,
    source_version_id,
    raw_text: str,
    object_label: str,
    structural_unit_id: str,
    effective_from=None,
    effective_to=None,
) -> LegalObjectVersion:
    import uuid

    from app.services.legal_object_persistence.status_enums import LegalObjectVersionStatus

    text_hash = sha256_text(raw_text)
    version = LegalObjectVersion(
        legal_object_version_id=uuid.uuid4(),
        legal_object_id=legal_object_id,
        source_version_id=source_version_id,
        parent_legal_object_id=None,
        structural_unit_id=structural_unit_id,
        object_label=object_label,
        object_title=None,
        start_offset=10,
        end_offset=20,
        raw_text=raw_text,
        text_hash=text_hash,
        effective_from=effective_from,
        effective_to=effective_to,
        version_status=LegalObjectVersionStatus.ACTIVE.value,
        extraction_status="success",
        created_at=utc_now(),
    )
    db_session.add(version)
    db_session.flush()
    return version
