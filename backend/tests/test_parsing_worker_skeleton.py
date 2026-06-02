import pytest
from sqlalchemy import select

from app.core.datetime_utils import utc_now
from app.models.extracted_text import ExtractedText
from app.models.extraction_run import ExtractionRun
from app.models.legal_object import LegalObject
from app.models.parsed_structure import ParsedStructure
from app.models.parser_run import ParserRun
from app.models.parsing_trigger_result import ParsingTriggerResult
from app.models.source_document import SourceDocument
from app.models.source_version import SourceVersion
from app.services.parsing_trigger import (
    create_parsing_trigger_request,
    persist_parsing_trigger_result,
)
from app.workers.parsing import (
    DRY_RUN_PARSER_NAME,
    ParsingProviderResult,
    ParsingWorker,
    ParsingWorkerError,
    run_parsing_dry_run,
)
from app.workers.parsing.dry_run_provider import ParsingProvider
from tests.monitoring_test_helpers import seed_source_document

pytestmark = pytest.mark.integration


class FailingParsingProvider(ParsingProvider):
    def run_parsing(self, extracted_text, trigger_request):
        _ = extracted_text, trigger_request
        return ParsingProviderResult(
            success=False,
            error_category="parsing_pipeline_unavailable",
            error_message="synthetic provider failure",
        )


def _seed_extracted_text(
    db_session,
    *,
    source_doc=None,
    checksum_suffix: str = "a",
    extraction_status: str = "success",
) -> ExtractedText:
    source_doc = source_doc or seed_source_document(db_session)
    version = SourceVersion(
        source_document_id=source_doc.id,
        version_label=f"v-{checksum_suffix}",
        publication_date=None,
        effective_from=None,
        effective_to=None,
        enforcement_date=None,
        retrieved_at=utc_now(),
        checksum_sha256=checksum_suffix * 64,
        storage_path="/fixtures/source-v1.json",
        mime_type="application/json",
        file_size=120,
        version_status="active",
        notes="seed for parsing worker tests",
        supersedes_version_id=None,
    )
    db_session.add(version)
    db_session.flush()
    run = ExtractionRun(
        source_version_id=version.id,
        extractor_name="test_extractor",
        extractor_version="1.0.0",
        extraction_status=extraction_status,
        started_at=utc_now(),
        completed_at=utc_now(),
        content_hash="b" * 64,
        raw_text_length=20,
    )
    db_session.add(run)
    db_session.flush()
    extracted = ExtractedText(
        extraction_run_id=run.id,
        source_version_id=version.id,
        content_hash="c" * 64,
        raw_text="Article 1\nTax applies.",
        storage_backend="database",
    )
    db_session.add(extracted)
    db_session.flush()
    return extracted


def test_invalid_execution_mode_rejected():
    with pytest.raises(ParsingWorkerError):
        ParsingWorker(provider=FailingParsingProvider(), mode="live")


def test_non_dry_run_runner_rejected():
    with pytest.raises(ParsingWorkerError):
        run_parsing_dry_run(None, dry_run=False)  # type: ignore[arg-type]


def test_dry_run_worker_processes_eligible_trigger(db_session):
    extracted = _seed_extracted_text(db_session)
    request = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="worker",
        trigger_reason="dry-run orchestration",
    )

    summary = run_parsing_dry_run(db_session, dry_run=True)

    assert summary.triggers_seen == 1
    assert summary.triggers_processed == 1
    assert summary.triggers_skipped == 0
    assert summary.parser_runs_created == 1
    assert summary.trigger_results_created == 4
    assert summary.failures == 0

    run = db_session.execute(select(ParserRun)).scalar_one()
    assert run.extraction_run_id == extracted.extraction_run_id
    assert run.parser_name == DRY_RUN_PARSER_NAME
    assert run.parser_version == "0.1.0"
    assert run.parser_status == "success"

    latest = (
        db_session.execute(
            select(ParsingTriggerResult)
            .where(ParsingTriggerResult.parsing_trigger_request_id == request.id)
            .order_by(ParsingTriggerResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest is not None
    assert latest.trigger_status == "completed"
    assert latest.parser_run_id == run.id


def test_completed_trigger_not_reprocessed(db_session):
    extracted = _seed_extracted_text(db_session)
    request = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="worker",
        trigger_reason="first run",
    )
    first = run_parsing_dry_run(db_session, dry_run=True)
    assert first.parser_runs_created == 1

    second = run_parsing_dry_run(db_session, dry_run=True)
    assert second.triggers_seen == 1
    assert second.triggers_processed == 0
    assert second.triggers_skipped == 1
    assert second.parser_runs_created == 0

    runs = db_session.execute(select(ParserRun)).scalars().all()
    assert len(runs) == 1
    assert runs[0].id == (
        db_session.execute(
            select(ParsingTriggerResult)
            .where(ParsingTriggerResult.parsing_trigger_request_id == request.id)
            .where(ParsingTriggerResult.trigger_status == "completed")
        )
        .scalar_one()
        .parser_run_id
    )


def test_force_reparse_allows_new_parser_run(db_session):
    extracted = _seed_extracted_text(db_session)
    create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="worker",
        trigger_reason="initial",
        force_reparse=False,
    )
    _ = run_parsing_dry_run(db_session, dry_run=True)

    create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="worker",
        trigger_reason="initial",
        force_reparse=True,
    )
    second = run_parsing_dry_run(db_session, dry_run=True)
    assert second.triggers_processed == 1
    assert second.parser_runs_created == 1
    assert db_session.query(ParserRun).count() == 2


