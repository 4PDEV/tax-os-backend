from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.datetime_utils import utc_now
from app.services.legal_object_convergence.enums import ConvergenceSource, ConvergenceStatus
from app.services.legal_object_convergence.models import ConvergedLegalObjectCandidate
from app.services.legal_object_extraction.enums import LegalObjectExtractionStatus, LegalObjectType
from app.services.legal_object_extraction.identity import generate_legal_object_id, sha256_text
from app.services.legal_object_extraction.models import LegalObjectCandidate
from app.services.legal_object_persistence_planning import (
    ALWAYS_RULES,
    BLOCKED_ASSUMPTIONS,
    BLOCKED_DIRECT_PERSISTENCE_SOURCES,
    CANONICAL_PERSISTENCE_INPUT,
    DUPLICATE_STRATEGY_RULES,
    LINEAGE_STRATEGY_RULES,
    MIGRATION_PHASES,
    NEVER_RULES,
    RISK_REGISTER,
    DuplicateScenario,
    LegalObjectPersistencePlanningError,
    MigrationPhase,
    PlannedLegalObjectPersistenceModel,
    assert_canonical_persistence_input,
    build_planned_persistence_model,
    get_strategy_for_scenario,
    is_approved_persistence_input,
    migration_phases_are_ordered,
    rules_are_complete,
)


def _converged(**kwargs) -> ConvergedLegalObjectCandidate:
    raw_text = kwargs.pop("raw_text", "Tax is due.")
    sid = str(kwargs.pop("source_version_id", uuid4()))
    canonical_path = kwargs.pop("canonical_path", "PART I > Section 15")
    object_label = kwargs.pop("object_label", "Section 15")
    th = sha256_text(raw_text)
    candidate = LegalObjectCandidate(
        source_version_id=sid,
        legal_object_id=generate_legal_object_id(
            source_version_id=sid,
            canonical_path=canonical_path,
            object_type=LegalObjectType.SECTION.value,
            object_label=object_label,
            start_offset=10,
            text_hash=th,
        ),
        object_type=LegalObjectType.SECTION,
        object_label=object_label,
        object_title=None,
        canonical_path=canonical_path,
        parent_legal_object_id=kwargs.pop("parent_legal_object_id", None),
        structural_unit_id="su-0001",
        start_offset=10,
        end_offset=20,
        raw_text=raw_text,
        text_hash=th,
        extraction_status=kwargs.pop(
            "extraction_status", LegalObjectExtractionStatus.SUCCESS
        ),
        extracted_at=utc_now(),
        extractor_version="1.0.0",
        metadata={},
    )
    return ConvergedLegalObjectCandidate(
        candidate=candidate,
        source_pipeline=kwargs.pop("source_pipeline", ConvergenceSource.STRUCTURAL_UNIT),
        convergence_status=kwargs.pop("convergence_status", ConvergenceStatus.CANONICAL),
        warnings=kwargs.pop("warnings", []),
        metadata=kwargs.pop("metadata", {}),
    )


def test_canonical_persistence_input_is_converged_candidate():
    assert CANONICAL_PERSISTENCE_INPUT is ConvergedLegalObjectCandidate


def test_blocked_direct_persistence_sources_documented():
    assert "segmentation" in BLOCKED_DIRECT_PERSISTENCE_SOURCES
    assert "legal_objects" in BLOCKED_DIRECT_PERSISTENCE_SOURCES
    assert "legal_object_extraction" in BLOCKED_DIRECT_PERSISTENCE_SOURCES
    assert "structure_parser" in BLOCKED_DIRECT_PERSISTENCE_SOURCES


def test_assert_canonical_persistence_input_accepts_converged():
    converged = _converged()
    assert assert_canonical_persistence_input(converged) is converged


def test_assert_canonical_persistence_input_rejects_non_converged():
    with pytest.raises(LegalObjectPersistencePlanningError, match="ConvergedLegalObjectCandidate"):
        assert_canonical_persistence_input({"not": "converged"})


def test_assert_canonical_persistence_input_rejects_rejected_convergence():
    converged = _converged(convergence_status=ConvergenceStatus.REJECTED)
    with pytest.raises(LegalObjectPersistencePlanningError, match="rejected"):
        assert_canonical_persistence_input(converged)


def test_is_approved_persistence_input():
    assert is_approved_persistence_input(_converged()) is True
    assert is_approved_persistence_input(object()) is False


def test_build_planned_persistence_model_from_converged():
    converged = _converged()
    planned = build_planned_persistence_model(converged)

    assert planned.legal_object_id == converged.candidate.legal_object_id
    assert planned.source_version_id == converged.candidate.source_version_id
    assert planned.text_hash == converged.candidate.text_hash
    assert planned.canonical_path == converged.candidate.canonical_path


def test_partial_convergence_planned_as_blocked():
    converged = _converged(convergence_status=ConvergenceStatus.PARTIAL)
    planned = build_planned_persistence_model(converged)
    assert planned.persistence_status.value == "blocked"


def test_duplicate_strategy_structure():
    scenarios = {rule.scenario for rule in DUPLICATE_STRATEGY_RULES}
    assert DuplicateScenario.DUPLICATE_TEXT_HASH in scenarios
    assert DuplicateScenario.CROSS_JURISDICTION_COLLISION in scenarios
    assert get_strategy_for_scenario(DuplicateScenario.CONFLICTING_LEGAL_OBJECT_ID).value == "reject"


def test_lineage_strategy_structure():
    assert len(LINEAGE_STRATEGY_RULES) >= 3
    expectations = {rule.expectation for rule in LINEAGE_STRATEGY_RULES}
    assert any("parent" in e.value for e in expectations)


def test_migration_phase_ordering():
    assert migration_phases_are_ordered() is True
    orders = [phase.order for phase in MIGRATION_PHASES]
    assert orders == [1, 2, 3, 4]
    assert MIGRATION_PHASES[0].phase == MigrationPhase.PHASE_1_TABLES
    assert MIGRATION_PHASES[-1].phase == MigrationPhase.PHASE_4_CITATION_ANCHORS


def test_persistence_rule_completeness():
    assert rules_are_complete() is True
    assert "persist unconverged candidates" in NEVER_RULES
    assert "preserve text_hash" in ALWAYS_RULES
    assert "preserve source_version_id" in ALWAYS_RULES


def test_risk_register_not_empty():
    assert len(RISK_REGISTER) >= 6
    categories = {risk.category for risk in RISK_REGISTER}
    assert "convergence_bypass" in {c.value for c in categories}
    assert len(BLOCKED_ASSUMPTIONS) >= 3


def test_planned_model_forbids_extra_fields():
    converged = _converged()
    planned = build_planned_persistence_model(converged)
    with pytest.raises(ValidationError):
        PlannedLegalObjectPersistenceModel(
            **planned.model_dump(),
            extra_field="not allowed",
        )


def test_no_persistence_implementation_in_module():
    import app.services.legal_object_persistence_planning as planning

    assert not hasattr(planning, "repository")
    assert not hasattr(planning, "Session")
