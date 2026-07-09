"""TASK-010A response runtime tests."""

import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.models.retrieval_evidence_reference import RetrievalEvidenceReference
from app.services.response_runtime import (
    CURRENT_CONTRACT_VERSION,
    RESPONSE_STATUS_COMPLETED,
    RESPONSE_STATUS_FAILED,
    ResponseEvidenceEntry,
    ResponsePackage,
    ResponseRequest,
    ResponseRuntimeError,
    build_response,
)
from app.services.response_runtime.runtime import ResponseRuntime
from app.workers.answer_runtime import build_answer_worker_request, run_answer_worker

PROHIBITED_IMPORT_PREFIXES = (
    "from app.services.retrieval_execution",
    "import app.services.retrieval_execution",
    "from app.services.ranking_execution",
    "import app.services.ranking_execution",
    "from app.workers.ranking_runtime",
    "import app.workers.ranking_runtime",
    "from app.workers.answer_runtime",
    "import app.workers.answer_runtime",
    "from app.services.answer_assembly",
    "import app.services.answer_assembly",
    "from app.services.ai",
    "import app.services.ai",
    "from app.services.semantic",
    "import app.services.semantic",
    "from app.services.vector",
    "import app.services.vector",
    "from app.services.citation.assembler",
    "import app.services.citation.assembler",
    "from fastapi",
    "import fastapi",
    "APIRouter",
    "import celery",
    "from celery",
    "import redis",
    "from redis",
    "import rabbitmq",
    "from rabbitmq",
    "import kafka",
    "from kafka",
)

FORBIDDEN_RUNTIME_TOKENS = (
    "persist_answer_for_ranking_request",
    "run_answer_worker",
    "assemble_answer_package",
    "create_answer_request",
    "create_answer_result",
    "create_answer_evidence_entry",
    "create_answer_uncertainty_flag",
    "resolve_ranking_assembly_inputs",
    "execute_controlled_ranking",
)


def _complete_ranking(db_session, evidence_specs, **request_kwargs):
    from app.core.datetime_utils import utc_now
    from app.services.ranking_execution import execute_controlled_ranking
    from app.services.retrieval_persistence import create_evidence_reference, create_retrieval_result
    from tests.test_retrieval_persistence import _create_request, _seed_citation

    request = _create_request(db_session, **request_kwargs)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="completed",
        result_count=len(evidence_specs),
        completed_at=utc_now(),
    )
    for index, spec in enumerate(evidence_specs, start=1):
        version, extracted, citation = _seed_citation(db_session)
        if spec.get("effective_from") is not None:
            version.effective_from = spec["effective_from"]
        if spec.get("effective_to") is not None:
            version.effective_to = spec["effective_to"]
        db_session.flush()
        create_evidence_reference(
            db_session,
            retrieval_result_id=result.id,
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=extracted.source_version_id,
            citation_id=citation.citation_id,
            citation_hash=citation.citation_hash,
            source_document_id=spec.get("source_document_id"),
            object_identifier=spec.get("object_identifier", f"obj-{index}"),
            deterministic_order_index=index,
        )
    outcome = execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
    )
    assert outcome.ranking_status == "completed"
    return outcome.ranking_request_id


def test_response_request_and_package_dto_fields():
    request = ResponseRequest(
        answer_request_id=uuid.uuid4(),
        contract_version=CURRENT_CONTRACT_VERSION,
        include_rendered_citation_text=False,
    )
    package = ResponsePackage(
        contract_version=CURRENT_CONTRACT_VERSION,
        answer_request_id=request.answer_request_id,
        answer_result_id=uuid.uuid4(),
        rank_count=1,
        evidence_entries=[
            ResponseEvidenceEntry(
                presentation_order_index=1,
                retrieval_evidence_reference_id=uuid.uuid4(),
                ranked_evidence_reference_id=uuid.uuid4(),
                legal_object_id="lo-1",
                source_version_id=uuid.uuid4(),
                object_identifier="obj-1",
                location_reference=None,
                citation_reference=None,
            )
        ],
        uncertainty_flags=[],
    )
    assert request.contract_version == "010A-v1"
    assert package.rank_count == 1


def test_runtime_validates_contract_version():
    runtime = ResponseRuntime()
    with pytest.raises(ResponseRuntimeError, match="contract_version_unsupported"):
        runtime.validate_request(
            ResponseRequest(
                answer_request_id=uuid.uuid4(),
                contract_version="009B-v1",
            )
        )


def test_runtime_validates_answer_request_id_type():
    runtime = ResponseRuntime()
    with pytest.raises(ResponseRuntimeError, match="invalid_response_request"):
        runtime.validate_request(
            ResponseRequest(
                answer_request_id="not-a-uuid",  # type: ignore[arg-type]
                contract_version=CURRENT_CONTRACT_VERSION,
            )
        )


