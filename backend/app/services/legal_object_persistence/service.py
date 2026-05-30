import uuid
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.legal_object_convergence.enums import ConvergenceStatus
from app.services.legal_object_convergence.models import ConvergedLegalObjectCandidate
from app.services.legal_object_persistence.audit import record_legal_object_audit_event
from app.services.legal_object_persistence.contract import assert_converged_persistence_input
from app.services.legal_object_persistence.enums import PersistenceStatus
from app.services.legal_object_persistence.integrity_hash import (
    build_object_identifier,
    compute_content_integrity_hash,
    verify_text_hash,
)
from app.services.legal_object_persistence.models import LegalObjectPersistenceResult
from app.services.legal_object_persistence.repository import LegalObjectPersistenceRepository
from app.services.legal_object_persistence.status_enums import (
    DuplicateType,
    LegalObjectStatus,
    LegalObjectVersionStatus,
)
from app.services.legal_object_persistence.traceability import validate_source_traceability
from app.services.legal_object_schema_contract.lineage import LineageRelationshipType


class LegalObjectPersistenceService:
    """Persist converged legal object candidates via the canonical write path."""

    def __init__(self, repository: LegalObjectPersistenceRepository | None = None):
        self._repository = repository or LegalObjectPersistenceRepository()

    def persist(
        self,
        db: Session,
        converged: ConvergedLegalObjectCandidate,
        *,
        commit: bool = False,
    ) -> LegalObjectPersistenceResult:
        try:
            assert_converged_persistence_input(converged)
        except Exception as exc:
            return LegalObjectPersistenceResult(
                legal_object_id=getattr(getattr(converged, "candidate", None), "legal_object_id", ""),
                persistence_status=PersistenceStatus.REJECTED,
                warnings=[str(exc)],
                metadata={"rejected_reason": "invalid_input"},
            )

        if converged.convergence_status == ConvergenceStatus.REJECTED:
            return LegalObjectPersistenceResult(
                legal_object_id=converged.candidate.legal_object_id,
                persistence_status=PersistenceStatus.REJECTED,
                warnings=["convergence_status is rejected"],
                metadata={"rejected_reason": "convergence_rejected"},
            )

        candidate = converged.candidate
        warnings = list(converged.warnings)

        if not candidate.source_version_id:
            return LegalObjectPersistenceResult(
                legal_object_id=candidate.legal_object_id,
                persistence_status=PersistenceStatus.REJECTED,
                warnings=["legal object cannot be created without source_version_id"],
                metadata={"rejected_reason": "missing_source_version_id"},
            )

        if not verify_text_hash(raw_text=candidate.raw_text, text_hash=candidate.text_hash):
            return LegalObjectPersistenceResult(
                legal_object_id=candidate.legal_object_id,
                persistence_status=PersistenceStatus.REJECTED,
                warnings=["text_hash does not match SHA-256 of raw_text"],
                metadata={"rejected_reason": "hash_integrity_failure"},
            )

        try:
            source_version_id = UUID(candidate.source_version_id)
        except ValueError:
            return LegalObjectPersistenceResult(
                legal_object_id=candidate.legal_object_id,
                persistence_status=PersistenceStatus.FAILED,
                warnings=["invalid source_version_id"],
                metadata={"failed_reason": "invalid_source_version_id"},
            )

        source_version = self._repository.get_source_version(db, source_version_id)
        try:
            validate_source_traceability(
                db,
                candidate=candidate,
                source_version=source_version,
            )
        except Exception as exc:
            return LegalObjectPersistenceResult(
                legal_object_id=candidate.legal_object_id,
                persistence_status=PersistenceStatus.REJECTED,
                warnings=[str(exc)],
                metadata={"rejected_reason": "traceability_failure"},
            )

        document = source_version.source_document
        object_identifier = build_object_identifier(
            structural_unit_id=candidate.structural_unit_id,
            object_label=candidate.object_label,
        )
        integrity_hash = compute_content_integrity_hash(
            source_version_id=candidate.source_version_id,
            object_type=candidate.object_type.value,
            object_identifier=object_identifier,
            canonical_text=candidate.raw_text,
        )

        try:
            existing_version = self._repository.get_version_by_text_hash(
                db,
                legal_object_id=candidate.legal_object_id,
                text_hash=candidate.text_hash,
            )
            if existing_version is not None:
                record_legal_object_audit_event(
                    db,
                    entity_type="legal_object",
                    entity_id=candidate.legal_object_id,
                    action_type="duplicate_detected",
                    new_state={
                        "legal_object_version_id": str(existing_version.legal_object_version_id),
                        "text_hash": candidate.text_hash,
                    },
                )
                if commit:
                    db.commit()
                else:
                    db.flush()
                return LegalObjectPersistenceResult(
                    legal_object_id=candidate.legal_object_id,
                    legal_object_version_id=str(existing_version.legal_object_version_id),
                    persistence_status=PersistenceStatus.DUPLICATE_DETECTED,
                    duplicate_detected=True,
                    warnings=warnings
                    + ["identical legal_object_id and text_hash already persisted"],
                    metadata={
                        "existing_version_id": str(existing_version.legal_object_version_id),
                        "integrity_hash": integrity_hash,
                    },
                )

            cross_object_match = self._repository.find_version_by_source_and_hash(
                db,
                source_version_id=source_version_id,
                text_hash=candidate.text_hash,
                exclude_legal_object_id=candidate.legal_object_id,
            )
            if cross_object_match is not None:
                self._repository.create_duplicate_record(
                    db,
                    primary_legal_object_id=cross_object_match.legal_object_id,
                    duplicate_legal_object_id=candidate.legal_object_id,
                    duplicate_type=DuplicateType.TEXT_HASH.value,
                    text_hash_match=True,
                    canonical_path_match=cross_object_match.legal_object.canonical_path
                    == candidate.canonical_path,
                    notes="detected during persistence; no auto-merge",
                )
                warnings.append(
                    "duplicate text_hash detected for different legal_object_id; "
                    "recorded in legal_object_duplicates without auto-merge"
                )

            legal_object = self._repository.get_legal_object(db, candidate.legal_object_id)
            created_legal_object = False
            if legal_object is None:
                legal_object = self._repository.create_legal_object(
                    db,
                    legal_object_id=candidate.legal_object_id,
                    source_document_id=document.id,
                    country_id=document.country_id,
                    tax_type_id=document.tax_type_id,
                    object_type=candidate.object_type.value,
                    canonical_path=candidate.canonical_path,
                    status=LegalObjectStatus.ACTIVE.value,
                )
                created_legal_object = True
            elif legal_object.canonical_path != candidate.canonical_path:
                warnings.append(
                    "canonical_path differs from persisted legal object identity record"
                )

            path_conflict = self._repository.find_version_with_different_hash_same_path(
                db,
                legal_object_id=candidate.legal_object_id,
                canonical_path=candidate.canonical_path,
                text_hash=candidate.text_hash,
            )
            if path_conflict is not None:
                warnings.append(
                    "canonical_path matches an existing version with different text_hash; "
                    "creating new version without auto-merge"
                )

            version_id = uuid.uuid4()
            version = self._repository.create_version(
                db,
                legal_object_version_id=version_id,
                legal_object_id=candidate.legal_object_id,
                source_version_id=source_version_id,
                parent_legal_object_id=candidate.parent_legal_object_id,
                structural_unit_id=candidate.structural_unit_id,
                object_label=candidate.object_label,
                object_title=candidate.object_title,
                start_offset=candidate.start_offset,
                end_offset=candidate.end_offset,
                raw_text=candidate.raw_text,
                text_hash=candidate.text_hash,
                version_status=LegalObjectVersionStatus.ACTIVE.value,
                extraction_status=candidate.extraction_status.value,
            )

            self._repository.set_current_version(
                db, legal_object, version.legal_object_version_id
            )

            if candidate.parent_legal_object_id:
                self._repository.create_lineage_record(
                    db,
                    legal_object_id=candidate.legal_object_id,
                    source_version_id=source_version_id,
                    relationship_type=LineageRelationshipType.PARENT_CHILD.value,
                    parent_legal_object_id=candidate.parent_legal_object_id,
                )

            record_legal_object_audit_event(
                db,
                entity_type="legal_object",
                entity_id=candidate.legal_object_id,
                action_type="create" if created_legal_object else "version_create",
                new_state={
                    "legal_object_version_id": str(version.legal_object_version_id),
                    "source_version_id": str(source_version_id),
                    "source_document_id": str(document.id),
                    "integrity_hash": integrity_hash,
                },
            )

            status = (
                PersistenceStatus.CREATED
                if created_legal_object
                else PersistenceStatus.VERSION_CREATED
            )

            if commit:
                db.commit()
            else:
                db.flush()

            return LegalObjectPersistenceResult(
                legal_object_id=candidate.legal_object_id,
                legal_object_version_id=str(version.legal_object_version_id),
                persistence_status=status,
                created_legal_object=created_legal_object,
                created_version=True,
                duplicate_detected=False,
                warnings=warnings,
                metadata={
                    "source_pipeline": converged.source_pipeline.value,
                    "convergence_status": converged.convergence_status.value,
                    "integrity_hash": integrity_hash,
                    "source_document_id": str(document.id),
                },
            )
        except Exception as exc:
            db.rollback()
            return LegalObjectPersistenceResult(
                legal_object_id=candidate.legal_object_id,
                persistence_status=PersistenceStatus.FAILED,
                warnings=[str(exc)],
                metadata={"failed_reason": "transaction_rollback"},
            )
