import inspect
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.retrieval_evidence_reference import RetrievalEvidenceReference
from app.models.retrieval_result import RetrievalResult
from app.services.retrieval_persistence import (
    create_retrieval_request,
    create_retrieval_result,
)
from app.workers.retrieval_runtime import (
    DRY_RUN_TERMINAL_STATUS,
    RetrievalRuntimeProviderResult,
    RetrievalRuntimeWorker,
    RetrievalRuntimeWorkerError,
    run_retrieval_runtime_dry_run,
)
from app.workers.retrieval_runtime.dry_run_provider import RetrievalRuntimeProvider

pytestmark = pytest.mark.integration


def _default_scope(**kwargs):
    base = {
        "legal_object_id": None,
        "legal_object_type": None,
        "object_identifier": None,
        "source_document_id": None,
        "source_version_id": None,
    }
    base.update(kwargs)
    return base


def _create_request(db_session, *, scope=None, force_replay=False, replay_nonce=None, **kwargs):
    defaults = {
        "retrieval_mode": "LATEST_VERSION",
        "jurisdiction_code": "RW",
        "scope_envelope": scope or _default_scope(),
        "include_canonical_text": False,
        "include_rendered_citation_text": False,
        "requested_by_actor_type": "worker",
        "force_replay": force_replay,
        "replay_nonce": replay_nonce,
    }
    defaults.update(kwargs)
    return create_retrieval_request(db_session, **defaults)


class FailingRetrievalRuntimeProvider(RetrievalRuntimeProvider):
    def run_retrieval(self, db, request):
        _ = db, request
        return RetrievalRuntimeProviderResult(
            success=False,
            error_category="retrieval_pipeline_unavailable",
            error_message="synthetic provider failure",
        )


def test_invalid_execution_mode_rejected():
    with pytest.raises(RetrievalRuntimeWorkerError):
        RetrievalRuntimeWorker(
            provider=FailingRetrievalRuntimeProvider(),
            mode="controlled_execution",
        )


def test_non_dry_run_runner_rejected():
    with pytest.raises(RetrievalRuntimeWorkerError):
        run_retrieval_runtime_dry_run(None, dry_run=False)  # type: ignore[arg-type]


