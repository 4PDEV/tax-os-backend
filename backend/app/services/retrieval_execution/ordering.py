from datetime import date

from app.services.retrieval_execution.models import EvidenceCandidate


def _effective_from_key(value: date | None) -> tuple:
    """ASC NULLS LAST."""
    if value is None:
        return (1, date.min)
    return (0, value)


def _nulls_last_str(value: str | None) -> tuple:
    if value is None:
        return (1, "")
    return (0, value)


def sort_evidence_candidates(candidates: list[EvidenceCandidate]) -> list[EvidenceCandidate]:
    """Canonical deterministic ordering per TASK-007E / RW-04."""
    return sorted(
        candidates,
        key=lambda c: (
            _effective_from_key(c.effective_from),
            c.legal_object_id,
            str(c.legal_object_version_id),
            _nulls_last_str(c.citation_hash),
            _nulls_last_str(c.object_identifier),
        ),
    )
