import uuid
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.models.source_version import SourceVersion


class LegalObjectPersistenceRepository:
    """Data access for canonical legal object persistence."""

    def get_source_version(self, db: Session, source_version_id: UUID) -> SourceVersion | None:
        return db.query(SourceVersion).filter(SourceVersion.id == source_version_id).first()

    def get_legal_object(self, db: Session, legal_object_id: str) -> LegalObject | None:
        return (
            db.query(LegalObject)
            .filter(LegalObject.legal_object_id == legal_object_id)
            .first()
        )

    def get_version_by_text_hash(
        self,
        db: Session,
        *,
        legal_object_id: str,
        text_hash: str,
    ) -> LegalObjectVersion | None:
        return (
            db.query(LegalObjectVersion)
            .filter(
                LegalObjectVersion.legal_object_id == legal_object_id,
                LegalObjectVersion.text_hash == text_hash,
            )
            .first()
        )

    def find_version_with_different_hash_same_path(
        self,
        db: Session,
        *,
        legal_object_id: str,
        canonical_path: str,
        text_hash: str,
    ) -> LegalObjectVersion | None:
        return (
            db.query(LegalObjectVersion)
            .join(LegalObject, LegalObject.legal_object_id == LegalObjectVersion.legal_object_id)
            .filter(
                LegalObject.legal_object_id == legal_object_id,
                LegalObject.canonical_path == canonical_path,
                LegalObjectVersion.text_hash != text_hash,
            )
            .first()
        )

    def create_legal_object(
        self,
        db: Session,
        *,
        legal_object_id: str,
        source_document_id: UUID,
        country_id: UUID,
        tax_type_id: UUID | None,
        object_type: str,
        canonical_path: str,
        status: str = "active",
    ) -> LegalObject:
        record = LegalObject(
            legal_object_id=legal_object_id,
            source_document_id=source_document_id,
            country_id=country_id,
            tax_type_id=tax_type_id,
            object_type=object_type,
            canonical_path=canonical_path,
            current_version_id=None,
            status=status,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        db.add(record)
        db.flush()
        return record

    def create_version(
        self,
        db: Session,
        *,
        legal_object_version_id: uuid.UUID,
        legal_object_id: str,
        source_version_id: UUID,
        parent_legal_object_id: str | None,
        structural_unit_id: str,
        object_label: str,
        object_title: str | None,
        start_offset: int,
        end_offset: int,
        raw_text: str,
        text_hash: str,
        version_status: str,
        extraction_status: str,
    ) -> LegalObjectVersion:
        record = LegalObjectVersion(
            legal_object_version_id=legal_object_version_id,
            legal_object_id=legal_object_id,
            source_version_id=source_version_id,
            parent_legal_object_id=parent_legal_object_id,
            structural_unit_id=structural_unit_id,
            object_label=object_label,
            object_title=object_title,
            start_offset=start_offset,
            end_offset=end_offset,
            raw_text=raw_text,
            text_hash=text_hash,
            effective_from=None,
            effective_to=None,
            version_status=version_status,
            extraction_status=extraction_status,
            created_at=utc_now(),
        )
        db.add(record)
        db.flush()
        return record

    def set_current_version(
        self,
        db: Session,
        legal_object: LegalObject,
        legal_object_version_id: uuid.UUID,
    ) -> LegalObject:
        legal_object.current_version_id = legal_object_version_id
        legal_object.updated_at = utc_now()
        db.add(legal_object)
        db.flush()
        return legal_object