def test_dry_run_worker_processes_eligible_request(db_session):
    request = _create_request(db_session)
    summary = run_retrieval_runtime_dry_run(db_session, dry_run=True)

    assert summary.requests_seen == 1
    assert summary.requests_processed == 1
    assert summary.requests_skipped == 0
    assert summary.results_created == 2
    assert summary.failures == 0

    latest = (
        db_session.execute(
            select(RetrievalResult)
            .where(RetrievalResult.retrieval_request_id == request.id)
            .order_by(RetrievalResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest is not None
    assert latest.retrieval_status == DRY_RUN_TERMINAL_STATUS
    assert latest.result_count == 0


def test_accepted_to_skipped_lifecycle(db_session):
    request = _create_request(db_session)
    _ = run_retrieval_runtime_dry_run(db_session, dry_run=True)

    results = (
        db_session.execute(
            select(RetrievalResult)
            .where(RetrievalResult.retrieval_request_id == request.id)
            .order_by(RetrievalResult.created_at.asc())
        )
        .scalars()
        .all()
    )
    assert [row.retrieval_status for row in results] == ["accepted", "skipped"]


def test_terminal_request_not_reprocessed(db_session):
    request = _create_request(db_session)
    first = run_retrieval_runtime_dry_run(db_session, dry_run=True)
    assert first.requests_processed == 1

    second = run_retrieval_runtime_dry_run(db_session, dry_run=True)
    assert second.requests_seen == 1
    assert second.requests_processed == 0
    assert second.requests_skipped == 1
    assert second.results_created == 0

    results = (
        db_session.execute(
            select(RetrievalResult).where(RetrievalResult.retrieval_request_id == request.id)
        )
        .scalars()
        .all()
    )
    assert len(results) == 2


def test_force_replay_allows_replay(db_session):
    scope = _default_scope()
    _create_request(db_session, scope=scope, force_replay=False)
    _ = run_retrieval_runtime_dry_run(db_session, dry_run=True)

    replay = _create_request(
        db_session,
        scope=scope,
        force_replay=True,
        replay_nonce="replay-1",
    )
    second = run_retrieval_runtime_dry_run(db_session, dry_run=True)
    assert second.requests_processed == 1
    assert second.results_created == 2
    assert second.requests_replayed == 1

    replay_results = (
        db_session.execute(
            select(RetrievalResult).where(RetrievalResult.retrieval_request_id == replay.id)
        )
        .scalars()
        .all()
    )
    assert len(replay_results) == 2
    assert replay_results[-1].retrieval_status == DRY_RUN_TERMINAL_STATUS


def test_duplicate_rejected_terminal_skipped(db_session):
    request = _create_request(db_session)
    create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="duplicate_rejected",
        error_category="duplicate_retrieval",
        error_message="duplicate",
    )

    summary = run_retrieval_runtime_dry_run(db_session, dry_run=True)
    assert summary.requests_seen == 1
    assert summary.requests_processed == 0
    assert summary.requests_skipped == 1
    assert summary.results_created == 0


def test_provider_failure_records_failed_result(db_session):
    _create_request(db_session)
    worker = RetrievalRuntimeWorker(
        provider=FailingRetrievalRuntimeProvider(),
        mode="dry_run",
    )
    summary = worker.run(db_session)

    assert summary.requests_processed == 1
    assert summary.failures == 1
    assert summary.results_created == 2

    latest = (
        db_session.execute(
            select(RetrievalResult).order_by(RetrievalResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest is not None
    assert latest.retrieval_status == "failed"
    assert latest.error_category == "retrieval_pipeline_unavailable"


def test_dry_run_does_not_use_completed_status(db_session):
    _create_request(db_session)
    _ = run_retrieval_runtime_dry_run(db_session, dry_run=True)

    completed_rows = (
        db_session.execute(
            select(RetrievalResult).where(RetrievalResult.retrieval_status == "completed")
        )
        .scalars()
        .all()
    )
    assert completed_rows == []


def test_no_evidence_references_created(db_session):
    _create_request(db_session)
    _ = run_retrieval_runtime_dry_run(db_session, dry_run=True)
    assert db_session.query(RetrievalEvidenceReference).count() == 0


def test_append_only_result_history(db_session):
    request = _create_request(db_session)
    _ = run_retrieval_runtime_dry_run(db_session, dry_run=True)
    _ = run_retrieval_runtime_dry_run(db_session, dry_run=True)

    results = (
        db_session.execute(
            select(RetrievalResult).where(RetrievalResult.retrieval_request_id == request.id)
        )
        .scalars()
        .all()
    )
    assert len(results) == 2


def test_summary_counts_with_multiple_eligible_requests(db_session):
    for idx in range(3):
        _create_request(
            db_session,
            scope=_default_scope(object_identifier=f"obj-{idx}"),
        )

    summary = run_retrieval_runtime_dry_run(db_session, dry_run=True)
    assert summary.requests_seen == 3
    assert summary.requests_processed == 3
    assert summary.requests_skipped == 0
    assert summary.results_created == 6
    assert summary.failures == 0


def test_no_retrieval_execution_imports():
    worker_dir = Path(__file__).resolve().parents[1] / "app" / "workers" / "retrieval_runtime"
    forbidden_prefixes = (
        "from app.services.retrieval.",
        "import app.services.retrieval.",
        "from app.services.citation.",
        "import app.services.citation.",
        "from app.services.answer",
        "import app.services.answer",
        "from app.services.ranking",
        "import app.services.ranking",
    )
    forbidden_tokens = (
        "citationassembler",
        "openai",
        "anthropic",
        "transformers",
        "pgvector",
        "semantic",
        "llm",
    )
    for path in worker_dir.glob("*.py"):
        source = path.read_text().lower()
        for line in source.splitlines():
            stripped = line.strip()
            if not stripped.startswith(("import ", "from ")):
                continue
            for prefix in forbidden_prefixes:
                assert not stripped.startswith(prefix), (
                    f"{prefix} import forbidden in {path.name}: {line}"
                )
        for token in forbidden_tokens:
            assert token not in source, f"{token} must not appear in {path.name}"


def test_worker_does_not_import_legal_object_version_selection():
    from app.workers import retrieval_runtime

    worker_source = inspect.getsource(retrieval_runtime.worker)
    forbidden = (
        "LegalObjectVersion",
        "LegalObject",
        "Citation",
        "create_evidence_reference",
        "list_evidence_references",
    )
    for token in forbidden:
        assert token not in worker_source


def test_persistence_module_not_used_for_evidence_in_worker():
    from app.workers.retrieval_runtime import worker as worker_module

    source = inspect.getsource(worker_module)
    assert "create_evidence_reference" not in source
    assert "list_evidence_references" not in source
