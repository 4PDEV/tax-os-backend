import pytest
from sqlalchemy import select

from app.core.datetime_utils import utc_now
from app.models.extracted_text import ExtractedText
from app.models.extraction_run import ExtractionRun
from app.models.extraction_trigger_result import ExtractionTriggerResult
from app.models.legal_object import LegalObject
from app.models.parsed_structure import ParsedStructure
from app.models.source_version import SourceVersion
from app.services.extraction_trigger import (
    create_extraction_trigger_request,
    persist_extraction_trigger_result,
)
from app.workers.extraction import (
    DRY_RUN_EXTRACTOR_NAME,
    ExtractionProviderResult,
    ExtractionWorker,
    ExtractionWorkerError,
    run_extraction_dry_run,
)
from app.workers.extraction.dry_run_provider import ExtractionProvider
from tests.monitoring_test_helpers import seed_source_document

pytestmark = pytest.mark.integration


class FailingExtractionProvider(ExtractionProvider):
    def run_extraction(self, source_version, trigger_request):
        _ = source_version, trigger_request
        return ExtractionProviderResult(
            success=False,
            error_category="extraction_pipeline_unavailable",
            error_message="synthetic provider failure",
        )


def _seed_source_version(db_session, *, status: str = "active") -> SourceVersion:
    source_doc = seed_source_document(db_session)
    version = SourceVersion(
        source_document_id=source_doc.id,
        version_label="v1",
        publication_date=None,
        effective_from=None,
        effective_to=None,
        enforcement_date=None,
        retrieved_at=utc_now(),
        checksum_sha256="a" * 64,
        storage_path="/fixtures/source-v1.json",
        mime_type="application/json",
        file_size=120,
        version_status=status,
        notes="seed source version for extraction worker tests",
        supersedes_version_id=None,
    )
    db_session.add(version)
    db_session.flush()
    return version


def test_invalid_execution_mode_rejected():
    with pytest.raises(ExtractionWorkerError):
        ExtractionWorker(provider=FailingExtractionProvider(), mode="live")


def test_non_dry_run_runner_rejected():
    with pytest.raises(ExtractionWorkerError):
        run_extraction_dry_run(None, dry_run=False)  # type: ignore[arg-type]


def test_dry_run_worker_processes_eligible_trigger(db_session):
    source_version = _seed_source_version(db_session)
    request = create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="dry-run orchestration",
    )

    summary = run_extraction_dry_run(db_session, dry_run=True)

    assert summary.triggers_seen == 1
    assert summary.triggers_processed == 1
    assert summary.triggers_skipped == 0
    assert summary.extraction_runs_created == 1
    assert summary.trigger_results_created == 4
    assert summary.failures == 0

    run = db_session.execute(select(ExtractionRun)).scalar_one()
    assert run.source_version_id == source_version.id
    assert run.extractor_name == DRY_RUN_EXTRACTOR_NAME
    assert run.extractor_version == "0.1.0"
    assert run.extraction_status == "success"

    latest = (
        db_session.execute(
            select(ExtractionTriggerResult)
            .where(ExtractionTriggerResult.extraction_trigger_request_id == request.id)
            .order_by(ExtractionTriggerResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest is not None
    assert latest.trigger_status == "completed"
    assert latest.extraction_run_id == run.id


def test_completed_trigger_not_reprocessed(db_session):
    source_version = _seed_source_version(db_session)
    request = create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="first run",
    )
    first = run_extraction_dry_run(db_session, dry_run=True)
    assert first.extraction_runs_created == 1

    second = run_extraction_dry_run(db_session, dry_run=True)
    assert second.triggers_seen == 1
    assert second.triggers_processed == 0
    assert second.triggers_skipped == 1
    assert second.extraction_runs_created == 0

    runs = db_session.execute(select(ExtractionRun)).scalars().all()
    assert len(runs) == 1
    assert runs[0].id == (
        db_session.execute(
            select(ExtractionTriggerResult)
            .where(ExtractionTriggerResult.extraction_trigger_request_id == request.id)
            .where(ExtractionTriggerResult.trigger_status == "completed")
        )
        .scalar_one()
        .extraction_run_id
    )


def test_force_reprocess_allows_new_run(db_session):
    source_version = _seed_source_version(db_session)
    create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="initial",
        force_reprocess=False,
    )
    _ = run_extraction_dry_run(db_session, dry_run=True)

    create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="initial",
        force_reprocess=True,
    )
    second = run_extraction_dry_run(db_session, dry_run=True)
    assert second.triggers_processed == 1
    assert second.extraction_runs_created == 1
    assert db_session.query(ExtractionRun).count() == 2


