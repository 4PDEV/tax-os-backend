"""Explicit retrieval failures — no silent generic errors."""


class LegalObjectRetrievalError(Exception):
    """Base class for legal object retrieval errors."""


class LegalObjectNotFoundError(LegalObjectRetrievalError):
    """Raised when a requested legal object cannot be found."""

    def __init__(self, legal_object_id: str):
        self.legal_object_id = legal_object_id
        super().__init__(f"legal object not found: {legal_object_id}")


class InvalidEffectiveDateError(LegalObjectRetrievalError):
    """Raised when effective-date inputs are invalid or inconsistent."""

    def __init__(self, message: str):
        super().__init__(message)


class RetrievalIntegrityError(LegalObjectRetrievalError):
    """Raised when persisted content fails integrity verification on read."""

    def __init__(self, legal_object_id: str, message: str):
        self.legal_object_id = legal_object_id
        super().__init__(f"retrieval integrity failure for {legal_object_id}: {message}")
