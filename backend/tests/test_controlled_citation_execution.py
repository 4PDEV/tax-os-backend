"""TASK-006AD controlled citation execution tests."""

from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.models.citation import Citation
from app.models.citation_assembly_governance_result import CitationAssemblyGovernanceResult
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.models.source_version import SourceVersion
from app.services.citation.hash import compute_citation_hash as assembler_compute_hash
from app.services.citation_assembly_governance import create_citation_assembly_request
from app.services.citation_execution import (
    compute_citation_hash,
    create_citation,
    execute_controlled_citation,
    find_existing_citation,
    get_citation_by_hash,
    render_citation,
)
from app.workers.citation_assembly_governance import (
    CONTROLLED_TERMINAL_STATUS,
    DRY_RUN_TERMINAL_STATUS,
    run_citation_assembly_governance_dry_run,
    run_controlled_citation_execution,
)
from tests.test_citation_worker_skeleton import _seed_legal_object_version

pytestmark = pytest.mark.integration


def _create_governance_request(db_session, version, extracted, *, reason: str, force_reassembly=False):
    return create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason=reason,
        force_reassembly=force_reassembly,
    )


def test_citation_hash_deterministic():
    source_version_id = uuid4()
    legal_object_version_id = uuid4()
    first = compute_citation_hash(
        source_version_id=source_version_id,
        legal_object_id="lo_test",
        legal_object_version_id=legal_object_version_id,
        location_reference="Section 15",
    )
    second = compute_citation_hash(
        source_version_id=source_version_id,
        legal_object_id="lo_test",
        legal_object_version_id=legal_object_version_id,
        location_reference="Section 15",
    )
    assert first == second
    assert len(first) == 64


