"""TASK-009A answer assembly tests."""

import uuid
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.datetime_utils import utc_now
from app.services.answer_assembly import (
    ANSWER_ERROR_CATEGORIES,
    AnswerAssemblyError,
    assemble_answer_package,
    resolve_ranking_assembly_inputs,
)
from app.services.ranking_execution import execute_controlled_ranking
from app.services.ranking_persistence import (
    create_ranked_evidence_reference,
    create_ranking_request,
    create_ranking_result,
    list_ranked_evidence_references,
    list_results_for_request,
)
from app.services.retrieval_persistence import create_retrieval_result
from tests.test_controlled_ranking_execution import (
    _accepted_result,
    _seed_completed_retrieval_with_evidence,
)
from tests.test_retrieval_persistence import _create_request

PROHIBITED_IMPORT_PREFIXES = (
    "from app.services.retrieval_execution",
    "import app.services.retrieval_execution",
    "from app.services.ranking_execution",
    "import app.services.ranking_execution",
    "from app.services.ai",
    "import app.services.ai",
    "from app.services.semantic",
    "import app.services.semantic",
    "from app.services.vector",
    "import app.services.vector",
    "from app.services.citation.assembler",
    "import app.services.citation.assembler",
    "from app.workers.answer_runtime",
    "import app.workers.answer_runtime",
    "from app.workers.ranking_runtime",
    "import app.workers.ranking_runtime",
    "from app.workers.retrieval_runtime",
    "import app.workers.retrieval_runtime",
)


def _complete_ranking(db_session, evidence_specs):
    _, result, _ = _seed_completed_retrieval_with_evidence(db_session, evidence_specs)
    outcome = execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
    )
    assert outcome.ranking_status == "completed"
    return outcome.ranking_request_id, result.id


@pytest.mark.integration
def test_rl_t01_terminal_completed_lookup(db_session):
    ranking_request_id, _ = _complete_ranking(db_session, [{}])
    inputs = resolve_ranking_assembly_inputs(db_session, ranking_request_id=ranking_request_id)
    assert inputs.terminal_ranking_result.ranking_status == "completed"


@pytest.mark.integration
def test_rl_t02_accepted_lookup(db_session):
    ranking_request_id, _ = _complete_ranking(db_session, [{}])
    inputs = resolve_ranking_assembly_inputs(db_session, ranking_request_id=ranking_request_id)
    assert inputs.accepted_ranking_result.ranking_status == "accepted"


@pytest.mark.integration
def test_rl_t03_ranked_rows_parented_to_accepted(db_session):
    ranking_request_id, _ = _complete_ranking(db_session, [{"object_identifier": "a"}])
    inputs = resolve_ranking_assembly_inputs(db_session, ranking_request_id=ranking_request_id)
    ranked_on_accepted = list_ranked_evidence_references(
        db_session,
        ranking_result_id=inputs.accepted_ranking_result.id,
    )
    ranked_on_terminal = list_ranked_evidence_references(
        db_session,
        ranking_result_id=inputs.terminal_ranking_result.id,
    )
    assert len(ranked_on_accepted) == 1
    assert ranked_on_terminal == []
    assert inputs.ranked_rows[0].ranking_result_id == inputs.accepted_ranking_result.id


@pytest.mark.integration
def test_rl_t04_presentation_order_preserved(db_session):
    ranking_request_id, _ = _complete_ranking(
        db_session,
        [{"object_identifier": "a"}, {"object_identifier": "b"}],
    )
    inputs = resolve_ranking_assembly_inputs(db_session, ranking_request_id=ranking_request_id)
    indices = [row.presentation_order_index for row in inputs.ranked_rows]
    assert indices == sorted(indices)
    assert indices == [1, 2]


@pytest.mark.integration
def test_rl_t05_count_integrity(db_session):
    ranking_request_id, _ = _complete_ranking(db_session, [{"object_identifier": "a"}])
    inputs = resolve_ranking_assembly_inputs(db_session, ranking_request_id=ranking_request_id)
    assert len(inputs.ranked_rows) == inputs.terminal_ranking_result.rank_count


@pytest.mark.integration
def test_rl_t06_missing_ranking_request_fails(db_session):
    outcome = assemble_answer_package(db_session, ranking_request_id=uuid.uuid4())
    assert outcome.answer_status == "failed"
    assert outcome.error_category == "ranking_result_not_completed"


@pytest.mark.integration
def test_rl_t07_package_ids_populated(db_session):
    ranking_request_id, _ = _complete_ranking(db_session, [{"object_identifier": "a"}])
    outcome = assemble_answer_package(db_session, ranking_request_id=ranking_request_id)
    package = outcome.answer_package
    assert package is not None
    assert package.terminal_ranking_result_id != package.accepted_ranking_result_id
    inputs = resolve_ranking_assembly_inputs(db_session, ranking_request_id=ranking_request_id)
    assert package.terminal_ranking_result_id == inputs.terminal_ranking_result.id
    assert package.accepted_ranking_result_id == inputs.accepted_ranking_result.id


