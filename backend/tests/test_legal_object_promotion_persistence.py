import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.datetime_utils import utc_now
from app.models.legal_object import LegalObject
from app.models.legal_object_promotion_request import LegalObjectPromotionRequest
from app.models.legal_object_promotion_result import LegalObjectPromotionResult
from app.models.legal_object_version import LegalObjectVersion
from app.models.parsed_structure import ParsedStructure
from app.models.parser_run import ParserRun
from app.services.ingestion.enums import ParserRunStatus, STRUCTURE_TYPE_STRUCTURAL_UNITS
from app.services.ingestion.hashing import sha256_structure
from app.services.legal_object_promotion import (
    LegalObjectPromotionPersistenceError,
    compute_promotion_hash,
    create_promotion_request,
    find_existing_default_promotion,
    get_latest_result_for_request,
    get_promotion_request,
    list_results_for_request,
    persist_promotion_result,
)
from tests.test_controlled_parsing_execution import SAMPLE_LEGAL_TEXT, _seed_extracted_text

pytestmark = pytest.mark.integration

_UNITS = [
    {
        "unit_type": "section",
        "unit_label": "15",
        "unit_title": None,
        "full_heading": "Section 15",
        "parent_unit_id": None,
        "hierarchy_level": 1,
        "start_offset": 0,
        "end_offset": 10,
        "raw_text": "Section 15",
    }
]


def _seed_parsed_structure(db_session, *, parser_status: str = ParserRunStatus.SUCCESS.value):
    extracted = _seed_extracted_text(db_session, raw_text=SAMPLE_LEGAL_TEXT)
    run = ParserRun(
        extraction_run_id=extracted.extraction_run_id,
        parser_name="test_parser",
        parser_version="1.0.0",
        parser_status=parser_status,
        started_at=utc_now(),
        completed_at=utc_now() if parser_status != ParserRunStatus.PENDING.value else None,
    )
    db_session.add(run)
    db_session.flush()
    structure_hash = sha256_structure(_UNITS)
    parsed = ParsedStructure(
        parser_run_id=run.id,
        source_version_id=extracted.source_version_id,
        structure_type=STRUCTURE_TYPE_STRUCTURAL_UNITS,
        structure_json={"structure_type": STRUCTURE_TYPE_STRUCTURAL_UNITS, "units": _UNITS},
        structure_hash=structure_hash,
    )
    db_session.add(parsed)
    db_session.flush()
    return parsed, extracted


def test_promotion_request_creation(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    request = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="admin",
        requested_by_actor_identifier="qa-reviewer",
        promotion_reason="manual promotion review",
        force_repromotion=False,
        notes="governance-only request",
    )
    assert request.id is not None
    assert request.parsed_structure_id == parsed.id
    assert request.source_version_id == extracted.source_version_id
    assert request.force_repromotion is False


def test_promotion_hash_deterministic_for_parsed_structure_only():
    from uuid import uuid4

    parsed_structure_id = uuid4()
    hash_one = compute_promotion_hash(parsed_structure_id=parsed_structure_id, force_repromotion=False)
    hash_two = compute_promotion_hash(parsed_structure_id=parsed_structure_id, force_repromotion=False)
    assert hash_one == hash_two


def test_promotion_hash_ignores_request_metadata(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    request = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="reason A",
        force_repromotion=False,
    )
    expected = compute_promotion_hash(parsed_structure_id=parsed.id, force_repromotion=False)
    assert request.promotion_hash == expected


def test_duplicate_default_promotion_rejected_when_force_repromotion_false(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="first",
        force_repromotion=False,
    )
    with pytest.raises(LegalObjectPromotionPersistenceError):
        create_promotion_request(
            db_session,
            parsed_structure_id=parsed.id,
            source_version_id=extracted.source_version_id,
            requested_by_actor_type="admin",
            promotion_reason="different reason still duplicate",
            force_repromotion=False,
        )


def test_force_repromotion_allows_new_request(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    first = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="same request",
        force_repromotion=False,
    )
    second = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="same request",
        force_repromotion=True,
    )
    assert first.id != second.id
    assert first.promotion_hash != second.promotion_hash


def test_promotion_result_persistence_and_append_only_history(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    request = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="system",
        promotion_reason="queue promotion",
    )
    first = persist_promotion_result(
        db_session,
        legal_object_promotion_request_id=request.id,
        promotion_status="failed",
        error_category="promotion_pipeline_unavailable",
        error_message="worker not reachable",
    )
    second = persist_promotion_result(
        db_session,
        legal_object_promotion_request_id=request.id,
        promotion_status="accepted",
        notes="retry accepted",
    )

    all_results = list_results_for_request(
        db_session, legal_object_promotion_request_id=request.id
    )
    latest = get_latest_result_for_request(
        db_session, legal_object_promotion_request_id=request.id
    )
    assert [r.id for r in all_results] == [first.id, second.id]
    assert latest is not None
    assert latest.id == second.id


def test_failed_rejected_skipped_results_preserved(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    request = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="test",
        promotion_reason="status coverage",
    )
    for status, category in [
        ("rejected", "invalid_request"),
        ("skipped", None),
        ("duplicate_rejected", "duplicate_promotion"),
    ]:
        persist_promotion_result(
            db_session,
            legal_object_promotion_request_id=request.id,
            promotion_status=status,
            error_category=category,
        )
    assert len(list_results_for_request(db_session, legal_object_promotion_request_id=request.id)) == 3


