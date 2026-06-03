import pytest
from sqlalchemy import select

from app.models.legal_object import LegalObject
from app.models.legal_object_promotion_result import LegalObjectPromotionResult
from app.models.legal_object_version import LegalObjectVersion
from app.models.parsed_structure import ParsedStructure
from app.services.legal_object_promotion import (
    create_promotion_request,
    persist_promotion_result,
)
from app.workers.legal_object_promotion import (
    DRY_RUN_TERMINAL_STATUS,
    LegalObjectPromotionProviderResult,
    LegalObjectPromotionWorker,
    LegalObjectPromotionWorkerError,
    run_legal_object_promotion_dry_run,
)
from app.workers.legal_object_promotion.dry_run_provider import LegalObjectPromotionProvider
from app.core.datetime_utils import utc_now
from app.models.extraction_run import ExtractionRun
from app.models.extracted_text import ExtractedText
from app.models.parsed_structure import ParsedStructure
from app.models.parser_run import ParserRun
from app.models.source_version import SourceVersion
from app.services.ingestion.enums import ParserRunStatus, STRUCTURE_TYPE_STRUCTURAL_UNITS
from app.services.ingestion.hashing import sha256_structure
from tests.monitoring_test_helpers import seed_source_document
from tests.test_legal_object_promotion_persistence import _UNITS, _seed_parsed_structure

pytestmark = pytest.mark.integration


