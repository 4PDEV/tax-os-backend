"""TASK-006X1 — verify DB uniqueness on (legal_object_id, text_hash) for legal_object_versions."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.datetime_utils import utc_now
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.services.legal_object_extraction.enums import LegalObjectExtractionStatus, LegalObjectType
from app.services.legal_object_extraction.identity import generate_legal_object_id, sha256_text
from app.services.legal_object_persistence.repository import LegalObjectPersistenceRepository
from app.services.legal_object_persistence.status_enums import (
    LegalObjectStatus,
    LegalObjectVersionStatus,
)
from app.services.legal_object_promotion import (
    create_promotion_request,
    legal_object_id_for_parsed_structure,
)
from app.workers.legal_object_promotion import run_controlled_legal_object_promotion
from tests.test_legal_object_persistence_repository import _seed_source_version
from tests.test_legal_object_promotion_persistence import _seed_parsed_structure

pytestmark = pytest.mark.integration

CONSTRAINT_NAME = "uq_legal_object_versions_object_hash"


def test_db_rejects_duplicate_legal_object_id_and_text_hash(db_session):
    version = _seed_source_version(db_session)
    raw_text = "Section 15 applies."
    text_hash = sha256_text(raw_text)
    legal_object_id = generate_legal_object_id(
        source_version_id=str(version.id),
        canonical_path="Section 15",
        object_type=LegalObjectType.SECTION.value,
        object_label="Section 15",
        start_offset=0,
        text_hash=text_hash,
    )
    document = version.source_document
    repo = LegalObjectPersistenceRepository()
    repo.create_legal_object(
        db_session,
        legal_object_id=legal_object_id,
        source_document_id=document.id,
        country_id=document.country_id,
        tax_type_id=document.tax_type_id,
        object_type=LegalObjectType.SECTION.value,
        canonical_path="Section 15",
        status=LegalObjectStatus.ACTIVE.value,
    )
    version_id = uuid.uuid4()
    repo.create_version(
        db_session,
        legal_object_version_id=version_id,
        legal_object_id=legal_object_id,
        source_version_id=version.id,
        parent_legal_object_id=None,
        structural_unit_id="su-001",
        object_label="Section 15",
        object_title=None,
        start_offset=0,
        end_offset=len(raw_text),
        raw_text=raw_text,
        text_hash=text_hash,
        version_status=LegalObjectVersionStatus.ACTIVE.value,
        extraction_status=LegalObjectExtractionStatus.SUCCESS.value,
    )
    db_session.flush()

    duplicate = LegalObjectVersion(
        legal_object_version_id=uuid.uuid4(),
        legal_object_id=legal_object_id,
        source_version_id=version.id,
        parent_legal_object_id=None,
        structural_unit_id="su-002",
        object_label="Section 15 duplicate",
        object_title=None,
        start_offset=0,
        end_offset=len(raw_text),
        raw_text=raw_text,
        text_hash=text_hash,
        version_status=LegalObjectVersionStatus.ACTIVE.value,
        extraction_status=LegalObjectExtractionStatus.SUCCESS.value,
        created_at=utc_now(),
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_repository_get_version_by_text_hash_finds_existing(db_session):
    version = _seed_source_version(db_session)
    raw_text = "Article 1 text."
    text_hash = sha256_text(raw_text)
    legal_object_id = generate_legal_object_id(
        source_version_id=str(version.id),
        canonical_path="Article 1",
        object_type=LegalObjectType.ARTICLE.value,
        object_label="Article 1",
        start_offset=0,
        text_hash=text_hash,
    )
    document = version.source_document
    repo = LegalObjectPersistenceRepository()
    repo.create_legal_object(
        db_session,
        legal_object_id=legal_object_id,
        source_document_id=document.id,
        country_id=document.country_id,
        tax_type_id=document.tax_type_id,
        object_type=LegalObjectType.ARTICLE.value,
        canonical_path="Article 1",
    )
    vid = uuid.uuid4()
    repo.create_version(
        db_session,
        legal_object_version_id=vid,
        legal_object_id=legal_object_id,
        source_version_id=version.id,
        parent_legal_object_id=None,
        structural_unit_id="su-a1",
        object_label="Article 1",
        object_title=None,
        start_offset=0,
        end_offset=10,
        raw_text=raw_text,
        text_hash=text_hash,
        version_status=LegalObjectVersionStatus.ACTIVE.value,
        extraction_status=LegalObjectExtractionStatus.SUCCESS.value,
    )
    found = repo.get_version_by_text_hash(
        db_session, legal_object_id=legal_object_id, text_hash=text_hash
    )
    assert found is not None
    assert found.legal_object_version_id == vid


def test_force_repromotion_creates_distinct_text_hash_versions(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="initial",
        force_repromotion=False,
    )
    run_controlled_legal_object_promotion(db_session, controlled_promotion=True)

    replay = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="replay",
        force_repromotion=True,
    )
    run_controlled_legal_object_promotion(db_session, controlled_promotion=True)

    legal_object_id = legal_object_id_for_parsed_structure(parsed.id)
    versions = (
        db_session.query(LegalObjectVersion)
        .filter(LegalObjectVersion.legal_object_id == legal_object_id)
        .order_by(LegalObjectVersion.created_at.asc())
        .all()
    )
    assert len(versions) == 2
    assert versions[0].text_hash == parsed.structure_hash
    assert versions[1].text_hash != versions[0].text_hash

    legal_object = db_session.get(LegalObject, legal_object_id)
    assert legal_object is not None
    assert legal_object.current_version_id == versions[1].legal_object_version_id
