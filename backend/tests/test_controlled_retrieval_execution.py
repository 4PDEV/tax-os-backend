"""TASK-007E controlled retrieval execution tests."""

import inspect
import uuid
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.citation import Citation
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.models.retrieval_evidence_reference import RetrievalEvidenceReference
from app.models.retrieval_result import RetrievalResult
from app.models.source_version import SourceVersion
from app.services.citation_execution import create_citation, render_citation
from app.services.retrieval_execution.ordering import sort_evidence_candidates
from app.services.retrieval_execution.models import EvidenceCandidate
from app.services.retrieval_persistence import create_retrieval_request, list_evidence_references
from app.workers.retrieval_runtime import (
    CONTROLLED_TERMINAL_STATUS,
    DRY_RUN_TERMINAL_STATUS,
    RetrievalRuntimeWorker,
    RetrievalRuntimeWorkerError,
    run_controlled_retrieval_execution,
    run_retrieval_runtime_dry_run,
)
from app.workers.retrieval_runtime.controlled_provider import ControlledRetrievalRuntimeProvider
from app.workers.retrieval_runtime.dry_run_provider import RetrievalRuntimeProvider
from app.workers.retrieval_runtime.result import RetrievalRuntimeProviderResult
from tests.test_citation_worker_skeleton import _seed_legal_object_version
from tests.test_retrieval_persistence import _create_request, _default_scope, _seed_citation

pytestmark = pytest.mark.integration


def _set_version_effective(version, *, effective_from=None, effective_to=None):
    version.effective_from = effective_from
    version.effective_to = effective_to


def _add_version_for_object(db_session, base_version, *, effective_from, effective_to, suffix: str):
    new_id = uuid.uuid4()
    new_version = LegalObjectVersion(
        legal_object_version_id=new_id,
        legal_object_id=base_version.legal_object_id,
        source_version_id=base_version.source_version_id,
        parent_legal_object_id=base_version.parent_legal_object_id,
        structural_unit_id=f"{base_version.structural_unit_id}-{suffix}",
        object_label=f"{base_version.object_label}-{suffix}",
        object_title=base_version.object_title,
        start_offset=base_version.start_offset,
        end_offset=base_version.end_offset,
        raw_text=f"{base_version.raw_text}-{suffix}",
        text_hash=f"{suffix}" * 64,
        effective_from=effective_from,
        effective_to=effective_to,
        version_status=base_version.version_status,
        extraction_status=base_version.extraction_status,
    )
    db_session.add(new_version)
    db_session.flush()
    return new_version


def test_controlled_runner_requires_flag():
    with pytest.raises(RetrievalRuntimeWorkerError):
        run_controlled_retrieval_execution(None, controlled_execution=False)  # type: ignore[arg-type]


def test_as_of_date_selects_by_legal_object_dates_only(db_session):
    version, _ = _seed_legal_object_version(db_session)
    _set_version_effective(version, effective_from=date(2024, 1, 1), effective_to=date(2024, 12, 31))

    source_version = db_session.get(SourceVersion, version.source_version_id)
    source_version.effective_from = date(1900, 1, 1)
    source_version.effective_to = date(1900, 12, 31)
    db_session.flush()

    scope = _default_scope(legal_object_id=version.legal_object_id)
    _create_request(
        db_session,
        scope=scope,
        retrieval_mode="AS_OF_DATE",
        as_of_date=date(2024, 6, 1),
    )
    run_controlled_retrieval_execution(db_session, controlled_execution=True)

    refs = db_session.query(RetrievalEvidenceReference).all()
    assert len(refs) == 1
    assert refs[0].legal_object_version_id == version.legal_object_version_id