def test_rejected_and_duplicate_rejected_triggers_skipped(db_session):
    source_version = _seed_source_version(db_session)
    rejected = create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="rejected path",
    )
    persist_extraction_trigger_result(
        db_session,
        extraction_trigger_request_id=rejected.id,
        trigger_status="rejected",
        error_category="invalid_request",
        error_message="manual rejection",
    )

    duplicate = create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="admin",
        trigger_reason="duplicate path",
    )
    persist_extraction_trigger_result(
        db_session,
        extraction_trigger_request_id=duplicate.id,
        trigger_status="duplicate_rejected",
        error_category="invalid_request",
        error_message="duplicate trigger",
    )

    summary = run_extraction_dry_run(db_session, dry_run=True)
    assert summary.triggers_seen == 2
    assert summary.triggers_processed == 0
    assert summary.triggers_skipped == 2
    assert summary.extraction_runs_created == 0


def test_provider_failure_records_failed_trigger_result(db_session):
    source_version = _seed_source_version(db_session)
    create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="provider failure path",
    )

    worker = ExtractionWorker(provider=FailingExtractionProvider(), mode="dry_run")
    summary = worker.run(db_session)

    assert summary.triggers_processed == 1
    assert summary.failures == 1
    assert summary.extraction_runs_created == 1

    latest = (
        db_session.execute(
            select(ExtractionTriggerResult).order_by(ExtractionTriggerResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest is not None
    assert latest.trigger_status == "failed"
    assert latest.error_category == "extraction_pipeline_unavailable"
    run = db_session.execute(select(ExtractionRun)).scalar_one()
    assert run.extraction_status == "failed"


def test_summary_counts_with_multiple_eligible_triggers(db_session):
    source_doc = seed_source_document(db_session)
    for idx in range(3):
        version = SourceVersion(
            source_document_id=source_doc.id,
            version_label=f"v-{idx}",
            publication_date=None,
            effective_from=None,
            effective_to=None,
            enforcement_date=None,
            retrieved_at=utc_now(),
            checksum_sha256=f"{idx}" * 64,
            storage_path=f"/fixtures/source-v{idx}.json",
            mime_type="application/json",
            file_size=120,
            version_status="active",
            notes="multi-trigger worker test",
            supersedes_version_id=None,
        )
        db_session.add(version)
        db_session.flush()
        create_extraction_trigger_request(
            db_session,
            source_version_id=version.id,
            requested_by_actor_type="worker",
            trigger_reason=f"trigger-{idx}",
        )

    summary = run_extraction_dry_run(db_session, dry_run=True)
    assert summary.triggers_seen == 3
    assert summary.triggers_processed == 3
    assert summary.triggers_skipped == 0
    assert summary.extraction_runs_created == 3
    assert summary.trigger_results_created == 12
    assert summary.failures == 0


def test_no_side_effects_on_downstream_artifacts(db_session):
    source_version = _seed_source_version(db_session)
    extracted_before = db_session.query(ExtractedText).count()
    parsed_before = db_session.query(ParsedStructure).count()
    legal_before = db_session.query(LegalObject).count()

    create_extraction_trigger_request(
        db_session,
        source_version_id=source_version.id,
        requested_by_actor_type="worker",
        trigger_reason="no downstream side effects",
    )
    _ = run_extraction_dry_run(db_session, dry_run=True)

    assert db_session.query(ExtractedText).count() == extracted_before
    assert db_session.query(ParsedStructure).count() == parsed_before
    assert db_session.query(LegalObject).count() == legal_before


def test_no_network_ocr_pdf_ai_imports_introduced():
    from pathlib import Path

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
        "openai",
        "anthropic",
    )
    for path in worker_dir.glob("*.py"):
        content = path.read_text().lower()
        for lib in forbidden:
            assert f"import {lib}" not in content
            assert f"from {lib} import" not in content
