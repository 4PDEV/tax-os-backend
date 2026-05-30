from enum import Enum


class LegalObjectStatus(str, Enum):
    """Governed lifecycle status for legal_objects rows."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class LegalObjectVersionStatus(str, Enum):
    """Governed lifecycle status for legal_object_versions rows."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class DuplicateType(str, Enum):
    """Classification for legal_object_duplicates rows."""

    TEXT_HASH = "text_hash"
    CANONICAL_PATH = "canonical_path"
    COMBINED = "combined"


class DuplicateResolutionStatus(str, Enum):
    """Review outcome for duplicate records — rows are never deleted."""

    PENDING = "pending"
    CONFIRMED_DUPLICATE = "confirmed_duplicate"
    NOT_DUPLICATE = "not_duplicate"
    DEFERRED = "deferred"


LEGAL_OBJECT_STATUS_VALUES: frozenset[str] = frozenset(s.value for s in LegalObjectStatus)
LEGAL_OBJECT_VERSION_STATUS_VALUES: frozenset[str] = frozenset(
    s.value for s in LegalObjectVersionStatus
)


def validate_legal_object_status(status: str) -> str:
    if status not in LEGAL_OBJECT_STATUS_VALUES:
        raise ValueError(
            f"invalid legal object status {status!r}; "
            f"allowed: {sorted(LEGAL_OBJECT_STATUS_VALUES)}"
        )
    return status


def validate_version_status(status: str) -> str:
    if status not in LEGAL_OBJECT_VERSION_STATUS_VALUES:
        raise ValueError(
            f"invalid version status {status!r}; "
            f"allowed: {sorted(LEGAL_OBJECT_VERSION_STATUS_VALUES)}"
        )
    return status
