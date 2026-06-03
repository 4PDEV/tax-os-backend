import pytest
from sqlalchemy import select

from app.core.datetime_utils import utc_now
from app.models.citation_assembly_governance_result import CitationAssemblyGovernanceResult
from app.models.extraction_run import ExtractionRun
from app.models.extracted_text import ExtractedText
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.models.parser_run import ParserRun
from app.models.parsed_structure import ParsedStructure
from app.models.source_version import SourceVersion
from app.services.citation_assembly_governance import (
    create_citation_assembly_request,
    persist_citation_assembly_result,
)
from app.services.ingestion.enums import ParserRunStatus, STRUCTURE_TYPE_STRUCTURAL_UNITS
from app.services.ingestion.hashing import sha256_structure
from app.services.legal_object_promotion import create_promotion_request
from app.workers.citation_assembly_governance import (
    DRY_RUN_TERMINAL_STATUS,
    CitationAssemblyGovernanceProviderResult,
    CitationAssemblyGovernanceWorker,
    CitationAssemblyGovernanceWorkerError,
    run_citation_assembly_governance_dry_run,
)
from app.workers.citation_assembly_governance.dry_run_provider import (
    CitationAssemblyGovernanceProvider,
)
from app.workers.legal_object_promotion import run_controlled_legal_object_promotion
from tests.monitoring_test_helpers import seed_source_document
from tests.test_legal_object_promotion_persistence import _UNITS, _seed_parsed_structure

pytestmark = pytest.mark.integration


def _seed_legal_object_version(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="seed for citation worker",
    )
    run_controlled_legal_object_promotion(db_session, controlled_promotion=True)
    version = db_session.execute(select(LegalObjectVersion)).scalar_one()
    return version, extracted


def _seed_legal_object_version_for_doc(db_session, *, source_doc, checksum_suffix: str):
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
        notes="citation worker multi-seed",
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
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=version.id,
        requested_by_actor_type="worker",
        promotion_reason="promote for citation worker seed",
    )
    run_controlled_legal_object_promotion(db_session, controlled_promotion=True)
    lo_version = (
        db_session.execute(
            select(LegalObjectVersion).where(
                LegalObjectVersion.source_version_id == version.id
            )
        )
        .scalars()
        .one()
    )
    return lo_version, version


class FailingCitationAssemblyGovernanceProvider(CitationAssemblyGovernanceProvider):
    def run_assembly(self, db, request, legal_object_version):
        _ = db, request, legal_object_version
        return CitationAssemblyGovernanceProviderResult(
            success=False,
            error_category="citation_pipeline_unavailable",
            error_message="synthetic provider failure",
        )


def test_invalid_execution_mode_rejected():
    with pytest.raises(CitationAssemblyGovernanceWorkerError):
        CitationAssemblyGovernanceWorker(
            provider=FailingCitationAssemblyGovernanceProvider(),
            mode="controlled_assembly",
        )


def test_non_dry_run_runner_rejected():
    with pytest.raises(CitationAssemblyGovernanceWorkerError):
        run_citation_assembly_governance_dry_run(None, dry_run=False)  # type: ignore[arg-type]


def test_run_citation_assembly_dry_run_alias(db_session):
    from app.workers.citation_assembly_governance import run_citation_assembly_dry_run

    version, extracted = _seed_legal_object_version(db_session)
    create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="runner alias",
    )
    summary = run_citation_assembly_dry_run(db_session, dry_run=True)
    assert summary.requests_processed == 1


def test_lineage_preserved_on_results(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    request = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="lineage check",
    )
    _ = run_citation_assembly_governance_dry_run(db_session, dry_run=True)
    results = (
        db_session.execute(
            select(CitationAssemblyGovernanceResult).where(
                CitationAssemblyGovernanceResult.citation_assembly_governance_request_id
                == request.id
            )
        )
        .scalars()
        .all()
    )
    assert len(results) == 2
    for row in results:
        assert row.legal_object_id == version.legal_object_id
        assert row.legal_object_version_id == version.legal_object_version_id


