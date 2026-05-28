import pytest

from app.models.source_version import SourceVersion
from app.services.ingestion_status import (
    INGESTION_STATUS_FAILED,
    INGESTION_STATUS_NOT_STARTED,
    INGESTION_STATUS_PARSED,
    INGESTION_STATUS_PROCESSING,
    INGESTION_STATUS_QUEUED,
    INGESTION_STATUS_SUPERSEDED,
    IngestionStatusError,
    transition_ingestion_status,
    validate_transition,
)


def _version(status: str) -> SourceVersion:
    return SourceVersion(
        source_document_id=None,
        version_label="v1",
        checksum_sha256="a" * 64,
        storage_path="rw/vat/v1.pdf",
        ingestion_status=status,
    )


def test_validate_transition_allows_expected_path():
    validate_transition(INGESTION_STATUS_NOT_STARTED, INGESTION_STATUS_QUEUED)
    validate_transition(INGESTION_STATUS_QUEUED, INGESTION_STATUS_PROCESSING)
    validate_transition(INGESTION_STATUS_PROCESSING, INGESTION_STATUS_PARSED)
    validate_transition(INGESTION_STATUS_PROCESSING, INGESTION_STATUS_FAILED)
    validate_transition(INGESTION_STATUS_FAILED, INGESTION_STATUS_QUEUED)


def test_validate_transition_rejects_invalid_target():
    with pytest.raises(IngestionStatusError):
        validate_transition(INGESTION_STATUS_NOT_STARTED, INGESTION_STATUS_PARSED)


def test_validate_transition_rejects_terminal_superseded_change():
    with pytest.raises(IngestionStatusError):
        validate_transition(INGESTION_STATUS_SUPERSEDED, INGESTION_STATUS_QUEUED)


def test_transition_updates_version_status():
    version = _version(INGESTION_STATUS_NOT_STARTED)
    transition_ingestion_status(version, INGESTION_STATUS_QUEUED)
    assert version.ingestion_status == INGESTION_STATUS_QUEUED
