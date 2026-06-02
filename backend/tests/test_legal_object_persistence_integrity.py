from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.datetime_utils import utc_now
from app.models.audit_log import AuditLog
from app.models.country import Country
from app.models.legal_object import LegalObject
from app.models.legal_object_duplicate import LegalObjectDuplicate
from app.models.legal_object_lineage import LegalObjectLineage
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
    IntegrityOperationStatus,
    LegalObjectIntegrityResult,
    LegalObjectIntegrityService,
    LegalObjectPersistenceService,
    LegalObjectStatus,
    PersistenceStatus,
    compute_content_integrity_hash,
    validate_legal_object_status,
    verify_text_hash,
)
from app.services.legal_object_persistence.immutability import ImmutabilityViolationError
from app.services.legal_object_persistence.repository import LegalObjectPersistenceRepository
from app.services.legal_object_schema_contract.lineage import LineageRelationshipType


def _candidate(
    *,
    source_version_id: str,
    legal_object_id: str | None = None,
    raw_text: str = "Tax is due on supply.",
    canonical_path: str = "PART I > Section 15",
    text_hash: str | None = None,
    parent_legal_object_id: str | None = None,
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
        parent_legal_object_id=parent_legal_object_id,
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


def _converged(candidate: LegalObjectCandidate) -> ConvergedLegalObjectCandidate:
    return ConvergedLegalObjectCandidate(
        candidate=candidate,
        source_pipeline=ConvergenceSource.STRUCTURAL_UNIT,
        convergence_status=ConvergenceStatus.CANONICAL,
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


def test_same_content_produces_same_integrity_hash():
    kwargs = {
        "source_version_id": str(uuid4()),
        "object_type": "section",
        "object_identifier": "su-0001:Section 15",
        "canonical_text": "Tax is due on supply.",
        "effective_from": date(2024, 1, 1),
        "effective_to": date(2025, 1, 1),
    }
    assert compute_content_integrity_hash(**kwargs) == compute_content_integrity_hash(**kwargs)


def test_modified_content_produces_different_integrity_hash():
    base = {
        "source_version_id": str(uuid4()),
        "object_type": "section",
        "object_identifier": "su-0001:Section 15",
        "effective_from": None,
        "effective_to": None,
    }
    first = compute_content_integrity_hash(canonical_text="Version A", **base)
    second = compute_content_integrity_hash(canonical_text="Version B", **base)
    assert first != second


def test_volatile_fields_not_in_integrity_hash_payload():
    base_text = "Stable legal text."
    kwargs = {
        "source_version_id": str(uuid4()),
        "object_type": "section",
        "object_identifier": "su-0001:Section 15",
        "canonical_text": base_text,
    }
    assert compute_content_integrity_hash(**kwargs) == compute_content_integrity_hash(**kwargs)
    assert verify_text_hash(raw_text=base_text, text_hash=sha256_text(base_text))


def test_invalid_status_rejected():
    with pytest.raises(ValueError, match="invalid legal object status"):
        validate_legal_object_status("deleted")


def test_integrity_result_forbids_extra_fields():
    with pytest.raises(ValidationError):
        LegalObjectIntegrityResult(
            legal_object_id="lo_test",
            operation="archive",
            operation_status=IntegrityOperationStatus.SUCCESS,
            extra_field="not allowed",
        )


def test_repository_hard_delete_raises():
    repo = LegalObjectPersistenceRepository()
    with pytest.raises(ImmutabilityViolationError, match="hard delete"):
        repo.delete_legal_object(None, None)  # type: ignore[arg-type]


@pytest.mark.integration
def test_persisted_content_cannot_be_silently_changed(db_session):
    version = _seed_source_version(db_session)
    candidate = _candidate(source_version_id=str(version.id))
    LegalObjectPersistenceService().persist(db_session, _converged(candidate))

    stored = db_session.query(LegalObjectVersion).one()
    original_text = stored.raw_text
    original_hash = stored.text_hash

    LegalObjectPersistenceService().persist(db_session, _converged(candidate))
    db_session.refresh(stored)

    assert stored.raw_text == original_text
    assert stored.text_hash == original_hash


@pytest.mark.integration
def test_destructive_update_rejected(db_session):
    version = _seed_source_version(db_session)
    candidate = _candidate(source_version_id=str(version.id))
    LegalObjectPersistenceService().persist(db_session, _converged(candidate))

    integrity = LegalObjectIntegrityService()
    result = integrity.update_legal_object(
        db_session,
        candidate.legal_object_id,
        updates={"canonical_path": "mutated path"},
    )

    assert result.operation_status == IntegrityOperationStatus.REJECTED
    legal_object = db_session.query(LegalObject).one()
    assert legal_object.canonical_path == candidate.canonical_path


@pytest.mark.integration
def test_archive_preserves_record(db_session):
    version = _seed_source_version(db_session)
    candidate = _candidate(source_version_id=str(version.id))
    LegalObjectPersistenceService().persist(db_session, _converged(candidate))

    result = LegalObjectIntegrityService().archive_legal_object(
        db_session,
        candidate.legal_object_id,
    )

    assert result.operation_status == IntegrityOperationStatus.SUCCESS
    assert db_session.query(LegalObject).count() == 1
    assert db_session.query(LegalObjectVersion).count() == 1
    legal_object = db_session.query(LegalObject).one()
    assert legal_object.status == LegalObjectStatus.ARCHIVED.value


@pytest.mark.integration
def test_missing_source_version_id_rejected(db_session):
    candidate = _candidate(source_version_id=str(uuid4()))
    candidate = candidate.model_copy(update={"source_version_id": ""})
    result = LegalObjectPersistenceService().persist(db_session, _converged(candidate))

    assert result.persistence_status == PersistenceStatus.REJECTED
    assert db_session.query(LegalObject).count() == 0


@pytest.mark.integration
def test_invalid_text_hash_rejected(db_session):
    version = _seed_source_version(db_session)
    candidate = _candidate(
        source_version_id=str(version.id),
        text_hash="0" * 64,
    )
    result = LegalObjectPersistenceService().persist(db_session, _converged(candidate))

    assert result.persistence_status == PersistenceStatus.REJECTED
    assert "text_hash" in result.warnings[0]


@pytest.mark.integration
def test_supersession_preserves_old_object_and_records_lineage(db_session):
    version = _seed_source_version(db_session)
    original = _candidate(source_version_id=str(version.id))
    LegalObjectPersistenceService().persist(db_session, _converged(original))

    replacement = _candidate(
        source_version_id=str(version.id),
        raw_text="Replacement legal text for supersession.",
        canonical_path="PART I > Section 16",
    )
    result = LegalObjectIntegrityService().supersede_legal_object(
        db_session,
        _converged(replacement),
        supersedes_legal_object_id=original.legal_object_id,
    )

    assert result.operation_status == IntegrityOperationStatus.SUCCESS
    prior = db_session.query(LegalObject).filter_by(legal_object_id=original.legal_object_id).one()
    assert prior.status == LegalObjectStatus.SUPERSEDED.value
    assert db_session.query(LegalObjectVersion).filter_by(
        legal_object_id=original.legal_object_id
    ).one().raw_text == original.raw_text

    lineage = db_session.query(LegalObjectLineage).all()
    assert len(lineage) == 2
    relationship_types = {row.relationship_type for row in lineage}
    assert relationship_types == {
        LineageRelationshipType.SUPERSEDES.value,
        LineageRelationshipType.SUPERSEDED_BY.value,
    }


@pytest.mark.integration
def test_supersede_rejected_when_persist_is_duplicate(db_session):
    version = _seed_source_version(db_session)
    original = _candidate(source_version_id=str(version.id))
    LegalObjectPersistenceService().persist(db_session, _converged(original))

    result = LegalObjectIntegrityService().supersede_legal_object(
        db_session,
        _converged(original),
        supersedes_legal_object_id=original.legal_object_id,
    )

    assert result.operation_status == IntegrityOperationStatus.REJECTED
    prior = db_session.query(LegalObject).filter_by(legal_object_id=original.legal_object_id).one()
    assert prior.status == LegalObjectStatus.ACTIVE.value
    assert db_session.query(LegalObjectLineage).count() == 0


@pytest.mark.integration
def test_supersede_rejected_when_persist_creates_version_not_object(db_session):
    version = _seed_source_version(db_session)
    original = _candidate(source_version_id=str(version.id))
    LegalObjectPersistenceService().persist(db_session, _converged(original))

    same_id_new_hash = _candidate(
        source_version_id=str(version.id),
        legal_object_id=original.legal_object_id,
        raw_text="Different text for version-only persist.",
    )
    result = LegalObjectIntegrityService().supersede_legal_object(
        db_session,
        _converged(same_id_new_hash),
        supersedes_legal_object_id=original.legal_object_id,
    )

    assert result.operation_status == IntegrityOperationStatus.REJECTED
    prior = db_session.query(LegalObject).filter_by(legal_object_id=original.legal_object_id).one()
    assert prior.status == LegalObjectStatus.ACTIVE.value
    assert db_session.query(LegalObjectLineage).count() == 0


def test_supersede_rejects_self_referential_legal_object_id():
    from unittest.mock import MagicMock

    from app.services.legal_object_persistence.models import LegalObjectPersistenceResult

    shared_id = "lo_self_referential_test_id"
    prior = MagicMock()
    prior.status = LegalObjectStatus.ACTIVE.value

    repository = MagicMock()
    repository.get_legal_object.return_value = prior

    persistence = MagicMock()
    persistence.persist.return_value = LegalObjectPersistenceResult(
        legal_object_id=shared_id,
        legal_object_version_id=str(uuid4()),
        persistence_status=PersistenceStatus.CREATED,
        created_legal_object=True,
        created_version=True,
    )

    candidate = _candidate(source_version_id=str(uuid4()), legal_object_id=shared_id)
    db = MagicMock()
    db.rollback = MagicMock()

    result = LegalObjectIntegrityService(
        repository=repository,
        persistence_service=persistence,
    ).supersede_legal_object(
        db,
        _converged(candidate),
        supersedes_legal_object_id=shared_id,
    )

    assert result.operation_status == IntegrityOperationStatus.REJECTED
    assert "must differ" in result.warnings[0]
    db.rollback.assert_not_called()
    repository.update_legal_object_status.assert_not_called()
    repository.create_lineage_record.assert_not_called()


@pytest.mark.integration
def test_parent_lineage_written_on_persist(db_session):
    version = _seed_source_version(db_session)
    parent = _candidate(source_version_id=str(version.id), canonical_path="PART I > Section 1")
    LegalObjectPersistenceService().persist(db_session, _converged(parent))

    child = _candidate(
        source_version_id=str(version.id),
        canonical_path="PART I > Section 1 > Clause A",
        raw_text="Child clause text.",
        parent_legal_object_id=parent.legal_object_id,
    )
    LegalObjectPersistenceService().persist(db_session, _converged(child))

    lineage = (
        db_session.query(LegalObjectLineage)
        .filter_by(relationship_type=LineageRelationshipType.PARENT_CHILD.value)
        .one()
    )
    assert lineage.parent_legal_object_id == parent.legal_object_id
    assert lineage.legal_object_id == child.legal_object_id


@pytest.mark.integration
def test_cross_object_duplicate_recorded(db_session):
    version = _seed_source_version(db_session)
    shared_text = "Identical shared legal text."
    primary = _candidate(
        source_version_id=str(version.id),
        raw_text=shared_text,
        canonical_path="PART I > Section 10",
    )
    LegalObjectPersistenceService().persist(db_session, _converged(primary))

    duplicate = _candidate(
        source_version_id=str(version.id),
        raw_text=shared_text,
        canonical_path="PART I > Section 99",
    )
    result = LegalObjectPersistenceService().persist(db_session, _converged(duplicate))

    assert result.persistence_status == PersistenceStatus.CREATED
    dup_row = db_session.query(LegalObjectDuplicate).one()
    assert dup_row.primary_legal_object_id == primary.legal_object_id
    assert dup_row.duplicate_legal_object_id == duplicate.legal_object_id
    assert dup_row.text_hash_match is True


@pytest.mark.integration
def test_audit_log_written_on_create(db_session):
    version = _seed_source_version(db_session)
    candidate = _candidate(source_version_id=str(version.id))
    LegalObjectPersistenceService().persist(db_session, _converged(candidate))

    audit_rows = db_session.query(AuditLog).filter_by(entity_type="legal_object").all()
    assert len(audit_rows) >= 1
    assert audit_rows[0].action_type in {"create", "version_create"}


def test_no_crud_api_files_introduced():
    from pathlib import Path

    routes = Path(__file__).resolve().parents[1] / "app" / "api" / "routes"
    assert not any("legal_object" in path.name for path in routes.glob("*.py"))
