import pytest
from sqlalchemy import select

from app.core.datetime_utils import utc_now
from app.models.extracted_text import ExtractedText
from app.models.extraction_run import ExtractionRun
from app.models.legal_object import LegalObject
from app.models.parsed_structure import ParsedStructure
from app.models.parser_run import ParserRun
from app.models.parsing_trigger_result import ParsingTriggerResult
from app.models.source_version import SourceVersion
from app.services.ingestion.enums import PipelineArtifactState
from app.services.ingestion.extraction_persistence import create_extraction_run, persist_extracted_text
from app.services.extraction.hashing import sha256_text
from app.services.ingestion.hashing import sha256_structure
from app.services.ingestion.ingestion_state import initialize_pipeline_state, update_ingestion_state
from app.services.parsing_trigger import create_parsing_trigger_request
from app.workers.parsing import (
    CONTROLLED_STRUCTURAL_PARSER_NAME,
    ParsingWorker,
    ParsingWorkerError,
    run_controlled_structural_parsing,
    run_parsing_dry_run,
    segment_extracted_text_structurally,
)
from app.workers.parsing.structural import CONTROLLED_STRUCTURAL_PARSER_VERSION
from tests.monitoring_test_helpers import seed_source_document

pytestmark = pytest.mark.integration

SAMPLE_LEGAL_TEXT = """\
VAT LAW 2024

Article 1
Introduction applies to registered persons.

Section 15
Tax is due on supply.

Schedule 1
Return forms listed here.

1. First numbered clause.
(a) Subclause detail.
Plain paragraph line.
"""


def _seed_extracted_text(
    db_session,
    *,
    raw_text: str = SAMPLE_LEGAL_TEXT,
    extraction_status: str = "success",
) -> ExtractedText:
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
        version_status="active",
        notes="controlled parsing test",
        supersedes_version_id=None,
    )
    db_session.add(version)
    db_session.flush()
    initialize_pipeline_state(db_session, source_version_id=version.id)
    started = utc_now()
    run = create_extraction_run(
        db_session,
        source_version_id=version.id,
        extractor_name="test_extractor",
        extractor_version="1.0.0",
        extraction_status=extraction_status,
        started_at=started,
        completed_at=utc_now(),
        content_hash=sha256_text(raw_text),
        raw_text_length=len(raw_text),
    )
    extracted = persist_extracted_text(
        db_session,
        extraction_run_id=run.id,
        raw_text=raw_text,
    )
    if extraction_status not in {"success", "partial"}:
        update_ingestion_state(
            db_session,
            source_version_id=version.id,
            pipeline_state=PipelineArtifactState.FAILED.value,
            extraction_run_id=run.id,
        )
    return extracted


def _trigger(db_session, extracted: ExtractedText, **kwargs):
    return create_parsing_trigger_request(
        db_session,
        extracted_text_id=extracted.id,
        requested_by_actor_type="worker",
        trigger_reason=kwargs.get("trigger_reason", "controlled parse"),
        force_reparse=kwargs.get("force_reparse", False),
    )


def test_controlled_parsing_success_creates_parser_run_and_structure(db_session):
    extracted = _seed_extracted_text(db_session)
    request = _trigger(db_session, extracted)

    summary = run_controlled_structural_parsing(db_session, controlled_structural=True)

    assert summary.triggers_processed == 1
    assert summary.parser_runs_created == 1
    assert summary.failures == 0

    run = db_session.execute(select(ParserRun)).scalar_one()
    assert run.parser_name == CONTROLLED_STRUCTURAL_PARSER_NAME
    assert run.parser_version == CONTROLLED_STRUCTURAL_PARSER_VERSION
    assert run.parser_status == "success"

    structure = db_session.execute(select(ParsedStructure)).scalar_one()
    assert structure.parser_run_id == run.id
    assert structure.structure_hash == sha256_structure(structure.structure_json["units"])
    assert structure.structure_json["parser_name"] == CONTROLLED_STRUCTURAL_PARSER_NAME
    assert structure.structure_json["document"]["unit_count"] > 0

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


def test_structure_hash_deterministic():
    units_one, _ = segment_extracted_text_structurally(SAMPLE_LEGAL_TEXT)
    units_two, _ = segment_extracted_text_structurally(SAMPLE_LEGAL_TEXT)
    assert sha256_structure(units_one) == sha256_structure(units_two)


