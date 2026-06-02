from pathlib import Path

import pytest
from sqlalchemy import select

from app.core.datetime_utils import utc_now
from app.models.extracted_text import ExtractedText
from app.models.extraction_run import ExtractionRun
from app.models.extraction_trigger_result import ExtractionTriggerResult
from app.models.legal_object import LegalObject
from app.models.parsed_structure import ParsedStructure
from app.models.source_version import SourceVersion
from app.services.extraction_trigger import create_extraction_trigger_request
from app.workers.extraction import (
    CONTROLLED_LOCAL_EXTRACTOR_NAME,
    ExtractionWorkerError,
    run_controlled_local_extraction,
    run_extraction_dry_run,
)
from app.workers.extraction.safety import resolve_artifact_path
from tests.monitoring_test_helpers import seed_source_document

pytestmark = pytest.mark.integration


def _fixture_root() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "fetch"


def _seed_source_version(
    db_session,
    *,
    storage_path: str,
    mime_type: str,
    checksum: str = "a" * 64,
) -> SourceVersion:
    source_doc = seed_source_document(db_session)
    version = SourceVersion(
        source_document_id=source_doc.id,
        version_label="v1",
        publication_date=None,
        effective_from=None,
        effective_to=None,
        enforcement_date=None,
        retrieved_at=utc_now(),
        checksum_sha256=checksum,
        storage_path=storage_path,
        mime_type=mime_type,
        file_size=120,
        version_status="active",
        notes="controlled extraction test",
        supersedes_version_id=None,
    )
    db_session.add(version)
    db_session.flush()
    return version


def _trigger(db_session, source_version: SourceVersion, *, reason: str = "controlled extract"):
    return create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason=reason,
    )


@pytest.mark.parametrize(
    ("filename", "mime_type"),
    [
        ("sample.txt", "text/plain"),
        ("sample.html", "text/html"),
        ("sample.json", "application/json"),
        ("sample.xml", "application/xml"),
    ],
)
def test_controlled_extraction_success_for_supported_formats(db_session, filename, mime_type):
    version = _seed_source_version(
        db_session,
        storage_path=f"/fixtures/{filename}",
        mime_type=mime_type,
        checksum=f"{filename}-hash",
    )
    _trigger(db_session, version, reason=f"extract {filename}")

    summary = run_controlled_local_extraction(
        db_session,
        artifact_root=_fixture_root(),
        controlled_local=True,
    )
    assert summary.triggers_processed == 1
    assert summary.extraction_runs_created == 1
    assert summary.failures == 0

    run = db_session.execute(select(ExtractionRun)).scalar_one()
    assert run.extractor_name == CONTROLLED_LOCAL_EXTRACTOR_NAME
    assert run.extraction_status in {"success", "partial"}
    assert run.content_hash is not None
    assert run.raw_text_length is not None

    extracted = db_session.execute(select(ExtractedText)).scalar_one()
    assert extracted.extraction_run_id == run.id
    assert extracted.raw_text
    assert extracted.content_hash == run.content_hash

    latest = (
        db_session.execute(
            select(ExtractionTriggerResult)
            .where(ExtractionTriggerResult.trigger_status == "completed")
        )
        .scalars()
        .first()
    )
    assert latest is not None
    assert latest.extraction_run_id == run.id


