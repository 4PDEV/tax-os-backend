"""Integrity-governed lifecycle operations for persisted legal objects."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.services.legal_object_convergence.models import ConvergedLegalObjectCandidate
from app.services.legal_object_persistence.audit import record_legal_object_audit_event
from app.services.legal_object_persistence.contract import (
    LegalObjectPersistenceError,
    assert_converged_persistence_input,
)
from app.services.legal_object_persistence.enums import IntegrityOperationStatus, PersistenceStatus
from app.services.legal_object_persistence.immutability import (
    ImmutabilityViolationError,
    assert_no_destructive_legal_object_update,
)
from app.services.legal_object_persistence.models import LegalObjectIntegrityResult
from app.services.legal_object_persistence.repository import LegalObjectPersistenceRepository
from app.services.legal_object_persistence.service import LegalObjectPersistenceService
from app.services.legal_object_persistence.status_enums import LegalObjectStatus
from app.services.legal_object_schema_contract.lineage import LineageRelationshipType


class LegalObjectIntegrityService:
    """Archive, supersede, and guarded update operations for legal objects."""

    def __init__(
        self,
        repository: LegalObjectPersistenceRepository | None = None,
        persistence_service: LegalObjectPersistenceService | None = None,
    ):
        self._repository = repository or LegalObjectPersistenceRepository()
        self._persistence = persistence_service or LegalObjectPersistenceService(self._repository)

    def archive_legal_object(
        self,
        db: Session,
        legal_object_id: str,
        *,
        commit: bool = False,
    ) -> LegalObjectIntegrityResult:
        try:
            legal_object = self._repository.get_legal_object(db, legal_object_id)
            if legal_object is None:
                return LegalObjectIntegrityResult(
                    legal_object_id=legal_object_id,
                    operation="archive",
                    operation_status=IntegrityOperationStatus.FAILED,
                    warnings=["legal object not found"],
                )

            previous_status = legal_object.status
            self._repository.update_legal_object_status(
                db,
                legal_object,
                status=LegalObjectStatus.ARCHIVED.value,
            )
            record_legal_object_audit_event(
                db,
                entity_type="legal_object",
                entity_id=legal_object_id,
                action_type="archive",
                previous_state={"status": previous_status},
                new_state={"status": LegalObjectStatus.ARCHIVED.value},
            )
            if commit:
                db.commit()
            else:
                db.flush()

            return LegalObjectIntegrityResult(
                legal_object_id=legal_object_id,
                operation="archive",
                operation_status=IntegrityOperationStatus.SUCCESS,
                previous_status=previous_status,
                new_status=LegalObjectStatus.ARCHIVED.value,
            )
        except Exception as exc:
            db.rollback()
            return LegalObjectIntegrityResult(
                legal_object_id=legal_object_id,
                operation="archive",
                operation_status=IntegrityOperationStatus.FAILED,
                warnings=[str(exc)],
            )

    def supersede_legal_object(
        self,
        db: Session,
        superseding: ConvergedLegalObjectCandidate,
        *,
        supersedes_legal_object_id: str,
        commit: bool = False,
    ) -> LegalObjectIntegrityResult:
        try:
            assert_converged_persistence_input(superseding)
            prior = self._repository.get_legal_object(db, supersedes_legal_object_id)
            if prior is None:
                return LegalObjectIntegrityResult(
                    legal_object_id=supersedes_legal_object_id,
                    operation="supersede",
                    operation_status=IntegrityOperationStatus.FAILED,
                    warnings=["superseded legal object not found"],
                )

            if prior.status not in {
                LegalObjectStatus.ACTIVE.value,
                LegalObjectStatus.DRAFT.value,
            }:
                return LegalObjectIntegrityResult(
                    legal_object_id=supersedes_legal_object_id,
                    operation="supersede",
                    operation_status=IntegrityOperationStatus.REJECTED,
                    warnings=[f"cannot supersede legal object with status {prior.status!r}"],
                    previous_status=prior.status,
                )

            previous_status = prior.status
            persist_result = self._persistence.persist(db, superseding, commit=False)
            if persist_result.persistence_status != PersistenceStatus.CREATED:
                operation_status = (
                    IntegrityOperationStatus.FAILED
                    if persist_result.persistence_status
                    in {PersistenceStatus.REJECTED, PersistenceStatus.FAILED}
                    else IntegrityOperationStatus.REJECTED
                )
                return LegalObjectIntegrityResult(
                    legal_object_id=supersedes_legal_object_id,
                    operation="supersede",
                    operation_status=operation_status,
                    warnings=persist_result.warnings
                    + [
                        "supersession requires a newly created legal object; "
                        f"persist returned {persist_result.persistence_status.value}"
                    ],
                    metadata={"persist_result": persist_result.persistence_status.value},
                )

            new_object_id = persist_result.legal_object_id
            if new_object_id == supersedes_legal_object_id:
                return LegalObjectIntegrityResult(
                    legal_object_id=supersedes_legal_object_id,
                    operation="supersede",
                    operation_status=IntegrityOperationStatus.REJECTED,
                    warnings=[
                        "supersession rejected: new and superseded legal_object_id must differ"
                    ],
                    previous_status=previous_status,
                )

            source_version_id = UUID(superseding.candidate.source_version_id)

            self._repository.update_legal_object_status(
                db,
                prior,
                status=LegalObjectStatus.SUPERSEDED.value,
            )
            self._repository.create_lineage_record(
                db,
                legal_object_id=new_object_id,
                source_version_id=source_version_id,
                relationship_type=LineageRelationshipType.SUPERSEDES.value,
                supersedes_legal_object_id=supersedes_legal_object_id,
            )
            self._repository.create_lineage_record(
                db,
                legal_object_id=supersedes_legal_object_id,
                source_version_id=source_version_id,
                relationship_type=LineageRelationshipType.SUPERSEDED_BY.value,
                superseded_by_legal_object_id=new_object_id,
            )
            record_legal_object_audit_event(
                db,
                entity_type="legal_object",
                entity_id=supersedes_legal_object_id,
                action_type="supersede",
                previous_state={"status": previous_status},
                new_state={
                    "status": LegalObjectStatus.SUPERSEDED.value,
                    "superseded_by_legal_object_id": new_object_id,
                },
            )
            if commit:
                db.commit()
            else:
                db.flush()

            return LegalObjectIntegrityResult(
                legal_object_id=new_object_id,
                operation="supersede",
                operation_status=IntegrityOperationStatus.SUCCESS,
                previous_status=previous_status,
                new_status=LegalObjectStatus.SUPERSEDED.value,
                related_legal_object_id=supersedes_legal_object_id,
                metadata={
                    "superseded_legal_object_id": supersedes_legal_object_id,
                    "legal_object_version_id": persist_result.legal_object_version_id,
                },
            )
        except Exception as exc:
            db.rollback()
            return LegalObjectIntegrityResult(
                legal_object_id=supersedes_legal_object_id,
                operation="supersede",
                operation_status=IntegrityOperationStatus.FAILED,
                warnings=[str(exc)],
            )

    def update_legal_object(
        self,
        db: Session,
        legal_object_id: str,
        *,
        updates: dict,
        commit: bool = False,
    ) -> LegalObjectIntegrityResult:
        try:
            legal_object = self._repository.get_legal_object(db, legal_object_id)
            if legal_object is None:
                return LegalObjectIntegrityResult(
                    legal_object_id=legal_object_id,
                    operation="update",
                    operation_status=IntegrityOperationStatus.FAILED,
                    warnings=["legal object not found"],
                )

            for field_name, new_value in updates.items():
                previous_value = getattr(legal_object, field_name)
                assert_no_destructive_legal_object_update(
                    field_name=field_name,
                    previous_value=previous_value,
                    new_value=new_value,
                )
                setattr(legal_object, field_name, new_value)

            legal_object.updated_at = utc_now()
            db.add(legal_object)
            if commit:
                db.commit()
            else:
                db.flush()

            return LegalObjectIntegrityResult(
                legal_object_id=legal_object_id,
                operation="update",
                operation_status=IntegrityOperationStatus.SUCCESS,
            )
        except (ImmutabilityViolationError, LegalObjectPersistenceError, ValueError) as exc:
            return LegalObjectIntegrityResult(
                legal_object_id=legal_object_id,
                operation="update",
                operation_status=IntegrityOperationStatus.REJECTED,
                warnings=[str(exc)],
            )
        except Exception as exc:
            db.rollback()
            return LegalObjectIntegrityResult(
                legal_object_id=legal_object_id,
                operation="update",
                operation_status=IntegrityOperationStatus.FAILED,
                warnings=[str(exc)],
            )