def test_as_of_date_returns_all_overlapping_matches(db_session):
    version, _ = _seed_legal_object_version(db_session)
    _set_version_effective(version, effective_from=date(2024, 1, 1), effective_to=date(2024, 6, 30))
    second = _add_version_for_object(
        db_session,
        version,
        effective_from=date(2024, 3, 1),
        effective_to=date(2024, 12, 31),
        suffix="b",
    )

    scope = _default_scope(legal_object_id=version.legal_object_id)
    _create_request(
        db_session,
        scope=scope,
        retrieval_mode="AS_OF_DATE",
        as_of_date=date(2024, 4, 1),
    )
    run_controlled_retrieval_execution(db_session, controlled_execution=True)

    refs = db_session.query(RetrievalEvidenceReference).order_by(
        RetrievalEvidenceReference.deterministic_order_index
    ).all()
    assert len(refs) == 2
    version_ids = {ref.legal_object_version_id for ref in refs}
    assert version.legal_object_version_id in version_ids
    assert second.legal_object_version_id in version_ids
    assert refs[0].deterministic_order_index == 1
    assert refs[1].deterministic_order_index == 2


def test_as_of_date_no_match_completed_zero(db_session):
    version, _ = _seed_legal_object_version(db_session)
    _set_version_effective(version, effective_from=date(2020, 1, 1), effective_to=date(2020, 12, 31))

    scope = _default_scope(legal_object_id=version.legal_object_id)
    request = _create_request(
        db_session,
        scope=scope,
        retrieval_mode="AS_OF_DATE",
        as_of_date=date(2025, 1, 1),
    )
    run_controlled_retrieval_execution(db_session, controlled_execution=True)

    latest = (
        db_session.execute(
            select(RetrievalResult)
            .where(RetrievalResult.retrieval_request_id == request.id)
            .order_by(RetrievalResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest.retrieval_status == CONTROLLED_TERMINAL_STATUS
    assert latest.result_count == 0
    assert latest.error_category is None
    assert db_session.query(RetrievalEvidenceReference).count() == 0


def test_exact_version_returns_pinned_version(db_session):
    version, _ = _seed_legal_object_version(db_session)
    scope = _default_scope(legal_object_id=version.legal_object_id)
    request = _create_request(
        db_session,
        scope=scope,
        retrieval_mode="EXACT_VERSION",
        legal_object_version_id=version.legal_object_version_id,
    )
    run_controlled_retrieval_execution(db_session, controlled_execution=True)

    refs = db_session.query(RetrievalEvidenceReference).all()
    assert len(refs) == 1
    assert refs[0].legal_object_version_id == version.legal_object_version_id

    latest = (
        db_session.execute(
            select(RetrievalResult)
            .where(RetrievalResult.retrieval_request_id == request.id)
            .order_by(RetrievalResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest.result_count == 1


def test_exact_version_no_match_no_latest_fallback(db_session):
    version, _ = _seed_legal_object_version(db_session)
    legal_object = db_session.get(LegalObject, version.legal_object_id)
    legal_object.current_version_id = version.legal_object_version_id
    db_session.flush()

    scope = _default_scope(legal_object_id="non_matching_object_id")
    request = _create_request(
        db_session,
        scope=scope,
        retrieval_mode="EXACT_VERSION",
        legal_object_version_id=version.legal_object_version_id,
    )
    run_controlled_retrieval_execution(db_session, controlled_execution=True)

    latest = (
        db_session.execute(
            select(RetrievalResult)
            .where(RetrievalResult.retrieval_request_id == request.id)
            .order_by(RetrievalResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest.retrieval_status == CONTROLLED_TERMINAL_STATUS
    assert latest.result_count == 0
    assert db_session.query(RetrievalEvidenceReference).count() == 0


def test_latest_version_explicit_only(db_session):
    version, _ = _seed_legal_object_version(db_session)
    legal_object = db_session.get(LegalObject, version.legal_object_id)
    legal_object.current_version_id = version.legal_object_version_id
    db_session.flush()

    scope = _default_scope(legal_object_id=version.legal_object_id)
    _create_request(db_session, scope=scope, retrieval_mode="LATEST_VERSION")
    run_controlled_retrieval_execution(db_session, controlled_execution=True)

    refs = db_session.query(RetrievalEvidenceReference).all()
    assert len(refs) == 1
    assert refs[0].legal_object_version_id == version.legal_object_version_id


def test_citation_attached_when_present(db_session):
    version, _, citation = _seed_citation(db_session)
    legal_object = db_session.get(LegalObject, version.legal_object_id)
    legal_object.current_version_id = version.legal_object_version_id
    db_session.flush()

    scope = _default_scope(legal_object_id=version.legal_object_id)
    _create_request(db_session, scope=scope, retrieval_mode="LATEST_VERSION")
    run_controlled_retrieval_execution(db_session, controlled_execution=True)

    ref = db_session.query(RetrievalEvidenceReference).one()
    assert ref.citation_id == citation.citation_id
    assert ref.citation_hash == citation.citation_hash


def test_citation_less_evidence_valid(db_session):
    version, _ = _seed_legal_object_version(db_session)
    legal_object = db_session.get(LegalObject, version.legal_object_id)
    legal_object.current_version_id = version.legal_object_version_id
    db_session.flush()

    assert db_session.query(Citation).count() == 0
    scope = _default_scope(legal_object_id=version.legal_object_id)
    _create_request(db_session, scope=scope, retrieval_mode="LATEST_VERSION")
    run_controlled_retrieval_execution(db_session, controlled_execution=True)

    ref = db_session.query(RetrievalEvidenceReference).one()
    assert ref.citation_id is None
    assert ref.citation_hash is None


def test_no_citation_creation_during_retrieval(db_session):
    version, _ = _seed_legal_object_version(db_session)
    legal_object = db_session.get(LegalObject, version.legal_object_id)
    legal_object.current_version_id = version.legal_object_version_id
    db_session.flush()

    scope = _default_scope(legal_object_id=version.legal_object_id)
    _create_request(db_session, scope=scope, retrieval_mode="LATEST_VERSION")
    run_controlled_retrieval_execution(db_session, controlled_execution=True)
    assert db_session.query(Citation).count() == 0


def test_deterministic_ordering_stable():
    first = EvidenceCandidate(
        legal_object_id="lo_b",
        legal_object_version_id=uuid.uuid4(),
        source_version_id=uuid.uuid4(),
        source_document_id=uuid.uuid4(),
        effective_from=date(2024, 2, 1),
        object_identifier="u1:l1",
        object_type="article",
        object_label="l1",
        citation_hash="bbb",
    )
    second = EvidenceCandidate(
        legal_object_id="lo_a",
        legal_object_version_id=uuid.uuid4(),
        source_version_id=uuid.uuid4(),
        source_document_id=uuid.uuid4(),
        effective_from=date(2024, 1, 1),
        object_identifier="u2:l2",
        object_type="article",
        object_label="l2",
        citation_hash="aaa",
    )
    ordered = sort_evidence_candidates([first, second])
    assert ordered[0].legal_object_id == "lo_a"
    assert ordered[1].legal_object_id == "lo_b"


def test_accepted_to_completed_lifecycle(db_session):
    version, _ = _seed_legal_object_version(db_session)
    legal_object = db_session.get(LegalObject, version.legal_object_id)
    legal_object.current_version_id = version.legal_object_version_id
    db_session.flush()

    scope = _default_scope(legal_object_id=version.legal_object_id)
    request = _create_request(db_session, scope=scope, retrieval_mode="LATEST_VERSION")
    run_controlled_retrieval_execution(db_session, controlled_execution=True)

    results = (
        db_session.execute(
            select(RetrievalResult)
            .where(RetrievalResult.retrieval_request_id == request.id)
            .order_by(RetrievalResult.created_at.asc())
        )
        .scalars()
        .all()
    )
    assert [row.retrieval_status for row in results] == ["accepted", "completed"]


def test_result_count_equals_evidence_count(db_session):
    version, _ = _seed_legal_object_version(db_session)
    _set_version_effective(version, effective_from=date(2024, 1, 1), effective_to=None)
    _add_version_for_object(
        db_session,
        version,
        effective_from=date(2024, 1, 1),
        effective_to=None,
        suffix="x",
    )

    scope = _default_scope(legal_object_id=version.legal_object_id)
    request = _create_request(
        db_session,
        scope=scope,
        retrieval_mode="AS_OF_DATE",
        as_of_date=date(2024, 6, 1),
    )
    run_controlled_retrieval_execution(db_session, controlled_execution=True)

    latest = (
        db_session.execute(
            select(RetrievalResult)
            .where(RetrievalResult.retrieval_request_id == request.id)
            .order_by(RetrievalResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    refs = db_session.query(RetrievalEvidenceReference).count()
    assert latest.result_count == refs


def test_force_replay_creates_new_lifecycle(db_session):
    scope = _default_scope()
    version, _ = _seed_legal_object_version(db_session)
    legal_object = db_session.get(LegalObject, version.legal_object_id)
    legal_object.current_version_id = version.legal_object_version_id
    db_session.flush()

    scoped = _default_scope(legal_object_id=version.legal_object_id)
    _create_request(db_session, scope=scoped, retrieval_mode="LATEST_VERSION")
    run_controlled_retrieval_execution(db_session, controlled_execution=True)

    replay = _create_request(
        db_session,
        scope=scoped,
        retrieval_mode="LATEST_VERSION",
        force_replay=True,
        replay_nonce="replay-controlled",
    )
    second = run_controlled_retrieval_execution(db_session, controlled_execution=True)
    assert second.requests_processed == 1
    assert second.results_created == 2

    replay_results = (
        db_session.execute(
            select(RetrievalResult).where(RetrievalResult.retrieval_request_id == replay.id)
        )
        .scalars()
        .all()
    )
    assert len(replay_results) == 2


def test_dry_run_worker_unchanged(db_session):
    version, _ = _seed_legal_object_version(db_session)
    scope = _default_scope(legal_object_id=version.legal_object_id)
    _create_request(db_session, scope=scope, retrieval_mode="LATEST_VERSION")
    summary = run_retrieval_runtime_dry_run(db_session, dry_run=True)

    assert summary.requests_processed == 1
    assert db_session.query(RetrievalEvidenceReference).count() == 0
    skipped = (
        db_session.execute(
            select(RetrievalResult).where(RetrievalResult.retrieval_status == DRY_RUN_TERMINAL_STATUS)
        )
        .scalars()
        .all()
    )
    assert len(skipped) == 1
    completed = (
        db_session.execute(
            select(RetrievalResult).where(RetrievalResult.retrieval_status == CONTROLLED_TERMINAL_STATUS)
        )
        .scalars()
        .all()
    )
    assert completed == []


def test_as_of_date_missing_fails(db_session):
    scope = _default_scope()
    _create_request(db_session, scope=scope, retrieval_mode="AS_OF_DATE", as_of_date=None)
    summary = run_controlled_retrieval_execution(db_session, controlled_execution=True)
    assert summary.failures == 1
    failed = (
        db_session.execute(
            select(RetrievalResult).where(RetrievalResult.retrieval_status == "failed")
        )
        .scalars()
        .first()
    )
    assert failed.error_category == "temporal_scope_missing"


def test_no_retrieval_or_answer_imports_in_controlled_path():
    worker_dir = Path(__file__).resolve().parents[1] / "app" / "workers" / "retrieval_runtime"
    service_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "retrieval_execution"
    forbidden_prefixes = (
        "from app.services.retrieval.",
        "import app.services.retrieval.",
        "from app.services.answer",
        "import app.services.answer",
        "from app.services.ranking",
        "import app.services.ranking",
        "from app.services.ai",
        "import app.services.ai",
        "from app.services.semantic",
        "import app.services.semantic",
        "from app.services.vector",
        "import app.services.vector",
        "from app.services.citation.assembler",
        "import app.services.citation.assembler",
    )
    for directory in (worker_dir, service_dir):
        for path in directory.glob("*.py"):
            for line in path.read_text().splitlines():
                stripped = line.strip().lower()
                if not stripped.startswith(("import ", "from ")):
                    continue
                for prefix in forbidden_prefixes:
                    assert not stripped.startswith(prefix), f"{prefix} forbidden in {path.name}: {line}"


def test_controlled_provider_does_not_import_citation_assembler():
    source = inspect.getsource(ControlledRetrievalRuntimeProvider)
    assert "CitationAssembler" not in source
    assert "citation_execution" not in source or "execute_controlled_citation" not in source
