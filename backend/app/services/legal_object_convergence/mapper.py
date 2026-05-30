from app.core.datetime_utils import utc_now
from app.services.legal_object_convergence.enums import ConvergenceSource, ConvergenceStatus
from app.services.legal_object_convergence.models import ConvergedLegalObjectCandidate
from app.services.legal_object_convergence.validator import LegalObjectCandidateValidator
from app.services.legal_object_extraction.enums import LegalObjectExtractionStatus, LegalObjectType
from app.services.legal_object_extraction.identity import generate_legal_object_id, sha256_text
from app.services.legal_object_extraction.models import LegalObjectCandidate
from app.services.legal_objects.models import LegalObjectCandidate as LegacyLegalObjectCandidate

CONVERGENCE_MAPPER_VERSION = "1.0.0"

# Surface mapping from legacy segment-backed types to canonical extraction types.
# Unmapped legacy labels converge to UNKNOWN — no semantic inference.
LEGACY_TO_CANONICAL_TYPE: dict[str, LegalObjectType] = {
    "act": LegalObjectType.ACT,
    "regulation": LegalObjectType.REGULATION,
    "part": LegalObjectType.PART,
    "chapter": LegalObjectType.CHAPTER,
    "section": LegalObjectType.SECTION,
    "article": LegalObjectType.ARTICLE,
    "paragraph": LegalObjectType.PARAGRAPH,
    "schedule": LegalObjectType.SCHEDULE,
    "definition": LegalObjectType.DEFINITION,
    "clause": LegalObjectType.PARAGRAPH,
    "subclause": LegalObjectType.SUBPARAGRAPH,
    "unknown": LegalObjectType.UNKNOWN,
}


