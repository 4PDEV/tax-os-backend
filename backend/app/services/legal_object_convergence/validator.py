from dataclasses import dataclass, field

from app.services.legal_object_extraction.enums import LegalObjectExtractionStatus
from app.services.legal_object_extraction.identity import generate_legal_object_id, sha256_text
from app.services.legal_object_extraction.models import LegalObjectCandidate


@dataclass
class ValidationResult:
    valid: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class LegalObjectCandidateValidator:
    """Validate canonical legal object candidates before persistence planning."""

    def validate(self, candidate: LegalObjectCandidate) -> ValidationResult:
        warnings: list[str] = []
        errors: list[str] = []

        if not candidate.legal_object_id or not candidate.legal_object_id.strip():
            errors.append("legal_object_id is required")
        if not candidate.source_version_id or not candidate.source_version_id.strip():
            errors.append("source_version_id is required")
        if not candidate.canonical_path or not candidate.canonical_path.strip():
            errors.append("canonical_path is required")
        if not candidate.raw_text:
            errors.append("raw_text is required")

        if candidate.end_offset < candidate.start_offset:
            errors.append("end_offset must be >= start_offset")

        expected_hash = sha256_text(candidate.raw_text)
        if candidate.text_hash != expected_hash:
            errors.append("text_hash does not match SHA256(raw_text)")

        expected_id = generate_legal_object_id(
            source_version_id=candidate.source_version_id,
            canonical_path=candidate.canonical_path,
            object_type=candidate.object_type.value,
            object_label=candidate.object_label,
            start_offset=candidate.start_offset,
            text_hash=candidate.text_hash,
        )
        if candidate.legal_object_id != expected_id:
            errors.append("legal_object_id does not match canonical identity generator output")

        if (
            candidate.parent_legal_object_id is None
            and candidate.extraction_status == LegalObjectExtractionStatus.SUCCESS
            and candidate.metadata.get("extraction_warning")
        ):
            warnings.append(
                "structural lineage warning present while extraction_status is success"
            )

        if (
            candidate.parent_legal_object_id is None
            and candidate.extraction_status not in (
                LegalObjectExtractionStatus.SUCCESS,
                LegalObjectExtractionStatus.PARTIAL,
            )
        ):
            warnings.append(
                f"missing parent lineage with extraction_status={candidate.extraction_status.value}"
            )

        return ValidationResult(valid=not errors, warnings=warnings, errors=errors)

    def check_duplicate_ids(self, candidates: list[LegalObjectCandidate]) -> list[str]:
        """Return warnings for duplicate legal_object_id values in a batch."""
        seen: dict[str, int] = {}
        warnings: list[str] = []
        for candidate in candidates:
            seen[candidate.legal_object_id] = seen.get(candidate.legal_object_id, 0) + 1
        for legal_object_id, count in seen.items():
            if count > 1:
                warnings.append(f"duplicate legal_object_id: {legal_object_id} ({count} occurrences)")
        return warnings
