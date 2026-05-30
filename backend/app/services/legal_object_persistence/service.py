import uuid
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.legal_object_convergence.enums import ConvergenceStatus
from app.services.legal_object_persistence.contract import assert_converged_persistence_input
from app.services.legal_object_persistence.enums import PersistenceStatus
from app.services.legal_object_persistence.models import LegalObjectPersistenceResult
from app.services.legal_object_persistence.repository import LegalObjectPersistenceRepository
from app.services.legal_object_convergence.models import ConvergedLegalObjectCandidate


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
        if source_version is None:
            return LegalObjectPersistenceResult(
                legal_object_id=candidate.legal_object_id,
                persistence_status=PersistenceStatus.FAILED,
                warnings=["source_version not found"],
                metadata={"failed_reason": "source_version_not_found"},
            )

        document = source_version.source_document
        if document is None:
            return LegalObjectPersistenceResult(
                legal_object_id=candidate.legal_object_id,
                persistence_status=PersistenceStatus.FAILED,
                warnings=["source_document not found for source_version"],
                metadata={"failed_reason": "source_document_not_found"},
            )

        existing_version = self._repository.get_version_by_text_hash(
            db,
            legal_object_id=candidate.legal_object_id,
            text_hash=candidate.text_hash,
        )
        if existing_version is not None:
            return LegalObjectPersistenceResult(
                legal_object_id=candidate.legal_object_id,
                legal_object_version_id=str(existing_version.legal_object_version_id),
                persistence_status=PersistenceStatus.DUPLICATE_DETECTED,
                duplicate_detected=True,
                warnings=warnings + ["identical legal_object_id and text_hash already persisted"],
                metadata={"existing_version_id": str(existing_version.legal_object_version_id)},
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
            version_status="active",
            extraction_status=candidate.extraction_status.value,
        )

        self._repository.set_current_version(db, legal_object, version.legal_object_version_id)

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
            },
        )