def test_unsupported_binary_rejected_without_extracted_text(db_session):
    version = _seed_source_version(
        db_session,
        storage_path="/fixtures/sample.bin",
        mime_type="application/octet-stream",
        checksum="b" * 64,
    )
    _trigger(db_session, version, reason="unsupported binary")

    summary = run_controlled_local_extraction(
        db_session,
        artifact_root=_fixture_root(),
        controlled_local=True,
    )
    assert summary.failures == 1
    assert db_session.query(ExtractedText).count() == 0

    run = db_session.execute(select(ExtractionRun)).scalar_one()
    assert run.extraction_status == "failed"

    latest = (
        db_session.execute(
            select(ExtractionTriggerResult).order_by(ExtractionTriggerResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest is not None
    assert latest.trigger_status == "failed"


def test_path_traversal_rejected(db_session):
    version = _seed_source_version(
        db_session,
        storage_path="../../../etc/passwd",
        mime_type="text/plain",
        checksum="c" * 64,
    )
    _trigger(db_session, version, reason="traversal")

    summary = run_controlled_local_extraction(
        db_session,
        artifact_root=_fixture_root(),
        controlled_local=True,
    )
    assert summary.failures == 1
    assert db_session.query(ExtractedText).count() == 0


def test_outside_root_rejected(db_session, tmp_path):
    artifact_root = tmp_path / "approved"
    artifact_root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside root", encoding="utf-8")
    version = _seed_source_version(
        db_session,
        storage_path="../outside.txt",
        mime_type="text/plain",
        checksum="d" * 64,
    )
    _trigger(db_session, version, reason="outside root")

    summary = run_controlled_local_extraction(
        db_session,
        artifact_root=artifact_root,
        controlled_local=True,
    )
    assert summary.failures == 1
    assert db_session.query(ExtractedText).count() == 0


def test_max_size_rejection(db_session):
    version = _seed_source_version(
        db_session,
        storage_path="/fixtures/sample.txt",
        mime_type="text/plain",
        checksum="e" * 64,
    )
    _trigger(db_session, version, reason="max size")

    summary = run_controlled_local_extraction(
        db_session,
        artifact_root=_fixture_root(),
        controlled_local=True,
        max_content_size_bytes=8,
    )
    assert summary.failures == 1
    assert db_session.query(ExtractedText).count() == 0


def test_idempotency_prevents_duplicate_extraction(db_session):
    version = _seed_source_version(
        db_session,
        storage_path="/fixtures/sample.txt",
        mime_type="text/plain",
        checksum="f" * 64,
    )
    _trigger(db_session, version, reason="idempotent")
    first = run_controlled_local_extraction(
        db_session,
        artifact_root=_fixture_root(),
        controlled_local=True,
    )
    assert first.extraction_runs_created == 1

    second = run_controlled_local_extraction(
        db_session,
        artifact_root=_fixture_root(),
        controlled_local=True,
    )
    assert second.triggers_skipped == 1
    assert db_session.query(ExtractionRun).count() == 1
    assert db_session.query(ExtractedText).count() == 1


def test_force_reprocess_allows_rerun(db_session):
    version = _seed_source_version(
        db_session,
        storage_path="/fixtures/sample.txt",
        mime_type="text/plain",
        checksum="1" * 64,
    )
    create_extraction_trigger_request(
        db_session,
        source_version_id=version.id,
        requested_by_actor_type="worker",
        trigger_reason="rerun",
        force_reprocess=False,
    )
    _ = run_controlled_local_extraction(
        db_session,
        artifact_root=_fixture_root(),
        controlled_local=True,
    )

    create_extraction_trigger_request(
        db_session,
        source_version_id=version.id,
        requested_by_actor_type="worker",
        trigger_reason="rerun",
        force_reprocess=True,
    )
    second = run_controlled_local_extraction(
        db_session,
        artifact_root=_fixture_root(),
        controlled_local=True,
    )
    assert second.extraction_runs_created == 1
    assert db_session.query(ExtractionRun).count() == 2
    assert db_session.query(ExtractedText).count() == 2


def test_dry_run_worker_still_passes(db_session):
    version = _seed_source_version(
        db_session,
        storage_path="/fixtures/sample.txt",
        mime_type="text/plain",
        checksum="2" * 64,
    )
    create_extraction_trigger_request(
        db_session,
        source_version_id=version.id,
        requested_by_actor_type="worker",
        trigger_reason="dry-run still works",
    )
    summary = run_extraction_dry_run(db_session, dry_run=True)
    assert summary.triggers_processed == 1
    assert db_session.query(ExtractedText).count() == 0


def test_no_downstream_artifact_side_effects(db_session):
    version = _seed_source_version(
        db_session,
        storage_path="/fixtures/sample.json",
        mime_type="application/json",
        checksum="3" * 64,
    )
    parsed_before = db_session.query(ParsedStructure).count()
    legal_before = db_session.query(LegalObject).count()
    _trigger(db_session, version, reason="no downstream")

    _ = run_controlled_local_extraction(
        db_session,
        artifact_root=_fixture_root(),
        controlled_local=True,
    )

    assert db_session.query(ParsedStructure).count() == parsed_before
    assert db_session.query(LegalObject).count() == legal_before


def test_controlled_local_mode_explicit_required():
    with pytest.raises(ExtractionWorkerError):
        run_controlled_local_extraction(None, artifact_root=_fixture_root(), controlled_local=False)  # type: ignore[arg-type]


def test_resolve_artifact_path_maps_fixture_storage_path():
    path = resolve_artifact_path(
        artifact_root=_fixture_root(),
        storage_path="/fixtures/sample.txt",
    )
    assert path.name == "sample.txt"
    assert path.exists()


def test_forbidden_imports_not_introduced():
    worker_dir = Path(__file__).resolve().parents[1] / "app" / "workers" / "extraction"
    forbidden = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib3",
        "pytesseract",
        "pdfplumber",
        "pypdf",
        "fitz",
        "playwright",
        "selenium",
        "openai",
        "anthropic",
    )
    for path in worker_dir.glob("*.py"):
        content = path.read_text().lower()
        for lib in forbidden:
            assert f"import {lib}" not in content
            assert f"from {lib} import" not in content