class LegalObjectCandidateMapper:
    """Map upstream candidate outputs into the canonical extraction model."""

    def __init__(self, validator: LegalObjectCandidateValidator | None = None):
        self._validator = validator or LegalObjectCandidateValidator()

    def from_structural_candidate(
        self, candidate: LegalObjectCandidate
    ) -> ConvergedLegalObjectCandidate:
        """Pass through structural-unit-backed candidates as canonical."""
        validation = self._validator.validate(candidate)
        warnings = list(validation.warnings)
        if validation.errors:
            return ConvergedLegalObjectCandidate(
                candidate=candidate,
                source_pipeline=ConvergenceSource.STRUCTURAL_UNIT,
                convergence_status=ConvergenceStatus.REJECTED,
                warnings=warnings + validation.errors,
                metadata={"validation_errors": validation.errors},
            )

        status = ConvergenceStatus.CANONICAL
        if candidate.extraction_status == LegalObjectExtractionStatus.PARTIAL:
            status = ConvergenceStatus.PARTIAL
            if candidate.metadata.get("extraction_warning"):
                warnings.append(str(candidate.metadata["extraction_warning"]))

        return ConvergedLegalObjectCandidate(
            candidate=candidate,
            source_pipeline=ConvergenceSource.STRUCTURAL_UNIT,
            convergence_status=status,
            warnings=warnings,
            metadata={"upstream": "legal_object_extraction"},
        )

    def from_segment_candidate(self, candidate: object) -> ConvergedLegalObjectCandidate:
        """Map segment-backed legacy candidates into the canonical model."""
        if not isinstance(candidate, LegacyLegalObjectCandidate):
            return ConvergedLegalObjectCandidate(
                candidate=_rejected_shell_candidate(),
                source_pipeline=ConvergenceSource.UNKNOWN,
                convergence_status=ConvergenceStatus.REJECTED,
                warnings=[f"unsupported candidate type: {type(candidate).__name__}"],
                metadata={"rejected_reason": "unsupported_type"},
            )

        warnings: list[str] = []
        object_label = candidate.object_label or candidate.heading
        if not object_label:
            return ConvergedLegalObjectCandidate(
                candidate=_rejected_shell_candidate(),
                source_pipeline=ConvergenceSource.SEGMENT,
                convergence_status=ConvergenceStatus.REJECTED,
                warnings=["segment candidate missing object_label and heading"],
                metadata={"rejected_reason": "missing_label", "legacy_segment_id": candidate.source_segment_id},
            )

        if not candidate.raw_text:
            return ConvergedLegalObjectCandidate(
                candidate=_rejected_shell_candidate(),
                source_pipeline=ConvergenceSource.SEGMENT,
                convergence_status=ConvergenceStatus.REJECTED,
                warnings=["segment candidate missing raw_text"],
                metadata={"rejected_reason": "missing_raw_text", "legacy_segment_id": candidate.source_segment_id},
            )

        canonical_type = LEGACY_TO_CANONICAL_TYPE.get(
            candidate.object_type.value, LegalObjectType.UNKNOWN
        )
        if candidate.object_type.value not in LEGACY_TO_CANONICAL_TYPE:
            warnings.append(
                f"legacy object_type '{candidate.object_type.value}' mapped to UNKNOWN"
            )

        source_version_id = str(candidate.source_version_id)
        canonical_path = object_label
        text_hash = sha256_text(candidate.raw_text)
        legal_object_id = generate_legal_object_id(
            source_version_id=source_version_id,
            canonical_path=canonical_path,
            object_type=canonical_type.value,
            object_label=object_label,
            start_offset=candidate.start_offset,
            text_hash=text_hash,
        )

        extraction_status = LegalObjectExtractionStatus.SUCCESS
        parent_legal_object_id: str | None = None
        if candidate.parent_legal_object_id is not None:
            extraction_status = LegalObjectExtractionStatus.PARTIAL
            warnings.append(
                "legacy parent_legal_object_id cannot be resolved without batch convergence; "
                "parent set to None"
            )

        mapped = LegalObjectCandidate(
            source_version_id=source_version_id,
            legal_object_id=legal_object_id,
            object_type=canonical_type,
            object_label=object_label,
            object_title=candidate.heading,
            canonical_path=canonical_path,
            parent_legal_object_id=parent_legal_object_id,
            structural_unit_id=candidate.source_segment_id,
            start_offset=candidate.start_offset,
            end_offset=candidate.end_offset,
            raw_text=candidate.raw_text,
            text_hash=text_hash,
            extraction_status=extraction_status,
            extracted_at=utc_now(),
            extractor_version=CONVERGENCE_MAPPER_VERSION,
            metadata={
                "convergence_source": ConvergenceSource.SEGMENT.value,
                "legacy_legal_object_id": candidate.legal_object_id,
                "legacy_segment_id": candidate.source_segment_id,
                "legacy_extractor": "legal_objects",
            },
        )

        validation = self._validator.validate(mapped)
        warnings.extend(validation.warnings)
        if validation.errors:
            return ConvergedLegalObjectCandidate(
                candidate=mapped,
                source_pipeline=ConvergenceSource.SEGMENT,
                convergence_status=ConvergenceStatus.REJECTED,
                warnings=warnings + validation.errors,
                metadata={
                    "upstream": "legal_objects",
                    "validation_errors": validation.errors,
                },
            )

        status = ConvergenceStatus.MAPPED
        if extraction_status == LegalObjectExtractionStatus.PARTIAL or warnings:
            status = ConvergenceStatus.PARTIAL

        return ConvergedLegalObjectCandidate(
            candidate=mapped,
            source_pipeline=ConvergenceSource.SEGMENT,
            convergence_status=status,
            warnings=warnings,
            metadata={"upstream": "legal_objects", "legacy": True},
        )


def _rejected_shell_candidate() -> LegalObjectCandidate:
    """Minimal placeholder for unmappable inputs; always fails validation."""
    now = utc_now()
    raw_text = ""
    text_hash = sha256_text(raw_text)
    return LegalObjectCandidate(
        source_version_id="",
        legal_object_id="lo_rejected",
        object_type=LegalObjectType.UNKNOWN,
        object_label="",
        object_title=None,
        canonical_path="",
        parent_legal_object_id=None,
        structural_unit_id="",
        start_offset=0,
        end_offset=0,
        raw_text=raw_text,
        text_hash=text_hash,
        extraction_status=LegalObjectExtractionStatus.FAILED,
        extracted_at=now,
        extractor_version=CONVERGENCE_MAPPER_VERSION,
        metadata={"rejected_shell": True},
    )