@pytest.mark.integration
def test_rl_t08_failed_ranking_rejected(db_session):
    _, result, _ = _seed_completed_retrieval_with_evidence(db_session, [{}])
    ranking_request = create_ranking_request(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
        requested_by_actor_type="test",
    )
    create_ranking_result(
        db_session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=result.id,
        ranking_status="failed",
        error_category="permutation_mismatch",
        error_message="injected",
        completed_at=utc_now(),
    )
    outcome = assemble_answer_package(db_session, ranking_request_id=ranking_request.id)
    assert outcome.answer_status == "failed"
    assert outcome.error_category == "ranking_result_not_completed"


@pytest.mark.integration
def test_rl_t09_zero_evidence_package(db_session):
    request = _create_request(db_session)
    result = create_retrieval_result(
        db_session,
        retrieval_request_id=request.id,
        retrieval_status="completed",
        result_count=0,
        completed_at=utc_now(),
    )
    ranking_outcome = execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
    )
    outcome = assemble_answer_package(
        db_session,
        ranking_request_id=ranking_outcome.ranking_request_id,
    )
    assert outcome.answer_status == "completed"
    package = outcome.answer_package
    assert package is not None
    assert package.rank_count == 0
    assert package.evidence_entries == ()
    assert any(flag.flag_type == "zero_evidence" for flag in package.uncertainty_flags)


@pytest.mark.integration
def test_rl_t10_retrieval_scope_mismatch_fails(db_session):
    ranking_request_id, retrieval_result_id = _complete_ranking(
        db_session,
        [{"object_identifier": "a"}],
    )
    accepted = _accepted_result(db_session, ranking_request_id)
    ranked = list_ranked_evidence_references(db_session, ranking_result_id=accepted.id)[0]
    other_request = _create_request(db_session)
    other_result = create_retrieval_result(
        db_session,
        retrieval_request_id=other_request.id,
        retrieval_status="completed",
        result_count=1,
        completed_at=utc_now(),
    )
    ranked.retrieval_result_id = other_result.id
    db_session.flush()
    outcome = assemble_answer_package(db_session, ranking_request_id=ranking_request_id)
    assert outcome.answer_status == "failed"
    assert outcome.error_category == "retrieval_result_mismatch"


@pytest.mark.integration
def test_accepted_without_terminal_completed_fails(db_session):
    _, result, _ = _seed_completed_retrieval_with_evidence(db_session, [{}])
    ranking_request = create_ranking_request(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
        requested_by_actor_type="test",
    )
    create_ranking_result(
        db_session,
        ranking_request_id=ranking_request.id,
        retrieval_result_id=result.id,
        ranking_status="accepted",
    )
    outcome = assemble_answer_package(db_session, ranking_request_id=ranking_request.id)
    assert outcome.answer_status == "failed"
    assert outcome.error_category == "ranking_result_not_completed"


@pytest.mark.integration
def test_evidence_count_mismatch_fails(db_session):
    ranking_request_id, _ = _complete_ranking(db_session, [{"object_identifier": "a"}])
    inputs = resolve_ranking_assembly_inputs(db_session, ranking_request_id=ranking_request_id)
    inputs.terminal_ranking_result.rank_count = 99
    db_session.flush()
    outcome = assemble_answer_package(db_session, ranking_request_id=ranking_request_id)
    assert outcome.answer_status == "failed"
    assert outcome.error_category == "evidence_count_mismatch"


@pytest.mark.integration
def test_duplicate_accepted_result_fails(db_session):
    _, result, _ = _seed_completed_retrieval_with_evidence(db_session, [{}])
    ranking_outcome = execute_controlled_ranking(
        db_session,
        retrieval_result_id=result.id,
        ranking_profile="CANONICAL",
    )
    create_ranking_result(
        db_session,
        ranking_request_id=ranking_outcome.ranking_request_id,
        retrieval_result_id=result.id,
        ranking_status="accepted",
    )
    outcome = assemble_answer_package(
        db_session,
        ranking_request_id=ranking_outcome.ranking_request_id,
    )
    assert outcome.answer_status == "failed"
    assert outcome.error_category == "accepted_ranking_result_missing"


@pytest.mark.integration
def test_evidence_completeness_one_to_one(db_session):
    ranking_request_id, _ = _complete_ranking(
        db_session,
        [{"object_identifier": "a"}, {"object_identifier": "b"}],
    )
    outcome = assemble_answer_package(db_session, ranking_request_id=ranking_request_id)
    package = outcome.answer_package
    assert package is not None
    assert len(package.evidence_entries) == 2
    indices = [entry.presentation_order_index for entry in package.evidence_entries]
    assert indices == [1, 2]


