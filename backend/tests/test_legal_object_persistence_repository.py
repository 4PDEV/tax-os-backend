from uuid import uuid4

import pytest
from pydantic import ValidationError

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
from app.services.legal_object_persistence import (
    LegalObjectPersistenceResult,
    LegalObjectPersistenceService,
    PersistenceStatus,
    assert_converged_persistence_input,
)


def _candidate(
    *,
    source_version_id: str,
    legal_object_id: str | None = None,
    raw_text: str = "Tax is due on supply.",
    canonical_path: str = "PART I > Section 15",
    text_hash: str | None = None,
) -> LegalObjectCandidate:
    th = text_hash if text_hash is not None else sha256_text(raw_text)
    lid = legal_object_id or generate_legal_object_id(
        source_version_id=source_version_id,
        canonical_path=canonical_path,
        object_type=LegalObjectType.SECTION.value,
        object_label="Section 15",
        start_offset=10,
        text_hash=th,
    )
    return LegalObjectCandidate(
        source_version_id=source_version_id,
        legal_object_id=lid,
        object_type=LegalObjectType.SECTION,
        object_label="Section 15",
        object_title=None,
        canonical_path=canonical_path,
        parent_legal_object_id=None,
        structural_unit_id="su-0001",
        start_offset=10,
        end_offset=20,
        raw_text=raw_text,
        text_hash=th,
        extraction_status=LegalObjectExtractionStatus.SUCCESS,
        extracted_at=utc_now(),
        extractor_version="1.0.0",
        metadata={},
    )


def _converged(
    candidate: LegalObjectCandidate,
    *,
    convergence_status: ConvergenceStatus = ConvergenceStatus.CANONICAL,
) -> ConvergedLegalObjectCandidate:
    return ConvergedLegalObjectCandidate(
        candidate=candidate,
        source_pipeline=ConvergenceSource.STRUCTURAL_UNIT,
        convergence_status=convergence_status,
        warnings=[],
        metadata={},
    )


def _seed_source_version(db_session):
    country = Country(code="RW", name="Rwanda", status="active")
    db_session.add(country)
    db_session.flush()

    tax_type = TaxType(country_id=country.id, code="VAT", name="VAT", status="active")
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
    return version


def test_only_converged_candidate_accepted():
    with pytest.raises(Exception):
        assert_converged_persistence_input({"not": "converged"})


def test_result_model_forbids_extra_fields():
    with pytest.raises(ValidationError):
        LegalObjectPersistenceResult(
            legal_object_id="lo_test",
            persistence_status=PersistenceStatus.CREATED,
            extra_field="not allowed",
        )


def test_rejected_convergence_is_rejected():
    candidate = _candidate(source_version_id=str(uuid4()))
    service = LegalObjectPersistenceService()
    result = service.persist(None, _converged(candidate, convergence_status=ConvergenceStatus.REJECTED))  # type: ignore[arg-type]

    assert result.persistence_status == PersistenceStatus.REJECTED


def test_invalid_input_type_rejected():
    service = LegalObjectPersistenceService()
    result = service.persist(None, object())  # type: ignore[arg-type]

    assert result.persistence_status == PersistenceStatus.REJECTED


@pytest.mark.integration
def test_legal_object_and_version_rows_created(db_session):
    version = _seed_source_version(db_session)
    candidate = _candidate(source_version_id=str(version.id))
    service = LegalObjectPersistenceService()
    result = service.persist(db_session, _converged(candidate))

    assert result.persistence_status == PersistenceStatus.CREATED
    assert result.created_legal_object is True
    assert result.created_version is True

    legal_object = db_session.query(LegalObject).one()
    assert legal_object.legal_object_id == candidate.legal_object_id
    assert legal_object.canonical_path == candidate.canonical_path

    stored_version = db_session.query(LegalObjectVersion).one()
    assert stored_version.raw_text == candidate.raw_text
    assert stored_version.text_hash == candidate.text_hash
    assert stored_version.source_version_id == version.id
    assert legal_object.current_version_id == stored_version.legal_object_version_id


@pytest.mark.integration
def test_identical_version_detected_as_duplicate(db_session):
    version = _seed_source_version(db_session)
    candidate = _candidate(source_version_id=str(version.id))
    service = LegalObjectPersistenceService()
    first = service.persist(db_session, _converged(candidate))
    second = service.persist(db_session, _converged(candidate))

    assert first.persistence_status == PersistenceStatus.CREATED
    assert second.persistence_status == PersistenceStatus.DUPLICATE_DETECTED
    assert second.duplicate_detected is True
    assert db_session.query(LegalObjectVersion).count() == 1


@pytest.mark.integration
def test_new_version_created_for_different_hash(db_session):
    version = _seed_source_version(db_session)
    candidate = _candidate(source_version_id=str(version.id))
    service = LegalObjectPersistenceService()
    service.persist(db_session, _converged(candidate))

    updated = _candidate(
        source_version_id=str(version.id),
        legal_object_id=candidate.legal_object_id,
        raw_text="Updated tax text.",
    )
    result = service.persist(db_session, _converged(updated))

    assert result.persistence_status == PersistenceStatus.VERSION_CREATED
    assert db_session.query(LegalObjectVersion).count() == 2


@pytest.mark.integration
def test_immutable_version_fields_not_overwritten(db_session):
    version = _seed_source_version(db_session)
    candidate = _candidate(source_version_id=str(version.id))
    service = LegalObjectPersistenceService()
    service.persist(db_session, _converged(candidate))

    stored = db_session.query(LegalObjectVersion).one()
    original_text = stored.raw_text
    original_hash = stored.text_hash

    service.persist(db_session, _converged(candidate))
    db_session.refresh(stored)

    assert stored.raw_text == original_text
    assert stored.text_hash == original_hash


@pytest.mark.integration
def test_current_version_id_updated_only_after_new_version(db_session):
    version = _seed_source_version(db_session)
    candidate = _candidate(source_version_id=str(version.id))
    service = LegalObjectPersistenceService()
    first = service.persist(db_session, _converged(candidate))
    legal_object = db_session.query(LegalObject).one()
    first_version_id = legal_object.current_version_id

    service.persist(db_session, _converged(candidate))
    assert legal_object.current_version_id == first_version_id

    updated = _candidate(
        source_version_id=str(version.id),
        legal_object_id=candidate.legal_object_id,
        raw_text="Different content for new version.",
    )
    second = service.persist(db_session, _converged(updated))
    db_session.refresh(legal_object)

    assert second.persistence_status == PersistenceStatus.VERSION_CREATED
    assert legal_object.current_version_id != first_version_id
    assert str(legal_object.current_version_id) == second.legal_object_version_id


def test_no_crud_api_files_introduced():
    from pathlib import Path

    routes = Path(__file__).resolve().parents[1] / "app" / "api" / "routes"
    assert not any("legal_object" in path.name for path in routes.glob("*.py"))