def test_provenance_fields_null_when_retrieval_join_missing():
    """Claude review: never derive legal_object_id or source_version_id from other fields."""
    entry = SimpleNamespace(
        presentation_order_index=1,
        retrieval_evidence_reference_id=uuid.uuid4(),
        ranked_evidence_reference_id=uuid.uuid4(),
    )
    session = MagicMock()
    session.get.return_value = None

    from app.services.response_runtime.rendering import _map_evidence_entry

    mapped = _map_evidence_entry(
        session,
        entry=entry,
        include_rendered_citation_text=False,
    )
    assert mapped.legal_object_id is None
    assert mapped.source_version_id is None
    assert mapped.object_identifier is None
    assert mapped.location_reference is None
    session.get.assert_called_with(RetrievalEvidenceReference, entry.retrieval_evidence_reference_id)


def test_provenance_fields_pass_through_from_retrieval_row():
    retrieval_id = uuid.uuid4()
    source_version_id = uuid.uuid4()
    retrieval_row = SimpleNamespace(
        legal_object_id="lo-pass-through",
        source_version_id=source_version_id,
        object_identifier="obj-pass",
        location_reference="loc-pass",
        citation_id=None,
        citation_hash=None,
    )
    entry = SimpleNamespace(
        presentation_order_index=1,
        retrieval_evidence_reference_id=retrieval_id,
        ranked_evidence_reference_id=uuid.uuid4(),
    )
    session = MagicMock()
    session.get.return_value = retrieval_row
    session.execute.return_value.scalar_one_or_none.return_value = None

    from app.services.response_runtime.rendering import _map_evidence_entry

    mapped = _map_evidence_entry(
        session,
        entry=entry,
        include_rendered_citation_text=False,
    )
    assert mapped.legal_object_id == "lo-pass-through"
    assert mapped.source_version_id == source_version_id
    assert mapped.object_identifier == "obj-pass"
    assert mapped.location_reference == "loc-pass"


def test_build_response_maps_non_deliverable_terminal_to_runtime_vocabulary():
    terminal = SimpleNamespace(
        id=uuid.uuid4(),
        answer_request_id=uuid.uuid4(),
        answer_status="failed",
        rank_count=0,
        created_at=uuid.uuid4(),
    )
    request = ResponseRequest(
        answer_request_id=terminal.answer_request_id,
        contract_version=CURRENT_CONTRACT_VERSION,
        answer_result_id=terminal.id,
    )
    runtime = ResponseRuntime()
    with patch("app.services.response_runtime.runtime.get_answer_request", return_value=object()):
        with patch("app.services.response_runtime.runtime.get_answer_result", return_value=terminal):
            outcome = runtime.run(MagicMock(), request)
    assert outcome.response_status == RESPONSE_STATUS_FAILED
    assert outcome.error_category == "answer_not_deliverable"
    assert outcome.response_package is None
    assert outcome.error_category != "duplicate_answer"


def test_response_runtime_import_guards():
    runtime_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "response_runtime"
    for path in runtime_dir.glob("*.py"):
        text = path.read_text()
        for token in (
            "create_answer_request",
            "create_answer_result",
            "create_answer_evidence_entry",
            "create_answer_uncertainty_flag",
            "persist_answer_for_ranking_request",
            "assemble_answer_package",
            "resolve_ranking_assembly_inputs",
            "CitationAssembler",
            "rabbitmq",
            "kafka",
        ):
            assert token not in text, f"{token} must not appear in {path.name}"
        for line in text.splitlines():
            stripped = line.strip().lower()
            if not stripped.startswith(("import ", "from ")):
                continue
            for prefix in PROHIBITED_IMPORT_PREFIXES:
                if stripped.startswith(prefix.lower()):
                    raise AssertionError(f"{prefix} forbidden in {path.name}: {line}")


def test_response_runtime_has_no_persistence_or_orchestration_logic():
    runtime_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "response_runtime"
    sources = "".join(path.read_text() for path in runtime_dir.glob("*.py")).lower()
    for token in FORBIDDEN_RUNTIME_TOKENS:
        assert token.lower() not in sources, f"{token} must not appear in response_runtime"


def test_response_runtime_package_has_no_extra_modules():
    runtime_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "response_runtime"
    names = {path.name for path in runtime_dir.glob("*.py")}
    assert names == {"__init__.py", "models.py", "runtime.py", "rendering.py"}