def test_rejected_and_duplicate_rejected_triggers_skipped(db_session):
    source_doc = seed_source_document(db_session)
    extracted_a = _seed_extracted_text(db_session, source_doc=source_doc, checksum_suffix="a")
    extracted_b = _seed_extracted_text(db_session, source_doc=source_doc, checksum_suffix="b")

    rejected = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted_a.id,
        requested_by_actor_type="worker",
        trigger_reason="rejected path",
    )
    persist_parsing_trigger_result(
        db_session,
        parsing_trigger_request_id=rejected.id,
        trigger_status="rejected",
        error_category="invalid_request",
        error_message="manual rejection",
    )

    duplicate = create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted_b.id,
        requested_by_actor_type="admin",
        trigger_reason="duplicate path",
    )
    persist_parsing_trigger_result(
        db_session,
        parsing_trigger_request_id=duplicate.id,
        trigger_status="duplicate_rejected",
        error_category="invalid_request",
        error_message="duplicate trigger",
    )

    summary = run_parsing_dry_run(db_session, dry_run=True)
    assert summary.triggers_seen == 2
    assert summary.triggers_processed == 0
    assert summary.triggers_skipped == 2
    assert summary.parser_runs_created == 0


def test_provider_failure_records_failed_trigger_result(db_session):
    extracted = _seed_extracted_text(db_session)
    create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="worker",
        trigger_reason="provider failure path",
    )

    worker = ParsingWorker(provider=FailingParsingProvider(), mode="dry_run")
    summary = worker.run(db_session)

    assert summary.triggers_processed == 1
    assert summary.failures == 1
    assert summary.parser_runs_created == 1

    latest = (
        db_session.execute(
            select(ParsingTriggerResult).order_by(ParsingTriggerResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest is not None
    assert latest.trigger_status == "failed"
    assert latest.error_category == "parsing_pipeline_unavailable"
    run = db_session.execute(select(ParserRun)).scalar_one()
    assert run.parser_status == "failed"


def test_summary_counts_with_multiple_eligible_triggers(db_session):
    source_doc = None
    for idx in range(3):
        extracted = _seed_extracted_text(
            db_session, source_doc=source_doc, checksum_suffix=str(idx)
        )
        if source_doc is None:
            version = db_session.get(SourceVersion, extracted.source_version_id)
            source_doc = db_session.get(SourceDocument, version.source_document_id)
        create_parsing_trigger_request(
            db_session,
            extracted_text_id=extracted.id,
            requested_by_actor_type="worker",
            trigger_reason="multi-trigger",
        )

    summary = run_parsing_dry_run(db_session, dry_run=True)
    assert summary.triggers_seen == 3
    assert summary.triggers_processed == 3
    assert summary.triggers_skipped == 0
    assert summary.parser_runs_created == 3
    assert summary.trigger_results_created == 12
    assert summary.failures == 0


def test_no_side_effects_on_downstream_artifacts(db_session):
    extracted = _seed_extracted_text(db_session)
    parsed_before = db_session.query(ParsedStructure).count()
    legal_before = db_session.query(LegalObject).count()

    create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="worker",
        trigger_reason="no downstream side effects",
    )
    _ = run_parsing_dry_run(db_session, dry_run=True)

    assert db_session.query(ParsedStructure).count() == parsed_before
    assert db_session.query(LegalObject).count() == legal_before


def test_no_parsing_nlp_ai_imports_introduced():
    from pathlib import Path

    worker_dir = Path(__file__).resolve().parents[1] / "app" / "workers" / "parsing"
    forbidden = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib3",
        "spacy",
        "nltk",
        "openai",
        "anthropic",
        "transformers",
    )
    for path in worker_dir.glob("*.py"):
        content = path.read_text().lower()
        for lib in forbidden:
            assert f"import {lib}" not in content
            assert f"from {lib} import" not in content