def test_headings_sections_articles_detected():
    units, envelope = segment_extracted_text_structurally(SAMPLE_LEGAL_TEXT)
    types = {u["unit_type"] for u in units}
    assert "article" in types
    assert "section" in types
    assert "schedule" in types
    assert "paragraph" in types or "clause" in types
    assert envelope["document"]["unit_count"] == len(units)


def test_empty_text_fails_safely(db_session):
    extracted = _seed_extracted_text(db_session, raw_text="placeholder")
    _trigger(db_session, extracted)
    extracted.raw_text = "   "
    db_session.flush()

    summary = run_controlled_structural_parsing(db_session, controlled_structural=True)
    assert summary.triggers_skipped == 1
    assert summary.parser_runs_created == 0
    assert db_session.query(ParsedStructure).count() == 0


def test_empty_text_segmentation_raises():
    with pytest.raises(ValueError, match="extracted_text_not_eligible"):
        segment_extracted_text_structurally("   ")


def test_unstructured_text_handled_as_paragraph_or_unknown():
    units, _ = segment_extracted_text_structurally("Single block of text without headings.")
    assert len(units) >= 1
    assert units[0]["unit_type"] in {"paragraph", "unknown", "heading"}


def test_completed_not_reprocessed(db_session):
    extracted = _seed_extracted_text(db_session)
    _trigger(db_session, extracted)
    first = run_controlled_structural_parsing(db_session, controlled_structural=True)
    assert first.parser_runs_created == 1

    second = run_controlled_structural_parsing(db_session, controlled_structural=True)
    assert second.triggers_processed == 0
    assert second.triggers_skipped == 1
    assert db_session.query(ParserRun).count() == 1
    assert db_session.query(ParsedStructure).count() == 1


def test_force_reparse_allows_new_run_and_structure(db_session):
    extracted = _seed_extracted_text(db_session)
    _trigger(db_session, extracted, force_reparse=False)
    _ = run_controlled_structural_parsing(db_session, controlled_structural=True)

    _trigger(db_session, extracted, force_reparse=True, trigger_reason="replay")
    second = run_controlled_structural_parsing(db_session, controlled_structural=True)
    assert second.parser_runs_created == 1
    assert db_session.query(ParserRun).count() == 2
    assert db_session.query(ParsedStructure).count() == 2


def test_non_controlled_structural_runner_rejected():
    with pytest.raises(ParsingWorkerError):
        run_controlled_structural_parsing(None, controlled_structural=False)  # type: ignore[arg-type]


def test_invalid_execution_mode_rejected():
    from app.workers.parsing.dry_run_provider import DryRunParsingProvider

    with pytest.raises(ParsingWorkerError):
        ParsingWorker(provider=DryRunParsingProvider(), mode="live")


def test_dry_run_worker_still_passes(db_session):
    extracted = _seed_extracted_text(db_session)
    _trigger(db_session, extracted)
    summary = run_parsing_dry_run(db_session, dry_run=True)
    assert summary.triggers_processed == 1
    assert summary.parser_runs_created == 1
    assert db_session.query(ParsedStructure).count() == 0


def test_no_legal_object_or_downstream_side_effects(db_session):
    extracted = _seed_extracted_text(db_session)
    legal_before = db_session.query(LegalObject).count()
    _trigger(db_session, extracted)
    _ = run_controlled_structural_parsing(db_session, controlled_structural=True)
    assert db_session.query(LegalObject).count() == legal_before

    structure = db_session.execute(select(ParsedStructure)).scalar_one()
    blob = str(structure.structure_json).lower()
    for forbidden in (
        "tax_effect",
        "applicability",
        "legal_consequence",
        "obligation",
        "interpretation",
    ):
        assert forbidden not in blob


def test_forbidden_imports_not_introduced():
    from pathlib import Path

    parsing_dir = Path(__file__).resolve().parents[1] / "app" / "workers" / "parsing"
    forbidden = (
        "requests",
        "httpx",
        "openai",
        "anthropic",
        "spacy",
        "nltk",
        "pytesseract",
        "pdfplumber",
        "selenium",
    )
    for path in parsing_dir.glob("*.py"):
        content = path.read_text().lower()
        for lib in forbidden:
            assert f"import {lib}" not in content
            assert f"from {lib} import" not in content