@pytest.mark.integration
def test_end_to_end_build_response_after_worker(db_session):
    ranking_request_id = _complete_ranking(db_session, [{"object_identifier": "resp-obj-1"}])
    worker_outcome = run_answer_worker(
        db_session,
        build_answer_worker_request(ranking_request_id=ranking_request_id),
    )
    assert worker_outcome.answer_status == "completed"

    request = ResponseRequest(
        answer_request_id=worker_outcome.answer_request_id,
        contract_version=CURRENT_CONTRACT_VERSION,
        include_rendered_citation_text=True,
    )
    with patch.object(db_session, "commit", side_effect=AssertionError("commit not allowed")):
        outcome = build_response(db_session, request)

    assert outcome.response_status == RESPONSE_STATUS_COMPLETED
    assert outcome.response_package is not None
    package = outcome.response_package
    assert package.contract_version == CURRENT_CONTRACT_VERSION
    assert package.answer_request_id == worker_outcome.answer_request_id
    assert package.rank_count == 1
    assert len(package.evidence_entries) == 1
    assert package.evidence_entries[0].presentation_order_index == 1
    assert package.evidence_entries[0].legal_object_id is not None
    assert package.evidence_entries[0].source_version_id is not None
    assert package.response_metadata is not None
    assert package.response_metadata.rendering_mode == "deterministic"
    assert package.evidence_entries[0].citation_reference is not None
    assert package.evidence_entries[0].citation_reference.rendered_citation_text is not None


@pytest.mark.integration
def test_build_response_omits_rendered_citation_when_flag_false(db_session):
    ranking_request_id = _complete_ranking(db_session, [{}])
    worker_outcome = run_answer_worker(
        db_session,
        build_answer_worker_request(ranking_request_id=ranking_request_id),
    )
    outcome = build_response(
        db_session,
        ResponseRequest(
            answer_request_id=worker_outcome.answer_request_id,
            contract_version=CURRENT_CONTRACT_VERSION,
            include_rendered_citation_text=False,
        ),
    )
    assert outcome.response_status == RESPONSE_STATUS_COMPLETED
    assert outcome.response_package is not None
    citation_ref = outcome.response_package.evidence_entries[0].citation_reference
    assert citation_ref is not None
    assert citation_ref.citation_id is not None
    assert citation_ref.rendered_citation_text is None


@pytest.mark.integration
def test_build_response_is_deterministic(db_session):
    ranking_request_id = _complete_ranking(db_session, [{}])
    worker_outcome = run_answer_worker(
        db_session,
        build_answer_worker_request(ranking_request_id=ranking_request_id),
    )
    request = ResponseRequest(
        answer_request_id=worker_outcome.answer_request_id,
        contract_version=CURRENT_CONTRACT_VERSION,
        include_rendered_citation_text=False,
    )
    first = build_response(db_session, request)
    second = build_response(db_session, request)
    assert first == second


@pytest.mark.integration
def test_build_response_zero_evidence(db_session):
    from tests.test_answer_persistence import _zero_evidence_ranking

    ranking_request_id, _ = _zero_evidence_ranking(db_session)
    worker_outcome = run_answer_worker(
        db_session,
        build_answer_worker_request(ranking_request_id=ranking_request_id),
    )
    outcome = build_response(
        db_session,
        ResponseRequest(
            answer_request_id=worker_outcome.answer_request_id,
            contract_version=CURRENT_CONTRACT_VERSION,
        ),
    )
    assert outcome.response_status == RESPONSE_STATUS_COMPLETED
    assert outcome.response_package is not None
    assert outcome.response_package.rank_count == 0
    assert outcome.response_package.evidence_entries == []
    assert any(
        flag.flag_type == "zero_evidence" for flag in outcome.response_package.uncertainty_flags
    )


@pytest.mark.integration
def test_build_response_answer_request_not_found(db_session):
    with pytest.raises(ResponseRuntimeError, match="answer_request_not_found"):
        build_response(
            db_session,
            ResponseRequest(
                answer_request_id=uuid.uuid4(),
                contract_version=CURRENT_CONTRACT_VERSION,
            ),
        )


@pytest.mark.integration
def test_build_response_duplicate_rejected_maps_to_answer_not_deliverable(db_session):
    ranking_request_id = _complete_ranking(db_session, [{}])
    request = build_answer_worker_request(ranking_request_id=ranking_request_id)
    first = run_answer_worker(db_session, request)
    assert first.answer_status == "completed"
    second = run_answer_worker(db_session, request)
    assert second.answer_status == "duplicate_rejected"

    outcome = build_response(
        db_session,
        ResponseRequest(
            answer_request_id=second.answer_request_id,
            contract_version=CURRENT_CONTRACT_VERSION,
            answer_result_id=second.answer_result_id,
        ),
    )
    assert outcome.response_status == RESPONSE_STATUS_FAILED
    assert outcome.error_category == "answer_not_deliverable"
    assert outcome.error_category != "duplicate_answer"