def test_citation_hash_ignores_rendered_text(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    legal_object = db_session.get(LegalObject, version.legal_object_id)
    rendered = render_citation(
        db_session,
        legal_object=legal_object,
        legal_object_version_id=version.legal_object_version_id,
    )
    hash_from_provenance = compute_citation_hash(
        source_version_id=rendered.source_version_id,
        legal_object_id=rendered.legal_object_id,
        legal_object_version_id=rendered.legal_object_version_id,
        location_reference=rendered.location_reference,
    )
    assert hash_from_provenance == rendered.citation_hash
    assert hash_from_provenance == assembler_compute_hash(
        source_version_id=rendered.source_version_id,
        legal_object_id=rendered.legal_object_id,
        legal_object_version_id=rendered.legal_object_version_id,
        location_reference=rendered.location_reference,
    )


def test_duplicate_execution_returns_existing_citation(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    legal_object = db_session.get(LegalObject, version.legal_object_id)
    rendered = render_citation(
        db_session,
        legal_object=legal_object,
        legal_object_version_id=version.legal_object_version_id,
    )

    first, created_first = create_citation(
        db_session,
        citation_id=rendered.citation_id,
        citation_hash=rendered.citation_hash,
        legal_object_id=rendered.legal_object_id,
        legal_object_version_id=rendered.legal_object_version_id,
        source_version_id=rendered.source_version_id,
        location_reference=rendered.location_reference,
        rendered_citation_text=rendered.citation_text,
        assembled_at=rendered.assembled_at,
    )
    second, created_second = create_citation(
        db_session,
        citation_id=rendered.citation_id,
        citation_hash=rendered.citation_hash,
        legal_object_id=rendered.legal_object_id,
        legal_object_version_id=rendered.legal_object_version_id,
        source_version_id=rendered.source_version_id,
        location_reference=rendered.location_reference,
        rendered_citation_text="Different formatting.\nStill not identity.",
        assembled_at=rendered.assembled_at,
    )

    assert created_first is True
    assert created_second is False
    assert first.id == second.id
    assert db_session.query(Citation).count() == 1


def test_unique_citation_hash_enforced(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    legal_object = db_session.get(LegalObject, version.legal_object_id)
    rendered = render_citation(
        db_session,
        legal_object=legal_object,
        legal_object_version_id=version.legal_object_version_id,
    )
    create_citation(
        db_session,
        citation_id=rendered.citation_id,
        citation_hash=rendered.citation_hash,
        legal_object_id=rendered.legal_object_id,
        legal_object_version_id=rendered.legal_object_version_id,
        source_version_id=rendered.source_version_id,
        location_reference=rendered.location_reference,
        rendered_citation_text=rendered.citation_text,
        assembled_at=rendered.assembled_at,
    )

    duplicate = Citation(
        citation_id="cit_duplicate_hash_collision",
        citation_hash=rendered.citation_hash,
        legal_object_id=rendered.legal_object_id,
        legal_object_version_id=rendered.legal_object_version_id,
        source_version_id=rendered.source_version_id,
        location_reference=rendered.location_reference,
        rendered_citation_text="collision attempt",
        assembled_at=rendered.assembled_at,
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_force_reassembly_does_not_create_new_hash(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    request = _create_governance_request(db_session, version, extracted, reason="initial")
    run_controlled_citation_execution(db_session, controlled_execution=True)
    first_citation = db_session.query(Citation).one()

    replay = _create_governance_request(
        db_session,
        version,
        extracted,
        reason="force replay",
        force_reassembly=True,
    )
    run_controlled_citation_execution(db_session, controlled_execution=True)

    assert db_session.query(Citation).count() == 1
    second_citation = db_session.query(Citation).one()
    assert second_citation.citation_hash == first_citation.citation_hash
    assert second_citation.citation_id == first_citation.citation_id

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
    assert any(row.citation_status == CONTROLLED_TERMINAL_STATUS for row in replay_results)


def test_governance_result_stores_citation_id_only(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    request = _create_governance_request(db_session, version, extracted, reason="governance boundary")
    run_controlled_citation_execution(db_session, controlled_execution=True)

    citation = db_session.query(Citation).one()
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
    assembled = [row for row in results if row.citation_status == CONTROLLED_TERMINAL_STATUS]
    assert len(assembled) == 1
    assert assembled[0].citation_id == citation.citation_id
    assert assembled[0].assembled_at is not None

    result_columns = {column.name for column in CitationAssemblyGovernanceResult.__table__.columns}
    assert "citation_hash" not in result_columns
    assert "rendered_citation_text" not in result_columns


def test_temporal_compliance_no_source_version_fallback(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    source_version = db_session.get(SourceVersion, extracted.source_version_id)
    source_version.effective_from = date(2020, 1, 1)
    source_version.effective_to = date(2020, 12, 31)
    source_version.version_label = ""
    db_session.flush()

    lo_version = db_session.get(LegalObjectVersion, version.legal_object_version_id)
    assert lo_version.effective_from is None
    assert lo_version.effective_to is None

    request = _create_governance_request(db_session, version, extracted, reason="temporal")
    run_controlled_citation_execution(db_session, controlled_execution=True)

    citation = db_session.query(Citation).one()
    assert "Version effective 1 January 2020." not in citation.rendered_citation_text
    assert "Source version metadata: effective from 1 January 2020." in citation.rendered_citation_text


def test_dry_run_unchanged(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    _create_governance_request(db_session, version, extracted, reason="dry-run unchanged")
    summary = run_citation_assembly_governance_dry_run(db_session, dry_run=True)

    assert summary.requests_processed == 1
    assert db_session.query(Citation).count() == 0
    assembled = (
        db_session.execute(
            select(CitationAssemblyGovernanceResult).where(
                CitationAssemblyGovernanceResult.citation_status == "assembled"
            )
        )
        .scalars()
        .all()
    )
    assert assembled == []
    skipped = (
        db_session.execute(
            select(CitationAssemblyGovernanceResult).where(
                CitationAssemblyGovernanceResult.citation_status == DRY_RUN_TERMINAL_STATUS
            )
        )
        .scalars()
        .all()
    )
    assert len(skipped) == 1
    assert skipped[0].citation_id is None


def test_assembled_only_in_controlled_mode(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    _create_governance_request(db_session, version, extracted, reason="controlled assembled")
    run_controlled_citation_execution(db_session, controlled_execution=True)

    assembled = (
        db_session.execute(
            select(CitationAssemblyGovernanceResult).where(
                CitationAssemblyGovernanceResult.citation_status == CONTROLLED_TERMINAL_STATUS
            )
        )
        .scalars()
        .all()
    )
    assert len(assembled) == 1
    assert assembled[0].citation_id is not None


def test_controlled_execution_lineage_preserved(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    request = _create_governance_request(db_session, version, extracted, reason="lineage")
    run_controlled_citation_execution(db_session, controlled_execution=True)

    citation = db_session.query(Citation).one()
    assert citation.legal_object_id == version.legal_object_id
    assert citation.legal_object_version_id == version.legal_object_version_id
    assert citation.source_version_id == extracted.source_version_id
    assert citation.location_reference
    assert get_citation_by_hash(db_session, citation_hash=citation.citation_hash) is not None
    assert find_existing_citation(db_session, citation_hash=citation.citation_hash) is not None


def test_controlled_runner_requires_flag():
    from app.workers.citation_assembly_governance.worker import CitationAssemblyGovernanceWorkerError

    with pytest.raises(CitationAssemblyGovernanceWorkerError):
        run_controlled_citation_execution(None, controlled_execution=False)  # type: ignore[arg-type]


def test_no_retrieval_or_answer_imports_in_controlled_path():
    worker_dir = (
        Path(__file__).resolve().parents[1] / "app" / "workers" / "citation_assembly_governance"
    )
    service_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "citation_execution"
    forbidden = (
        "app.services.retrieval",
        "app.services.answer",
        "openai",
        "anthropic",
    )
    for directory in (worker_dir, service_dir):
        for path in directory.glob("*.py"):
            text = path.read_text().lower()
            for token in forbidden:
                assert token not in text, f"{token} forbidden in {path.name}"


def test_citations_table_exists_at_head(engine):
    tables = set(inspect(engine).get_table_names())
    assert "citations" in tables
    indexes = {idx["name"] for idx in inspect(engine).get_indexes("citations")}
    assert "uq_citations_citation_hash" in indexes or any(
        "citation_hash" in idx.get("column_names", []) and idx.get("unique")
        for idx in inspect(engine).get_indexes("citations")
    )


def test_execute_controlled_citation_direct(db_session):
    version, extracted = _seed_legal_object_version(db_session)
    request = _create_governance_request(db_session, version, extracted, reason="direct execution")
    lo_version = db_session.get(LegalObjectVersion, version.legal_object_version_id)
    outcome = execute_controlled_citation(
        db_session,
        request=request,
        legal_object_version=lo_version,
    )
    assert outcome.citation.citation_id.startswith("cit_")
    assert outcome.created is True
