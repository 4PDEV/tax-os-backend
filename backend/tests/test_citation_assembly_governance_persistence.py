import inspect
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.datetime_utils import utc_now
from app.models.citation_assembly_governance_request import CitationAssemblyGovernanceRequest
from app.models.citation_assembly_governance_result import CitationAssemblyGovernanceResult
from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.models.source_version import SourceVersion
from app.services.citation_assembly_governance import (
    CitationAssemblyGovernancePersistenceError,
    compute_request_hash,
    create_citation_assembly_request,
    find_existing_default_request_for_version,
    get_citation_assembly_request,
    get_latest_result_for_request,
    list_results_for_request,
    persist_citation_assembly_result,
)
from app.services.legal_object_promotion import create_promotion_request
from app.workers.legal_object_promotion import run_controlled_legal_object_promotion
from tests.test_legal_object_promotion_persistence import _seed_parsed_structure

pytestmark = pytest.mark.integration


def _seed_legal_object_version(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="seed for citation persistence",
    )
    run_controlled_legal_object_promotion(db_session, controlled_promotion=True)
    version = db_session.execute(select(LegalObjectVersion)).scalar_one()
    return version, parsed, extracted


def test_citation_assembly_request_creation(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    request = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="admin",
        requested_by_actor_identifier="qa-reviewer",
        citation_reason="manual citation assembly review",
        force_reassembly=False,
        notes="governance-only request",
    )
    assert request.id is not None
    assert request.legal_object_id == version.legal_object_id
    assert request.legal_object_version_id == version.legal_object_version_id
    assert request.source_version_id == extracted.source_version_id
    assert request.force_reassembly is False


def test_request_hash_deterministic_for_version_only():
    from uuid import uuid4

    version_id = uuid4()
    hash_one = compute_request_hash(legal_object_version_id=version_id, force_reassembly=False)
    hash_two = compute_request_hash(legal_object_version_id=version_id, force_reassembly=False)
    assert hash_one == hash_two


def test_request_hash_ignores_request_metadata(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    request = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="reason A",
        force_reassembly=False,
    )
    expected = compute_request_hash(
        legal_object_version_id=version.legal_object_version_id, force_reassembly=False
    )
    assert request.request_hash == expected


def test_request_hash_changes_with_different_reason_or_actor(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    first = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="reason A",
        force_reassembly=False,
    )
    with pytest.raises(CitationAssemblyGovernancePersistenceError):
        create_citation_assembly_request(
            db_session,
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=extracted.source_version_id,
            requested_by_actor_type="admin",
            citation_reason="reason B",
            force_reassembly=False,
        )
    assert first.request_hash == compute_request_hash(
        legal_object_version_id=version.legal_object_version_id, force_reassembly=False
    )


def test_duplicate_default_request_rejected(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="first",
        force_reassembly=False,
    )
    with pytest.raises(CitationAssemblyGovernancePersistenceError):
        create_citation_assembly_request(
            db_session,
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=extracted.source_version_id,
            requested_by_actor_type="admin",
            citation_reason="different reason still duplicate",
            force_reassembly=False,
        )


def test_force_reassembly_allows_new_request(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    first = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="same request",
        force_reassembly=False,
    )
    second = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="same request",
        force_reassembly=True,
    )
    assert first.id != second.id
    assert first.request_hash != second.request_hash


def test_result_persistence_and_append_only_history(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    request = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="system",
        citation_reason="queue assembly",
    )
    first = persist_citation_assembly_result(
        db_session,
        citation_assembly_governance_request_id=request.id,
        citation_status="failed",
        error_category="citation_pipeline_unavailable",
        error_message="worker not reachable",
    )
    second = persist_citation_assembly_result(
        db_session,
        citation_assembly_governance_request_id=request.id,
        citation_status="accepted",
        notes="retry accepted",
    )
    all_results = list_results_for_request(
        db_session, citation_assembly_governance_request_id=request.id
    )
    latest = get_latest_result_for_request(
        db_session, citation_assembly_governance_request_id=request.id
    )
    assert [r.id for r in all_results] == [first.id, second.id]
    assert latest is not None
    assert latest.id == second.id
    assert latest.legal_object_id == version.legal_object_id
    assert latest.legal_object_version_id == version.legal_object_version_id