def test_enum_validation(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    with pytest.raises(ValueError):
        create_promotion_request(
            db_session,
            parsed_structure_id=parsed.id,
            source_version_id=extracted.source_version_id,
            requested_by_actor_type="invalid",
            promotion_reason="bad actor",
        )


def test_fk_integrity_and_get_request(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    request = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="admin",
        promotion_reason="fk integrity check",
    )
    loaded = get_promotion_request(db_session, legal_object_promotion_request_id=request.id)
    assert loaded is not None
    assert loaded.parsed_structure_id == parsed.id


def test_parsed_structure_missing(db_session):
    from uuid import uuid4

    with pytest.raises(LegalObjectPromotionPersistenceError) as exc:
        create_promotion_request(
            db_session,
            parsed_structure_id=uuid4(),
            source_version_id=uuid4(),
            requested_by_actor_type="admin",
            promotion_reason="missing structure",
        )
    assert "parsed_structure_missing" in str(exc.value)


def test_parser_run_incomplete(db_session):
    parsed, extracted = _seed_parsed_structure(db_session, parser_status=ParserRunStatus.FAILED.value)
    with pytest.raises(LegalObjectPromotionPersistenceError) as exc:
        create_promotion_request(
            db_session,
            parsed_structure_id=parsed.id,
            source_version_id=extracted.source_version_id,
            requested_by_actor_type="admin",
            promotion_reason="should fail",
        )
    assert "parser_run_incomplete" in str(exc.value)


def test_find_existing_default_promotion(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    request = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="user",
        promotion_reason="existing lookup",
    )
    existing = find_existing_default_promotion(db_session, parsed_structure_id=parsed.id)
    assert existing is not None
    assert existing.id == request.id


def test_legal_object_id_reference_without_auto_creation(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    legal_before = db_session.query(LegalObject).count()
    version_before = db_session.query(LegalObjectVersion).count()

    request = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="test",
        promotion_reason="nullable legal_object_id",
    )
    result = persist_promotion_result(
        db_session,
        legal_object_promotion_request_id=request.id,
        promotion_status="accepted",
        legal_object_id=None,
    )
    assert result.legal_object_id is None
    assert db_session.query(LegalObject).count() == legal_before
    assert db_session.query(LegalObjectVersion).count() == version_before


def test_no_side_effects_on_legal_memory_or_parsed_structures(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    parsed_before = db_session.query(ParsedStructure).count()
    legal_before = db_session.query(LegalObject).count()

    request = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="admin",
        promotion_reason="persistence only",
    )
    persist_promotion_result(
        db_session,
        legal_object_promotion_request_id=request.id,
        promotion_status="pending",
    )

    assert db_session.query(ParsedStructure).count() == parsed_before
    assert db_session.query(LegalObject).count() == legal_before


def test_db_rejects_duplicate_default_promotion_at_constraint_level(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    now = utc_now()
    first = LegalObjectPromotionRequest(
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        promotion_reason="direct insert one",
        requested_by_actor_type="worker",
        requested_by_actor_identifier=None,
        requested_at=now,
        force_repromotion=False,
        promotion_hash=compute_promotion_hash(parsed_structure_id=parsed.id, force_repromotion=False),
        notes=None,
        created_at=now,
    )
    db_session.add(first)
    db_session.flush()

    second = LegalObjectPromotionRequest(
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        promotion_reason="direct insert two",
        requested_by_actor_type="admin",
        requested_by_actor_identifier=None,
        requested_at=now,
        force_repromotion=False,
        promotion_hash=compute_promotion_hash(parsed_structure_id=parsed.id, force_repromotion=False),
        notes=None,
        created_at=now,
    )
    db_session.add(second)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_db_allows_multiple_force_repromotion_requests_same_parsed_structure(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    now = utc_now()
    for _ in range(2):
        row = LegalObjectPromotionRequest(
            parsed_structure_id=parsed.id,
            source_version_id=extracted.source_version_id,
            promotion_reason="force replay",
            requested_by_actor_type="worker",
            requested_by_actor_identifier=None,
            requested_at=now,
            force_repromotion=True,
            promotion_hash=compute_promotion_hash(
                parsed_structure_id=parsed.id, force_repromotion=True
            ),
            notes=None,
            created_at=now,
        )
        db_session.add(row)
    db_session.flush()


def test_tables_present_after_persist(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    request = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="test",
        promotion_reason="table presence check",
    )
    persist_promotion_result(
        db_session,
        legal_object_promotion_request_id=request.id,
        promotion_status="pending",
    )
    assert db_session.execute(select(LegalObjectPromotionRequest)).scalar_one_or_none() is not None
    assert db_session.execute(select(LegalObjectPromotionResult)).scalar_one_or_none() is not None


def test_no_citation_or_answer_tables_created(db_session, engine):
    from sqlalchemy import inspect

    parsed, extracted = _seed_parsed_structure(db_session)
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="test",
        promotion_reason="boundary check",
    )
    tables = set(inspect(engine).get_table_names())
    citation_tables = {name for name in tables if "citation" in name}
    assert citation_tables <= {
        "citation_assembly_governance_requests",
        "citation_assembly_governance_results",
        "citations",
    }
    from app.models.citation import Citation

    assert db_session.query(Citation).count() == 0
    assert not any("answer" in name for name in tables)