def test_dry_run_worker_processes_eligible_request(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    request = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="dry-run orchestration",
    )

    summary = run_citation_assembly_governance_dry_run(db_session, dry_run=True)

    assert summary.requests_seen == 1
    assert summary.requests_processed == 1
    assert summary.requests_skipped == 0
    assert summary.results_created == 2
    assert summary.failures == 0

    latest = (
        db_session.execute(
            select(CitationAssemblyGovernanceResult)
            .where(
                CitationAssemblyGovernanceResult.citation_assembly_governance_request_id
                == request.id
            )
            .order_by(CitationAssemblyGovernanceResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest is not None
    assert latest.citation_status == DRY_RUN_TERMINAL_STATUS
    assert latest.citation_id is None
    assert latest.assembled_at is None


def test_terminal_request_not_reprocessed(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    request = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="first run",
    )
    first = run_citation_assembly_governance_dry_run(db_session, dry_run=True)
    assert first.requests_processed == 1

    second = run_citation_assembly_governance_dry_run(db_session, dry_run=True)
    assert second.requests_seen == 1
    assert second.requests_processed == 0
    assert second.requests_skipped == 1
    assert second.results_created == 0

    results = (
        db_session.execute(
            select(CitationAssemblyGovernanceResult).where(
                CitationAssemblyGovernanceResult.citation_assembly_governance_request_id
                == request.id
            )
        )
        .scalars()
        .all()
    )
    assert len(results) == 2


def test_force_reassembly_allows_replay(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="initial",
        force_reassembly=False,
    )
    _ = run_citation_assembly_governance_dry_run(db_session, dry_run=True)

    replay = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="replay",
        force_reassembly=True,
    )
    second = run_citation_assembly_governance_dry_run(db_session, dry_run=True)
    assert second.requests_processed == 1
    assert second.results_created == 2
    assert second.requests_replayed == 1

    replay_results = (
        db_session.execute(
            select(CitationAssemblyGovernanceResult).where(
                CitationAssemblyGovernanceResult.citation_assembly_governance_request_id
                == replay.id
            )
        )
        .scalars()
        .all()
    )
    assert len(replay_results) == 2
    assert replay_results[-1].citation_status == DRY_RUN_TERMINAL_STATUS


def test_rejected_and_duplicate_rejected_requests_skipped(db_session):
    source_doc = seed_source_document(db_session)
    version_a, sv_a = _seed_legal_object_version_for_doc(
        db_session, source_doc=source_doc, checksum_suffix="a"
    )
    version_b, sv_b = _seed_legal_object_version_for_doc(
        db_session, source_doc=source_doc, checksum_suffix="b"
    )

    rejected = create_citation_assembly_request(
        db_session,
        legal_object_id=version_a.legal_object_id,
        legal_object_version_id=version_a.legal_object_version_id,
        source_version_id=sv_a.id,
        requested_by_actor_type="worker",
        citation_reason="rejected path",
    )
    persist_citation_assembly_result(
        db_session,
        citation_assembly_governance_request_id=rejected.id,
        citation_status="rejected",
        error_category="invalid_request",
        error_message="manual rejection",
    )

    duplicate = create_citation_assembly_request(
        db_session,
        legal_object_id=version_b.legal_object_id,
        legal_object_version_id=version_b.legal_object_version_id,
        source_version_id=sv_b.id,
        requested_by_actor_type="admin",
        citation_reason="duplicate path",
    )
    persist_citation_assembly_result(
        db_session,
        citation_assembly_governance_request_id=duplicate.id,
        citation_status="duplicate_rejected",
        error_category="duplicate_citation",
        error_message="duplicate citation",
    )

    summary = run_citation_assembly_governance_dry_run(db_session, dry_run=True)
    assert summary.requests_seen == 2
    assert summary.requests_processed == 0
    assert summary.requests_skipped == 2
    assert summary.results_created == 0


def test_provider_failure_records_failed_result(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="provider failure path",
    )

    worker = CitationAssemblyGovernanceWorker(
        provider=FailingCitationAssemblyGovernanceProvider(),
        mode="dry_run",
    )
    summary = worker.run(db_session)

    assert summary.requests_processed == 1
    assert summary.failures == 1
    assert summary.results_created == 2

    latest = (
        db_session.execute(
            select(CitationAssemblyGovernanceResult).order_by(
                CitationAssemblyGovernanceResult.created_at.desc()
            )
        )
        .scalars()
        .first()
    )
    assert latest is not None
    assert latest.citation_status == "failed"
    assert latest.error_category == "citation_pipeline_unavailable"
    assert latest.citation_id is None


def test_summary_counts_with_multiple_eligible_requests(db_session):
    source_doc = seed_source_document(db_session)
    for idx in range(3):
        version, sv = _seed_legal_object_version_for_doc(
            db_session, source_doc=source_doc, checksum_suffix=str(idx)
        )
        create_citation_assembly_request(
            db_session,
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=sv.id,
            requested_by_actor_type="worker",
            citation_reason=f"multi-request-{idx}",
        )

    summary = run_citation_assembly_governance_dry_run(db_session, dry_run=True)
    assert summary.requests_seen == 3
    assert summary.requests_processed == 3
    assert summary.requests_skipped == 0
    assert summary.results_created == 6
    assert summary.failures == 0


def test_no_side_effects_beyond_governance_results(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    legal_before = db_session.query(LegalObject).count()
    version_before = db_session.query(LegalObjectVersion).count()

    create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="no side effects",
    )
    _ = run_citation_assembly_governance_dry_run(db_session, dry_run=True)

    assert db_session.query(LegalObject).count() == legal_before
    assert db_session.query(LegalObjectVersion).count() == version_before


def test_dry_run_does_not_use_assembled_status(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="status discipline",
    )
    _ = run_citation_assembly_governance_dry_run(db_session, dry_run=True)

    assembled_rows = (
        db_session.execute(
            select(CitationAssemblyGovernanceResult).where(
                CitationAssemblyGovernanceResult.citation_status == "assembled"
            )
        )
        .scalars()
        .all()
    )
    assert assembled_rows == []


def test_no_citation_assembler_or_retrieval_imports():
    from pathlib import Path

    worker_dir = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "workers"
        / "citation_assembly_governance"
    )
    forbidden_prefixes = (
        "from app.services.citation.",
        "import app.services.citation.",
        "from app.services.retrieval",
        "import app.services.retrieval",
    )
    forbidden_libs = ("openai", "anthropic", "transformers")
    for path in worker_dir.glob("*.py"):
        for line in path.read_text().splitlines():
            stripped = line.strip().lower()
            if not stripped.startswith(("import ", "from ")):
                continue
            for prefix in forbidden_prefixes:
                assert not stripped.startswith(prefix.lower()), (
                    f"{prefix} import forbidden in {path.name}: {line}"
                )
            for lib in forbidden_libs:
                assert f"import {lib}" not in stripped
                assert f"from {lib}" not in stripped