def test_failed_rejected_skipped_results_preserved(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    request = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="test",
        citation_reason="status coverage",
    )
    for status, category in [
        ("rejected", "invalid_request"),
        ("skipped", None),
        ("duplicate_rejected", "duplicate_citation"),
    ]:
        persist_citation_assembly_result(
            db_session,
            citation_assembly_governance_request_id=request.id,
            citation_status=status,
            error_category=category,
        )
    assert (
        len(
            list_results_for_request(
                db_session, citation_assembly_governance_request_id=request.id
            )
        )
        == 3
    )


def test_enum_validation(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    with pytest.raises(ValueError):
        create_citation_assembly_request(
            db_session,
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=extracted.source_version_id,
            requested_by_actor_type="invalid",
            citation_reason="bad actor",
        )


def test_fk_integrity_and_get_request(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    request = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="admin",
        citation_reason="fk integrity check",
    )
    loaded = get_citation_assembly_request(
        db_session, citation_assembly_governance_request_id=request.id
    )
    assert loaded is not None
    assert loaded.legal_object_version_id == version.legal_object_version_id


def test_legal_object_missing(db_session):
    from uuid import uuid4

    version, _, extracted = _seed_legal_object_version(db_session)
    with pytest.raises(CitationAssemblyGovernancePersistenceError) as exc:
        create_citation_assembly_request(
            db_session,
            legal_object_id="missing-object",
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=extracted.source_version_id,
            requested_by_actor_type="admin",
            citation_reason="missing object",
        )
    assert "legal_object_missing" in str(exc.value)


def test_version_missing(db_session):
    from uuid import uuid4

    version, _, extracted = _seed_legal_object_version(db_session)
    with pytest.raises(CitationAssemblyGovernancePersistenceError) as exc:
        create_citation_assembly_request(
            db_session,
            legal_object_id=version.legal_object_id,
            legal_object_version_id=uuid4(),
            source_version_id=extracted.source_version_id,
            requested_by_actor_type="admin",
            citation_reason="missing version",
        )
    assert "version_missing" in str(exc.value)


def test_version_belongs_to_legal_object_validation(db_session):
    from uuid import uuid4

    from app.services.citation_assembly_governance.validation import validate_legal_memory_lineage

    version, _, _ = _seed_legal_object_version(db_session)
    other_source_id = uuid4()

    class _StubVersion:
        legal_object_id = "other-object-id"
        source_version_id = version.source_version_id

    with pytest.raises(ValueError, match="invalid_request"):
        validate_legal_memory_lineage(
            db_session.get(LegalObject, version.legal_object_id),
            _StubVersion(),
            db_session.get(SourceVersion, version.source_version_id),
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=version.source_version_id,
        )

    with pytest.raises(CitationAssemblyGovernancePersistenceError) as exc:
        create_citation_assembly_request(
            db_session,
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=other_source_id,
            requested_by_actor_type="admin",
            citation_reason="mismatched source",
        )
    assert "provenance_incomplete" in str(exc.value)


def test_find_existing_default_request_for_version(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    request = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="user",
        citation_reason="existing lookup",
    )
    existing = find_existing_default_request_for_version(
        db_session, legal_object_version_id=version.legal_object_version_id
    )
    assert existing is not None
    assert existing.id == request.id


def test_citation_id_nullable_no_citation_content(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    request = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="test",
        citation_reason="nullable citation_id",
    )
    result = persist_citation_assembly_result(
        db_session,
        citation_assembly_governance_request_id=request.id,
        citation_status="accepted",
        citation_id=None,
    )
    assert result.citation_id is None
    assert result.assembled_at is None


def test_assembled_at_on_terminal_success(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    request = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        citation_reason="assembled timestamp",
    )
    now = utc_now()
    result = persist_citation_assembly_result(
        db_session,
        citation_assembly_governance_request_id=request.id,
        citation_status="assembled",
        assembled_at=now,
    )
    assert result.assembled_at == now


def test_no_side_effects_beyond_governance_tables(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    legal_before = db_session.query(LegalObject).count()
    version_before = db_session.query(LegalObjectVersion).count()

    request = create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="admin",
        citation_reason="persistence only",
    )
    persist_citation_assembly_result(
        db_session,
        citation_assembly_governance_request_id=request.id,
        citation_status="pending",
    )

    assert db_session.query(LegalObject).count() == legal_before
    assert db_session.query(LegalObjectVersion).count() == version_before


def test_db_rejects_duplicate_default_request_at_constraint_level(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    now = utc_now()
    first = CitationAssemblyGovernanceRequest(
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        citation_reason="direct insert one",
        requested_by_actor_type="worker",
        requested_by_actor_identifier=None,
        requested_at=now,
        force_reassembly=False,
        request_hash=compute_request_hash(
            legal_object_version_id=version.legal_object_version_id, force_reassembly=False
        ),
        notes=None,
        created_at=now,
    )
    db_session.add(first)
    db_session.flush()

    second = CitationAssemblyGovernanceRequest(
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        citation_reason="direct insert two",
        requested_by_actor_type="admin",
        requested_by_actor_identifier=None,
        requested_at=now,
        force_reassembly=False,
        request_hash=compute_request_hash(
            legal_object_version_id=version.legal_object_version_id, force_reassembly=False
        ),
        notes=None,
        created_at=now,
    )
    db_session.add(second)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_db_allows_multiple_force_reassembly_requests(db_session):
    version, _, extracted = _seed_legal_object_version(db_session)
    now = utc_now()
    for _ in range(2):
        row = CitationAssemblyGovernanceRequest(
            legal_object_id=version.legal_object_id,
            legal_object_version_id=version.legal_object_version_id,
            source_version_id=extracted.source_version_id,
            citation_reason="force replay",
            requested_by_actor_type="worker",
            requested_by_actor_identifier=None,
            requested_at=now,
            force_reassembly=True,
            request_hash=compute_request_hash(
                legal_object_version_id=version.legal_object_version_id,
                force_reassembly=True,
            ),
            notes=None,
            created_at=now,
        )
        db_session.add(row)
    db_session.flush()


def test_no_task_004d_assembler_or_retrieval_in_governance_package():
    pkg_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "citation_assembly_governance"
    forbidden = (
        "CitationAssembler",
        "app.services.citation.assembler",
        "app.services.retrieval",
    )
    for path in pkg_dir.glob("*.py"):
        source = path.read_text()
        for token in forbidden:
            assert token not in source, f"{token} must not appear in {path.name}"


def test_governance_tables_only_no_final_citation_entity(db_session, engine):
    from sqlalchemy import inspect as sa_inspect

    version, _, extracted = _seed_legal_object_version(db_session)
    create_citation_assembly_request(
        db_session,
        legal_object_id=version.legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="test",
        citation_reason="boundary check",
    )
    tables = set(sa_inspect(engine).get_table_names())
    assert "citation_assembly_governance_requests" in tables
    assert "citation_assembly_governance_results" in tables
    assert "citations" not in tables
    assert not any(name == "citation_assembly_requests" for name in tables)
    assert not any("answer" in name for name in tables)


def test_persistence_module_avoids_004d_request_dto_names():
    from app.services import citation_assembly_governance

    exported = set(citation_assembly_governance.__all__)
    assert "CitationAssemblyRequest" not in exported
    assert "CitationAssemblyResult" not in exported
    persistence_source = inspect.getsource(citation_assembly_governance.persistence)
    assert "CitationAssembler" not in persistence_source