@pytest.mark.integration
def test_provenance_read_only_no_session_add(db_session):
    ranking_request_id, _ = _complete_ranking(db_session, [{"object_identifier": "a"}])
    original_add = db_session.add

    def guarded_add(instance, *args, **kwargs):
        module = type(instance).__module__
        if module.startswith("app.models."):
            raise AssertionError(f"unexpected ORM write: {type(instance).__name__}")
        return original_add(instance, *args, **kwargs)

    with patch.object(db_session, "add", side_effect=guarded_add):
        outcome = assemble_answer_package(db_session, ranking_request_id=ranking_request_id)
    assert outcome.answer_status == "completed"


@pytest.mark.integration
def test_citation_formatter_used_when_flag_true(db_session):
    ranking_request_id, _ = _complete_ranking(db_session, [{"object_identifier": "a"}])
    with patch(
        "app.services.answer_assembly.assembly.CitationFormatter.format",
        return_value="formatted-citation",
    ) as mocked:
        outcome = assemble_answer_package(
            db_session,
            ranking_request_id=ranking_request_id,
            include_rendered_citation_text=True,
        )
    assert outcome.answer_status == "completed"
    assert mocked.called
    entry = outcome.answer_package.evidence_entries[0]
    assert entry.citation_reference is not None
    assert entry.citation_reference.rendered_citation_text == "formatted-citation"


@pytest.mark.integration
def test_citation_formatter_not_called_when_flag_false(db_session):
    ranking_request_id, _ = _complete_ranking(db_session, [{"object_identifier": "a"}])
    with patch(
        "app.services.answer_assembly.assembly.CitationFormatter.format",
    ) as mocked:
        outcome = assemble_answer_package(
            db_session,
            ranking_request_id=ranking_request_id,
            include_rendered_citation_text=False,
        )
    assert outcome.answer_status == "completed"
    mocked.assert_not_called()
    entry = outcome.answer_package.evidence_entries[0]
    assert entry.citation_reference.rendered_citation_text is None


def test_citation_assembler_prohibited_in_service():
    service_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "answer_assembly"
    sources = "".join(path.read_text() for path in service_dir.glob("*.py")).lower()
    assert "citationassembler" not in sources
    assert "citation.assembler" not in sources


@pytest.mark.integration
def test_deterministic_assembly_structure(db_session):
    ranking_request_id, _ = _complete_ranking(
        db_session,
        [
            {"object_identifier": "b", "effective_from": date(2024, 6, 1)},
            {"object_identifier": "a", "effective_from": date(2024, 1, 1)},
        ],
    )
    first = assemble_answer_package(db_session, ranking_request_id=ranking_request_id)
    second = assemble_answer_package(db_session, ranking_request_id=ranking_request_id)
    assert first.answer_status == "completed"
    assert second.answer_status == "completed"
    ids_first = [e.retrieval_evidence_reference_id for e in first.answer_package.evidence_entries]
    ids_second = [e.retrieval_evidence_reference_id for e in second.answer_package.evidence_entries]
    assert ids_first == ids_second
    order_first = [e.presentation_order_index for e in first.answer_package.evidence_entries]
    order_second = [e.presentation_order_index for e in second.answer_package.evidence_entries]
    assert order_first == order_second


def test_canonical_error_categories_only():
    assert len(ANSWER_ERROR_CATEGORIES) == 10
    with pytest.raises(ValueError, match="invalid error_category"):
        AnswerAssemblyError("permutation_mismatch", "ranking layer")


def test_answer_assembly_import_guards():
    service_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "answer_assembly"
    for path in service_dir.glob("*.py"):
        for line in path.read_text().splitlines():
            stripped = line.strip().lower()
            if not stripped.startswith(("import ", "from ")):
                continue
            for prefix in PROHIBITED_IMPORT_PREFIXES:
                assert not stripped.startswith(prefix), f"{prefix} forbidden in {path.name}: {line}"


@pytest.mark.integration
def test_no_ranking_persistence_writes(db_session):
    ranking_request_id, _ = _complete_ranking(db_session, [{"object_identifier": "a"}])
    with patch("app.services.ranking_persistence.create_ranking_request") as create_request:
        with patch("app.services.ranking_persistence.create_ranking_result") as create_result:
            with patch(
                "app.services.ranking_persistence.create_ranked_evidence_reference"
            ) as create_ranked:
                outcome = assemble_answer_package(db_session, ranking_request_id=ranking_request_id)
    assert outcome.answer_status == "completed"
    create_request.assert_not_called()
    create_result.assert_not_called()
    create_ranked.assert_not_called()


def test_answer_package_has_no_prohibited_fields():
    service_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "answer_assembly"
    sources = "".join(path.read_text() for path in service_dir.glob("*.py")).lower()
    for token in (
        "answer_text",
        "legal_conclusion",
        "recommendation_text",
        "ranking_score",
        "semantic_score",
        "ai_score",
    ):
        assert token not in sources