def _seed_parsed_structure_for_doc(
    db_session,
    *,
    source_doc,
    checksum_suffix: str,
):
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
        notes="promotion worker multi-seed",
        supersedes_version_id=None,
    )
    db_session.add(version)
    db_session.flush()
    run = ExtractionRun(
        source_version_id=version.id,
        extractor_name="test_extractor",
        extractor_version="1.0.0",
        extraction_status="success",
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
    parser_run = ParserRun(
        extraction_run_id=run.id,
        parser_name="test_parser",
        parser_version="1.0.0",
        parser_status=ParserRunStatus.SUCCESS.value,
        started_at=utc_now(),
        completed_at=utc_now(),
    )
    db_session.add(parser_run)
    db_session.flush()
    structure_hash = sha256_structure(_UNITS)
    parsed = ParsedStructure(
        parser_run_id=parser_run.id,
        source_version_id=version.id,
        structure_type=STRUCTURE_TYPE_STRUCTURAL_UNITS,
        structure_json={"structure_type": STRUCTURE_TYPE_STRUCTURAL_UNITS, "units": _UNITS},
        structure_hash=structure_hash,
    )
    db_session.add(parsed)
    db_session.flush()
    return parsed, extracted


class FailingLegalObjectPromotionProvider(LegalObjectPromotionProvider):
    def run_promotion(self, db, parsed_structure, promotion_request):
        _ = db, parsed_structure, promotion_request
        return LegalObjectPromotionProviderResult(
            success=False,
            error_category="promotion_pipeline_unavailable",
            error_message="synthetic provider failure",
        )


def test_invalid_execution_mode_rejected():
    with pytest.raises(LegalObjectPromotionWorkerError):
        LegalObjectPromotionWorker(
            provider=FailingLegalObjectPromotionProvider(),
            mode="live",
        )


def test_non_dry_run_runner_rejected():
    with pytest.raises(LegalObjectPromotionWorkerError):
        run_legal_object_promotion_dry_run(None, dry_run=False)  # type: ignore[arg-type]


def test_dry_run_worker_processes_eligible_promotion_request(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    request = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="dry-run orchestration",
    )

    summary = run_legal_object_promotion_dry_run(db_session, dry_run=True)

    assert summary.requests_seen == 1
    assert summary.requests_processed == 1
    assert summary.requests_skipped == 0
    assert summary.results_created == 2
    assert summary.failures == 0

    latest = (
        db_session.execute(
            select(LegalObjectPromotionResult)
            .where(LegalObjectPromotionResult.legal_object_promotion_request_id == request.id)
            .order_by(LegalObjectPromotionResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest is not None
    assert latest.promotion_status == DRY_RUN_TERMINAL_STATUS
    assert latest.legal_object_id is None
    assert latest.promoted_at is None


def test_terminal_request_not_reprocessed(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    request = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="first run",
    )
    first = run_legal_object_promotion_dry_run(db_session, dry_run=True)
    assert first.requests_processed == 1

    second = run_legal_object_promotion_dry_run(db_session, dry_run=True)
    assert second.requests_seen == 1
    assert second.requests_processed == 0
    assert second.requests_skipped == 1
    assert second.results_created == 0

    results = (
        db_session.execute(
            select(LegalObjectPromotionResult)
            .where(LegalObjectPromotionResult.legal_object_promotion_request_id == request.id)
        )
        .scalars()
        .all()
    )
    assert len(results) == 2


def test_force_repromotion_allows_replay(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="initial",
        force_repromotion=False,
    )
    _ = run_legal_object_promotion_dry_run(db_session, dry_run=True)

    replay = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="replay",
        force_repromotion=True,
    )
    second = run_legal_object_promotion_dry_run(db_session, dry_run=True)
    assert second.requests_processed == 1
    assert second.results_created == 2

    replay_results = (
        db_session.execute(
            select(LegalObjectPromotionResult)
            .where(LegalObjectPromotionResult.legal_object_promotion_request_id == replay.id)
        )
        .scalars()
        .all()
    )
    assert len(replay_results) == 2
    assert replay_results[-1].promotion_status == DRY_RUN_TERMINAL_STATUS


def test_rejected_and_duplicate_rejected_requests_skipped(db_session):
    source_doc = seed_source_document(db_session)
    parsed_a, extracted_a = _seed_parsed_structure_for_doc(
        db_session, source_doc=source_doc, checksum_suffix="a"
    )
    parsed_b, extracted_b = _seed_parsed_structure_for_doc(
        db_session, source_doc=source_doc, checksum_suffix="b"
    )

    rejected = create_promotion_request(
        db_session,
        parsed_structure_id=parsed_a.id,
        source_version_id=extracted_a.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="rejected path",
    )
    persist_promotion_result(
        db_session,
        legal_object_promotion_request_id=rejected.id,
        promotion_status="rejected",
        error_category="invalid_request",
        error_message="manual rejection",
    )

    duplicate = create_promotion_request(
        db_session,
        parsed_structure_id=parsed_b.id,
        source_version_id=extracted_b.source_version_id,
        requested_by_actor_type="admin",
        promotion_reason="duplicate path",
    )
    persist_promotion_result(
        db_session,
        legal_object_promotion_request_id=duplicate.id,
        promotion_status="duplicate_rejected",
        error_category="duplicate_promotion",
        error_message="duplicate promotion",
    )

    summary = run_legal_object_promotion_dry_run(db_session, dry_run=True)
    assert summary.requests_seen == 2
    assert summary.requests_processed == 0
    assert summary.requests_skipped == 2
    assert summary.results_created == 0


def test_provider_failure_records_failed_result(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="provider failure path",
    )

    worker = LegalObjectPromotionWorker(
        provider=FailingLegalObjectPromotionProvider(),
        mode="dry_run",
    )
    summary = worker.run(db_session)

    assert summary.requests_processed == 1
    assert summary.failures == 1
    assert summary.results_created == 2

    latest = (
        db_session.execute(
            select(LegalObjectPromotionResult).order_by(LegalObjectPromotionResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest is not None
    assert latest.promotion_status == "failed"
    assert latest.error_category == "promotion_pipeline_unavailable"
    assert latest.legal_object_id is None


def test_summary_counts_with_multiple_eligible_requests(db_session):
    source_doc = seed_source_document(db_session)
    for idx in range(3):
        parsed, extracted = _seed_parsed_structure_for_doc(
            db_session, source_doc=source_doc, checksum_suffix=str(idx)
        )
        create_promotion_request(
            db_session,
            parsed_structure_id=parsed.id,
            source_version_id=extracted.source_version_id,
            requested_by_actor_type="worker",
            promotion_reason=f"multi-request-{idx}",
        )

    summary = run_legal_object_promotion_dry_run(db_session, dry_run=True)
    assert summary.requests_seen == 3
    assert summary.requests_processed == 3
    assert summary.requests_skipped == 0
    assert summary.results_created == 6
    assert summary.failures == 0


def test_no_side_effects_on_legal_memory(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    legal_before = db_session.query(LegalObject).count()
    version_before = db_session.query(LegalObjectVersion).count()
    parsed_before = db_session.query(ParsedStructure).count()

    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="no legal memory side effects",
    )
    _ = run_legal_object_promotion_dry_run(db_session, dry_run=True)

    assert db_session.query(LegalObject).count() == legal_before
    assert db_session.query(LegalObjectVersion).count() == version_before
    assert db_session.query(ParsedStructure).count() == parsed_before


def test_dry_run_does_not_use_promoted_status(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="status discipline",
    )
    _ = run_legal_object_promotion_dry_run(db_session, dry_run=True)

    promoted_rows = (
        db_session.execute(
            select(LegalObjectPromotionResult).where(
                LegalObjectPromotionResult.promotion_status == "promoted"
            )
        )
        .scalars()
        .all()
    )
    assert promoted_rows == []


def test_no_promotion_ai_imports_introduced():
    from pathlib import Path

    worker_dir = (
        Path(__file__).resolve().parents[1] / "app" / "workers" / "legal_object_promotion"
    )
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
